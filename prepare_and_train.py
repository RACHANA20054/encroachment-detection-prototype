from pathlib import Path
import cv2
import random
import shutil
from ultralytics import YOLO

# ============================================================
# CUSTOM ENCROACHMENT DATASET
# 0 = cement_bag
# 1 = brick
# 2 = cement_block
# ============================================================

PROJECT = Path(__file__).resolve().parent
RAW = PROJECT / "dataset" / "raw" / "images"
OUT = PROJECT / "dataset" / "yolo_dataset"

CLASSES = ["cement_bag", "brick", "cement_block"]
PROMPTS = ["cement bag", "brick", "cement block"]

# Your DroidCam image area
CROP_W = 427
CROP_H = 320


def crop_camera_area(img):
    h, w = img.shape[:2]
    return img[:min(CROP_H, h), :min(CROP_W, w)]


def convert_box(box, width, height):
    x1, y1, x2, y2 = map(float, box)

    x1 = max(0, min(x1, width))
    x2 = max(0, min(x2, width))
    y1 = max(0, min(y1, height))
    y2 = max(0, min(y2, height))

    bw = x2 - x1
    bh = y2 - y1

    if bw <= 1 or bh <= 1:
        return None

    xc = (x1 + x2) / 2 / width
    yc = (y1 + y2) / 2 / height

    return xc, yc, bw / width, bh / height


def main():

    images = sorted([
        p for p in RAW.iterdir()
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ])

    print(f"\nFound {len(images)} images.")

    if not images:
        print("ERROR: No images found.")
        return

    # --------------------------------------------------------
    # Load YOLO-World for automatic initial annotations
    # --------------------------------------------------------

    print("\nLoading YOLO-World...")
    world = YOLO("yolov8s-world.pt")

    world.set_classes(PROMPTS)

    # --------------------------------------------------------
    # Create dataset folders
    # --------------------------------------------------------

    if OUT.exists():
        shutil.rmtree(OUT)

    for split in ["train", "val", "test"]:
        (OUT / "images" / split).mkdir(parents=True)
        (OUT / "labels" / split).mkdir(parents=True)

    # --------------------------------------------------------
    # Shuffle and split
    # --------------------------------------------------------

    random.seed(42)
    random.shuffle(images)

    total = len(images)

    train_end = int(total * 0.70)
    val_end = int(total * 0.90)

    train_images = images[:train_end]
    val_images = images[train_end:val_end]
    test_images = images[val_end:]

    splits = {
        "train": train_images,
        "val": val_images,
        "test": test_images
    }

    total_boxes = 0

    # --------------------------------------------------------
    # Generate automatic YOLO annotations
    # --------------------------------------------------------

    for split, split_images in splits.items():

        print(f"\nPreparing {split}: {len(split_images)} images")

        for index, image_path in enumerate(split_images, 1):

            img = cv2.imread(str(image_path))

            if img is None:
                print(f"\nSkipping: {image_path.name}")
                continue

            # Remove black DroidCam area
            img = crop_camera_area(img)

            height, width = img.shape[:2]

            output_image = OUT / "images" / split / image_path.name

            cv2.imwrite(str(output_image), img)

            # Detect objects
            results = world.predict(
                img,
                conf=0.10,
                iou=0.50,
                verbose=False
            )

            labels = []

            for result in results:

                if result.boxes is None:
                    continue

                for box, cls, conf in zip(
                    result.boxes.xyxy.cpu().numpy(),
                    result.boxes.cls.cpu().numpy(),
                    result.boxes.conf.cpu().numpy()
                ):

                    class_id = int(cls)

                    if class_id < 0 or class_id >= 3:
                        continue

                    converted = convert_box(
                        box,
                        width,
                        height
                    )

                    if converted is None:
                        continue

                    xc, yc, bw, bh = converted

                    # Ignore extremely tiny detections
                    if bw * bh < 0.001:
                        continue

                    labels.append(
                        f"{class_id} "
                        f"{xc:.6f} "
                        f"{yc:.6f} "
                        f"{bw:.6f} "
                        f"{bh:.6f}"
                    )

            label_path = (
                OUT
                / "labels"
                / split
                / f"{image_path.stem}.txt"
            )

            label_path.write_text(
                "\n".join(labels)
            )

            total_boxes += len(labels)

            print(
                f"\r{split}: {index}/{len(split_images)}",
                end=""
            )

    # --------------------------------------------------------
    # data.yaml
    # --------------------------------------------------------

    yaml = f"""path: {OUT}

train: images/train
val: images/val
test: images/test

names:
  0: cement_bag
  1: brick
  2: cement_block
"""

    (OUT / "data.yaml").write_text(yaml)

    print("\n\n================================")
    print("DATASET PREPARATION COMPLETE")
    print("================================")

    print(f"Images: {total}")
    print(f"Generated boxes: {total_boxes}")
    print(f"Dataset: {OUT}")

    # --------------------------------------------------------
    # Train YOLOv8
    # --------------------------------------------------------

    print("\nStarting YOLOv8 training...")
    print("Do NOT close this terminal.\n")

    model = YOLO("yolov8n.pt")

    model.train(
        data=str(OUT / "data.yaml"),
        epochs=50,
        imgsz=640,
        batch=4,
        workers=2,
        device="mps",
        project=str(PROJECT / "runs"),
        name="encroachment_v1",
        pretrained=True,
        patience=10,
        exist_ok=True
    )

    print("\n================================")
    print("TRAINING COMPLETE")
    print("================================")

    print(
        "\nYour trained model should be here:"
    )

    print(
        PROJECT
        / "runs"
        / "encroachment_v1"
        / "weights"
        / "best.pt"
    )


if __name__ == "__main__":
    main()