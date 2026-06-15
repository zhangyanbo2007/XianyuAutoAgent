#!/usr/bin/env node

// ============================================================================
// Follow Builders — WeChat Official Account Delivery Script
// ============================================================================
// Publishes a digest as a WeChat Official Account draft article.
//
// Steps:
//   1. Get access_token from WeChat API
//   2. Download YouTube thumbnails via proxy (if any videoIds in HTML)
//   3. Upload thumbnails as inline images via uploadimg API
//   4. Upload cover image via add_material API
//   5. Replace thumbnail URLs in HTML with WeChat media URLs
//   6. Create draft article via draft/add API
//   7. Optionally publish via freepublish/submit API
//
// Usage:
//   node deliver-wechat.js --file /path/to/digest.html
//   node deliver-wechat.js --file /path/to/digest.html --publish
//
// Config: ~/.follow-builders/config.json (delivery.wechat section)
// Env:    ~/.wechat/.env (WECHAT_APPID, WECHAT_APPSECRET)
// ============================================================================

import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { execSync } from 'child_process';

// -- Constants ---------------------------------------------------------------

const USER_DIR = join(homedir(), '.follow-builders');
const WECHAT_DIR = join(homedir(), '.wechat');
const CONFIG_PATH = join(USER_DIR, 'config.json');
const WECHAT_ENV_PATH = join(WECHAT_DIR, '.env');
const THUMB_DIR = '/tmp/wechat-thumbnails';
const URL_MAP_PATH = '/tmp/wechat-urls/thumbnail-map.json';
const PROXY = process.env.WECHAT_PROXY || 'http://192.168.28.92:7897';

// -- Helpers -----------------------------------------------------------------

async function getConfig() {
  if (!existsSync(CONFIG_PATH)) throw new Error('config.json not found');
  return JSON.parse(await readFile(CONFIG_PATH, 'utf-8'));
}

async function getWechatEnv() {
  if (!existsSync(WECHAT_ENV_PATH)) throw new Error('~/.wechat/.env not found');
  const content = await readFile(WECHAT_ENV_PATH, 'utf-8');
  const lines = content.split('\n');
  const env = {};
  for (const line of lines) {
    const match = line.match(/^(\w+)=(.*)$/);
    if (match) env[match[1]] = match[2].trim();
  }
  return env;
}

async function getAccessToken(appid, appsecret) {
  const url = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${appid}&secret=${appsecret}`;
  const res = await fetch(url);
  const data = await res.json();
  if (data.errcode) throw new Error(`WeChat token error ${data.errcode}: ${data.errmsg}`);
  return data.access_token;
}

async function uploadInlineImage(token, filePath) {
  const formData = new FormData();
  const buffer = await readFile(filePath);
  formData.append('media', new Blob([buffer]), 'thumbnail.jpg');
  const res = await fetch(
    `https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=${token}`,
    { method: 'POST', body: formData }
  );
  const data = await res.json();
  if (data.errcode) throw new Error(`uploadimg error ${data.errcode}: ${data.errmsg}`);
  return data.url;
}

async function uploadCoverImage(token, filePath) {
  const formData = new FormData();
  const buffer = await readFile(filePath);
  formData.append('media', new Blob([buffer]), 'cover.jpg');
  const res = await fetch(
    `https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${token}&type=image`,
    { method: 'POST', body: formData }
  );
  const data = await res.json();
  if (data.errcode) throw new Error(`add_material error ${data.errcode}: ${data.errmsg}`);
  return data.media_id;
}

function extractVideoIds(html) {
  const regex = /https:\/\/img\.youtube\.com\/vi\/([\w-]+)\/hqdefault\.jpg/g;
  const ids = [];
  let match;
  while ((match = regex.exec(html)) !== null) {
    ids.push(match[1]);
  }
  return ids;
}

async function downloadThumbnail(videoId) {
  const filePath = join(THUMB_DIR, `${videoId}.jpg`);
  if (existsSync(filePath)) return filePath;
  const url = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
  try {
    execSync(
      `curl -s -o "${filePath}" "${url}"`,
      { env: { ...process.env, http_proxy: PROXY, https_proxy: PROXY }, timeout: 15000 }
    );
    if (!existsSync(filePath)) throw new Error('Download failed');
    return filePath;
  } catch (e) {
    console.error(`Failed to download thumbnail for ${videoId}: ${e.message}`);
    return null;
  }
}

async function createDraft(token, title, content, thumbMediaId, sourceUrl) {
  const article = {
    title: title,
    author: 'Follow Builders',
    content: content,
    thumb_media_id: thumbMediaId,
    show_cover_pic: 0,
    content_source_url: sourceUrl || ''
  };
  const body = { articles: [article] };
  // Must send with non-escaped Chinese chars (\uXXXX inflates payload ~2x,
  // causing error 45004 "description size out of limit")
  const payload = new TextEncoder().encode(JSON.stringify(body));
  const res = await fetch(
    `https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${token}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: payload
    }
  );
  const data = await res.json();
  if (data.errcode) throw new Error(`draft/add error ${data.errcode}: ${data.errmsg}`);
  return data.media_id;
}

async function publishDraft(token, mediaId) {
  const payload = new TextEncoder().encode(JSON.stringify({ media_id: mediaId }));
  const res = await fetch(
    `https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token=${token}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: payload
    }
  );
  const data = await res.json();
  if (data.errcode) throw new Error(`freepublish/submit error ${data.errcode}: ${data.errmsg}`);
  return data.publish_id;
}

// -- Main --------------------------------------------------------------------

async function main() {
  const args = process.argv.slice(2);
  const shouldPublish = args.includes('--publish');

  const fileIdx = args.indexOf('--file');
  if (fileIdx === -1 || !args[fileIdx + 1]) {
    console.error('Usage: node deliver-wechat.js --file <path> [--source-url <url>] [--publish]');
    process.exit(1);
  }
  const filePath = args[fileIdx + 1];

  const sourceUrlIdx = args.indexOf('--source-url');
  const sourceUrl = sourceUrlIdx !== -1 ? args[sourceUrlIdx + 1] : '';

  // Load config and env
  const config = await getConfig();
  const wechatEnv = await getWechatEnv();
  const appid = config.delivery?.wechat?.appid || wechatEnv.WECHAT_APPID;
  const appsecret = config.delivery?.wechat?.appsecret || wechatEnv.WECHAT_APPSECRET;
  if (!appid || !appsecret) throw new Error('WeChat AppID/AppSecret not configured');

  // Get today's date
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const title = `AI Builders 每日摘要 ${new Date().toISOString().slice(0, 10)}`;

  // Read HTML content
  const html = await readFile(filePath, 'utf-8');

  // Get access token
  console.log('Getting WeChat access token...');
  const token = await getAccessToken(appid, appsecret);

  // Handle YouTube thumbnails
  const videoIds = extractVideoIds(html);
  console.log(`Found ${videoIds.length} YouTube thumbnails to process`);

  let thumbnailMap = {};
  if (existsSync(URL_MAP_PATH)) {
    thumbnailMap = JSON.parse(await readFile(URL_MAP_PATH, 'utf-8'));
  }

  await mkdir(THUMB_DIR, { recursive: true });
  await mkdir('/tmp/wechat-urls', { recursive: true });

  let updatedHtml = html;
  for (const videoId of videoIds) {
    if (thumbnailMap[videoId]) {
      console.log(`Using cached URL for ${videoId}`);
    } else {
      console.log(`Downloading thumbnail for ${videoId}...`);
      const localPath = await downloadThumbnail(videoId);
      if (!localPath) continue;
      console.log(`Uploading ${videoId} to WeChat...`);
      const wechatUrl = await uploadInlineImage(token, localPath);
      thumbnailMap[videoId] = wechatUrl;
    }
    // Replace YouTube URL with WeChat URL in HTML
    updatedHtml = updatedHtml.replace(
      `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
      thumbnailMap[videoId]
    );
  }

  // Save thumbnail map for reuse
  await writeFile(URL_MAP_PATH, JSON.stringify(thumbnailMap, null, 2));

  // Upload cover image (use first available thumbnail or a default)
  const coverVideoId = videoIds[0] || '57lDpTwiW6g';
  const coverPath = join(THUMB_DIR, `${coverVideoId}.jpg`);
  if (!existsSync(coverPath)) await downloadThumbnail(coverVideoId);

  let thumbMediaId;
  if (existsSync('/tmp/wechat-cover-thumb-id.txt')) {
    thumbMediaId = (await readFile('/tmp/wechat-cover-thumb-id.txt', 'utf-8')).trim();
  } else if (existsSync(coverPath)) {
    console.log('Uploading cover image...');
    thumbMediaId = await uploadCoverImage(token, coverPath);
    await writeFile('/tmp/wechat-cover-thumb-id.txt', thumbMediaId);
  } else {
    throw new Error('No cover image available');
  }

  // Save final HTML
  const outPath = `/tmp/wechat-digest-${today}.html`;
  await writeFile(outPath, updatedHtml);

  // Create draft
  console.log('Creating WeChat draft article...');
  const mediaId = await createDraft(token, title, updatedHtml, thumbMediaId, sourceUrl);
  console.log(`Draft created! media_id: ${mediaId}`);

  // Optionally publish
  if (shouldPublish) {
    console.log('Publishing draft...');
    const publishId = await publishDraft(token, mediaId);
    console.log(`Published! publish_id: ${publishId}`);
  }

  console.log(JSON.stringify({
    status: 'ok',
    method: 'wechat',
    media_id: mediaId,
    published: shouldPublish,
    html_path: outPath
  }));
}

main().catch(err => {
  console.error(`Error: ${err.message}`);
  console.log(JSON.stringify({ status: 'error', method: 'wechat', message: err.message }));
  process.exit(1);
});