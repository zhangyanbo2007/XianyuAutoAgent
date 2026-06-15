#!/usr/bin/env python3
"""清理飞书文档中替换操作遗留的旧 block"""
import os, sys, json, requests

APP_ID = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]
DOC_TOKEN = "X4eLdNWNPoK4QGxni1jccufUnHY"

def get_token():
    r = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                      json={"app_id": APP_ID, "app_secret": APP_SECRET})
    return r.json()["tenant_access_token"]

def get_doc_blocks(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks",
                     headers=headers, params={"page_size": 500})
    data = r.json().get("data", {})
    return data.get("items", [])

def delete_block(token, block_id):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks/{block_id}"
    r = requests.delete(url, headers=headers)
    status = "OK" if r.status_code == 200 else f"FAIL({r.status_code})"
    print(f"  Delete {block_id}: {status}")
    return r.status_code == 200

def delete_blocks(token, block_ids):
    ok = 0
    for bid in block_ids:
        if delete_block(token, bid):
            ok += 1
    print(f"  Deleted {ok}/{len(block_ids)} blocks")
    return ok

def main():
    token = get_token()
    blocks = get_doc_blocks(token)

    # Build a map of block_id -> block
    block_map = {b["block_id"]: b for b in blocks}

    # Find orphaned old blocks in Section 4 area
    # Old Section 4 blocks (between heading4 4.1 and divider before section 5)
    old_section4_ids = [
        "doxcn7WQMr3zhTcib34xOLCcuge",  # heading4: 4.1 使用内容
        "doxcndvk0HcVZDk67WxfYXdgybh",  # bullet: GEPA
        "doxcnsiehrYsZmabIg5tYdpU5Uc",  # bullet: Prompt优化
        "doxcnLGLM8oSGHUahtey2W4oeQh",  # bullet: badcase
        "doxcnHGnGyz3xVPN0n4jeJx6Onf",  # heading4: 4.2 预期迭代节奏
        "doxcnV4DIHtwIhh7Byw571eN1ed",  # bullet: 单次COT
        "doxcnTS279jbqaOZKyWuEZ6XeCM",  # bullet: Claude code 1.2
        "doxcniVLWNIjmvH4F6e0kOMvz1f",  # bullet: 每日优化
        "doxcnJxVQlPOsSinHjQDGmma93c",  # bullet: 上班
        "doxcnB539h7P0zn74Uuy3UXX7Se",  # bullet: 下班
        "doxcnzOeDvbnZDEKFfcaUcE9UQf",  # empty bullet
    ]

    # Old Section 5 blocks
    old_section5_ids = [
        "doxcnyT5C31alzQq51XZyawjOoc",  # bullet: Claude code pro max 20
        "doxcnmFe4eMSAd8CERZn0XvnZSf",  # bullet: Codex pro x5
    ]

    # Old Section 6 blocks
    old_section6_ids = [
        "doxcna9AP3Zoc8sk5lmDeniu1Mb",  # heading3: 6 申请金额 (first one)
    ]

    # Old empty text blocks
    old_empty_ids = [
        "doxcnEM7eQy6pJo3MT7iLYEolSg",  # empty text (was after section 4)
        "doxcndE3vcSQnuUtsI2PlbL6V0e",  # empty text (was after section 5)
        "doxcnWmtynSMBI0qlx3aHQKJGZd",  # empty text (was before section 6)
        "doxcnENrFSf8m3o4JtoRPokRZ7X",  # empty text (was before section 6)
    ]

    # Collect all IDs to delete, only those that still exist
    all_ids = old_section4_ids + old_section5_ids + old_section6_ids + old_empty_ids
    to_delete = [bid for bid in all_ids if bid in block_map]

    print(f"Found {len(to_delete)} blocks to delete out of {len(all_ids)} candidates")

    if to_delete:
        # Delete in batches of 50
        for i in range(0, len(to_delete), 50):
            batch = to_delete[i:i+50]
            result = delete_blocks(token, batch)
            print(f"Batch {i//50 + 1}: {result}")

    # Also need to delete the old table in Section 6
    # Table block: doxcn6v0SFsF0wYgRD1CXXmRqwf
    # And its children (table cells)
    table_id = "doxcn6v0SFsF0wYgRD1CXXmRqwf"
    if table_id in block_map:
        # First delete all cell blocks, then the table
        cell_ids = [bid for bid, b in block_map.items()
                    if b.get("parent") == table_id]
        if cell_ids:
            print(f"Deleting {len(cell_ids)} table cells...")
            for i in range(0, len(cell_ids), 50):
                batch = cell_ids[i:i+50]
                result = delete_blocks(token, batch)
                print(f"Cell batch: {result}")
        # Now delete the table itself
        result = delete_blocks(token, [table_id])
        print(f"Table delete: {result}")

    # Also delete old Section 5 image/file blocks that are children of the section
    # doxcnOTJXmOmQkUWycAAGWGq0nb (file block with images)
    # doxcnkVcTCo91gIJngW8XBmTaKc (image block)
    file_block_id = "doxcnOTJXmOmQkUWycAAGWGq0nb"
    image_block_id = "doxcnkVcTCo91gIJngW8XBmTaKc"

    for bid in [file_block_id, image_block_id]:
        if bid in block_map:
            # Delete children first
            children = [b["block_id"] for b in blocks if b.get("parent") == bid]
            if children:
                delete_blocks(token, children)
            result = delete_blocks(token, [bid])
            print(f"Delete {bid}: {result}")

    print("Done!")

if __name__ == "__main__":
    main()
