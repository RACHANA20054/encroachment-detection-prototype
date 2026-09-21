import os
from pathlib import Path

BASE = Path("dataset_clean/yolo")
SPLITS = ["train", "val"]
NUM_CLASSES = 6
CLASS_NAMES = ["cement_bag", "brick", "cement_block", "foundation_block", "owner", "encroacher"]

known_negatives = set()

issues = []
class_counts = {i: 0 for i in range(NUM_CLASSES)}
total_images = 0
total_labeled = 0
total_negative = 0

for split in SPLITS:
    img_dir = BASE / "images" / split
    lbl_dir = BASE / "labels" / split

    images = sorted([f for f in os.listdir(img_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    total_images += len(images)

    for img_name in images:
        stem = Path(img_name).stem
        lbl_path = lbl_dir / f"{stem}.txt"

        if not lbl_path.exists():
            total_negative += 1
            known_negatives.add(stem)
            continue

        total_labeled += 1
        with open(lbl_path, "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        if len(lines) == 0:
            issues.append(f"{split}/{stem}.txt exists but is EMPTY (should have no file if negative)")
            continue

        for line_num, line in enumerate(lines, 1):
            parts = line.split()
            if len(parts) != 5:
                issues.append(f"{split}/{stem}.txt line {line_num}: wrong number of fields ({len(parts)})")
                continue

            cls, x, y, w, h = parts
            try:
                cls = int(cls)
                x, y, w, h = float(x), float(y), float(w), float(h)
            except ValueError:
                issues.append(f"{split}/{stem}.txt line {line_num}: non-numeric value")
                continue

            if cls < 0 or cls >= NUM_CLASSES:
                issues.append(f"{split}/{stem}.txt line {line_num}: invalid class id {cls}")
                continue

            if w <= 0 or h <= 0:
                issues.append(f"{split}/{stem}.txt line {line_num}: zero/negative width or height (w={w}, h={h})")

            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                issues.append(f"{split}/{stem}.txt line {line_num}: coordinate out of [0,1] range")

            x1, x2 = x - w/2, x + w/2
            y1, y2 = y - h/2, y + h/2
            if x1 < -0.01 or x2 > 1.01 or y1 < -0.01 or y2 > 1.01:
                issues.append(f"{split}/{stem}.txt line {line_num}: box extends outside image bounds")

            class_counts[cls] += 1

print("=" * 50)
print("DATASET VALIDATION REPORT")
print("=" * 50)
print(f"Total images found: {total_images}")
print(f"Labeled images: {total_labeled}")
print(f"Negative (no label) images: {total_negative}")
print()
print("Class instance counts:")
for i in range(NUM_CLASSES):
    print(f"  {i} {CLASS_NAMES[i]}: {class_counts[i]}")
print()

if issues:
    print(f"⚠️  {len(issues)} ISSUE(S) FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ No issues found. Dataset looks clean.")

print()
print("Negative images detected (no label file):")
for name in sorted(known_negatives):
    print(f"  - {name}")
