#!/usr/bin/env python3
"""调试飞书 block 删除 API"""
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
        print(f"  HTTP {e.code}: {error_body[:300]}")
        try:
            return json.loads(error_body)
        except:
            return {"code": -1, "msg": f"HTTP {e.code}"}

def get_token():
    r = api_call("POST", "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", "",
                 {"app_id": APP_ID, "app_secret": APP_SECRET})
    return r["tenant_access_token"]

def main():
    token = get_token()
    print(f"Token: {token[:20]}...")

    # Test 1: Try batch_delete endpoint
    test_block_id = "doxcn7WQMr3zhTcib34xOLCcuge"
    print(f"\nTest 1: batch_delete with {test_block_id}")
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks/batch_delete"
    r = api_call("DELETE", url, token, {"block_ids": [test_block_id]})
    print(f"  Result: {r}")

    # Test 2: Try single delete with document_revision_id
    print(f"\nTest 2: single delete {test_block_id}")
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks/{test_block_id}"
    r = api_call("DELETE", url, token)
    print(f"  Result: {r}")

    # Test 3: Try without revision
    print(f"\nTest 3: single delete with revision -1")
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks/{test_block_id}?document_revision_id=-1"
    r = api_call("DELETE", url, token)
    print(f"  Result: {r}")

    # Test 4: Check what the wiki resolution gives us
    print(f"\nTest 4: Wiki resolution")
    url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token=FNzcwVrv7iAjeKk2SPBcOfP7nUt"
    r = api_call("GET", url, token)
    print(f"  Result: {json.dumps(r, indent=2, ensure_ascii=False)[:500]}")

    # Test 5: Check the actual blocks API
    print(f"\nTest 5: Get first few blocks")
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks?page_size=5"
    r = api_call("GET", url, token)
    items = r.get("data", {}).get("items", [])
    for item in items[:3]:
        print(f"  Block: {item['block_id']} type={item.get('block_type')} parent={item.get('parent')}")

if __name__ == "__main__":
    main()
