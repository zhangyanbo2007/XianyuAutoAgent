#!/usr/bin/env python3
"""清理飞书文档中旧的 block（使用 urllib，与 edit_doc.py 一致）"""
import os, json, urllib.request, urllib.error

APP_ID = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]
DOC_TOKEN = "X4eLdNWNPoK4QGxni1jccufUnHY"

def api_call(method, url, token, body=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Authorization": f"Bearer {token}"}
    if data:
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        resp = urllib.request.urlopen(req).read()
        return json.loads(resp)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(error_body)
        except:
            return {"code": -1, "msg": f"HTTP {e.code}: {error_body[:200]}"}

def get_token():
    r = api_call("POST", "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", "",
                 {"app_id": APP_ID, "app_secret": APP_SECRET})
    return r["tenant_access_token"]

def get_blocks(token):
    blocks = []
    page_token = None
    while True:
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks?page_size=500"
        if page_token:
            url += f"&page_token={page_token}"
        r = api_call("GET", url, token)
        items = r.get("data", {}).get("items", [])
        blocks.extend(items)
        if not r.get("data", {}).get("has_more"):
            break
        page_token = r["data"].get("page_token")
    return blocks

def delete_block(token, block_id):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks/{block_id}?document_revision_id=-1"
    r = api_call("DELETE", url, token)
    code = r.get("code", -1)
    if code == 0:
        print(f"  ✓ {block_id}")
        return True
    else:
        print(f"  ✗ {block_id}: {r.get('msg', 'unknown')}")
        return False

def main():
    token = get_token()
    blocks = get_blocks(token)
    print(f"Total blocks: {len(blocks)}")

    block_map = {b["block_id"]: b for b in blocks}

    # Find the old content blocks (before the new content)
    # Old Section 4 heading + content blocks
    old_section4 = [
        "doxcn7WQMr3zhTcib34xOLCcuge",  # heading4: 4.1 使用内容
        "doxcndvk0HcVZDk67WxfYXdgybh",  # bullet: GEPA
        "doxcnsiehrYsZmabIg5tYdpU5Uc",  # bullet: Prompt优化
        "doxcnLGLM8oSGHUahtey2W4oeQh",  # bullet: badcase
        "doxcnHGnGyz3xVPN0n4jeJx6Onf",  # heading4: 4.2 预期迭代节奏
        "doxcnV4DIHtwIhh7Byw571eN1ed",  # bullet parent
        "doxcnTS279jbqaOZKyWuEZ6XeCM",  # bullet child
        "doxcniVLWNIjmvH4F6e0kOMvz1f",  # bullet parent
        "doxcnJxVQlPOsSinHjQDGmma93c",  # bullet child
        "doxcnB539h7P0zn74Uuy3UXX7Se",  # bullet child
        "doxcnzOeDvbnZDEKFfcaUcE9UQf",  # empty bullet
    ]

    # Old Section 5 blocks
    old_section5 = [
        "doxcnyT5C31alzQq51XZyawjOoc",  # bullet: Claude code pro max 20
        "doxcnOTJXmOmQkUWycAAGWGq0nb",  # file block (images)
        "doxcnwyc4U1C5QehD0y4Fmwqqcu",  # sub block
        "doxcnFscgz6giILJ5gE8UnVdBmc",  # image
        "doxcnV6ag3ZxgCAWc3HcuQApS3e",  # sub block
        "doxcnfU9k2jLfslM2yfcd2rleod",  # image
        "doxcnmFe4eMSAd8CERZn0XvnZSf",  # bullet: Codex pro x5
        "doxcnkVcTCo91gIJngW8XBmTaKc",  # image
    ]

    # Old Section 6 blocks
    old_section6 = [
        "doxcn6v0SFsF0wYgRD1CXXmRqwf",  # old table
        "doxcn2l3YF1pXzhB4pTDv2KU7Zb", "doxcnPnX1KyrrrCMte4z6oA6SOd",
        "doxcnc3ZfRHwfLLgsARFs96Fbdb", "doxcnhtckEDjg2uh6Cj6Wumzlwd",
        "doxcnmeZ4qk7jkj5jkoIMZlTytd", "doxcnfZ9uxocAEsUCzydKtCbNGg",
        "doxcnm2XidepBpviTBpV427Roye", "doxcnllfkPjbe2O0WUXgKBmsOmd",
        "doxcnF92YebxJDMlCmAuIaOeB8d", "doxcnKXD39ISdJVo4YsJ235H90c",
        "doxcnD6v5QadIPzTKFw84juFaZg", "doxcn6l4u4osiXoYDImCjRJHHxg",
        "doxcnp0n1wWozkteyE7qYiLV9Kg", "doxcnvHXVk20dga4WzUcEUEqoab",
        "doxcnShZj5Q1b55XySDdUzgyzwg", "doxcnHxpPznFlwlh2hittHkRSjc",
        "doxcn6PMNAZm7uhRKMxlApRtuHb", "doxcnLcMGTLolSbCW4wrMJW7Rjh",
        "doxcn8sLT1qgRPOlRcHbJVrAU7b", "doxcnJ9AJkI73nS8qyJSVGuRBSh",
        "doxcntyYfX7yIG84zlQJqdluHah", "doxcnWFu2tuIutKH2wRbJivpdgg",
        "doxcnaBrwWZa8LXCpCOA1D7izfe", "doxcnqhtK81hjAQZM2ZcCWHnu0g",
        "doxcn8e7wBt54rSVL0mm0F57Rwg", "doxcnHUj3OdhknYLVxWIkAvVjnf",
        "doxcn63NNd2AQNp34fZMCtfJYrc", "doxcnZ51B1JwA2zEbnszizgJOlh",
        "doxcntCzoho8IoimsweTTe5yYKg", "doxcnT3JInN4y3sVCRgk9XHk7qd",
        "doxcnFS8YXPxEqAwDJiL1EFCaAu", "doxcn2kYwM0gM6ECMJ5xonYP0pe",
        "doxcnJO5dkSvMQ5jyDEPyTg5grd", "doxcnn7K5IISDNpPCQ3cAEgJOvm",
    ]

    # Old empty/divider blocks
    old_misc = [
        "doxcnWmtynSMBI0qlx3aHQKJGZd",  # empty text
        "doxcnENrFSf8m3o4JtoRPokRZ7X",  # empty text
        "doxcnylvoiIMtsDIOjlgSQB7zNe",  # text "### 6 申请金额" (duplicate)
    ]

    all_ids = old_section4 + old_section5 + old_section6 + old_misc
    to_delete = [bid for bid in all_ids if bid in block_map]

    print(f"Blocks to delete: {len(to_delete)}/{len(all_ids)}")

    ok = 0
    for bid in to_delete:
        if delete_block(token, bid):
            ok += 1

    print(f"\nDone: {ok}/{len(to_delete)} deleted")

if __name__ == "__main__":
    main()
