#!/usr/bin/env python3
"""Insert downloaded images into report markdown.

After fetch_all_images.py downloads images to 05-images/,
this script inserts ![alt](05-images/filename.ext) after each #### heading.

Usage:
  insert_images.py --report 05-report.md --images-dir 05-images
"""

import argparse
import os
import re
import sys


def main():
    parser = argparse.ArgumentParser(description="Insert images into report")
    parser.add_argument("--report", required=True, help="Path to 05-report.md")
    parser.add_argument("--images-dir", required=True, help="Path to 05-images/ directory")

    args = parser.parse_args()

    if not os.path.exists(args.report):
        print(f"ERROR: Report not found: {args.report}")
        sys.exit(1)

    if not os.path.exists(args.images_dir):
        print(f"ERROR: Images dir not found: {args.images_dir}")
        sys.exit(1)

    # Read report
    with open(args.report, encoding="utf-8") as f:
        content = f.read()

    # Get sorted list of images (exclude cover.png)
    images = sorted([
        f for f in os.listdir(args.images_dir)
        if f != "cover.png" and not f.startswith("temp_")
        and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
    ])

    if not images:
        print("No entry images found (only cover). Nothing to insert.")
        return

    print(f"Found {len(images)} entry images to insert")

    # Find all #### headings that don't have an image
    lines = content.split('\n')
    new_lines = []
    img_idx = 0

    for i, line in enumerate(lines):
        new_lines.append(line)

        # After a #### heading, check if next non-empty line is already an image
        if line.strip().startswith('#### '):
            # Look ahead for existing image
            has_image = False
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].strip().startswith('!['):
                    has_image = True
                    break
                if lines[j].strip().startswith('> ') or lines[j].strip().startswith('**'):
                    break

            if not has_image and img_idx < len(images):
                img_file = images[img_idx]
                new_lines.append(f'![{img_file}](05-images/{img_file})')
                new_lines.append('')
                img_idx += 1

    # Write updated report
    with open(args.report, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"Inserted {img_idx} images into report")


if __name__ == "__main__":
    main()
