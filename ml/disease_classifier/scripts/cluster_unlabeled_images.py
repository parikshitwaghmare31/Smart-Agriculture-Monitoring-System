"""
cluster_unlabeled_images.py
-----------------------------
OFFLINE, UNSUPERVISED helper script — run this on your own machine.

If you have a folder of raw, unlabeled plant photos (e.g. straight off a
phone, not yet sorted by disease), this script groups visually similar
images together automatically using a pretrained CNN as a feature extractor
plus K-Means clustering. It does NOT know what any cluster actually *is*
(that requires a human to look and label it) — it just groups similar-
looking images so you can label a whole cluster at once instead of every
photo individually. This is a big time-saver when bootstrapping a labeled
dataset for train_classifier.py from scratch.

Workflow:
  1. Point this script at a folder of raw unlabeled images
  2. It creates cluster_00/, cluster_01/, ... folders with the images sorted
     into groups
  3. You open each cluster folder, quickly confirm what disease/condition
     it represents, and rename the folder accordingly (e.g. cluster_00 ->
     tomato_early_blight)
  4. Merge any folders that turned out to represent the same class
  5. Feed the resulting folder structure into train_classifier.py

Usage:
    pip install -r requirements-training.txt
    python cluster_unlabeled_images.py --input-dir /path/to/raw_photos --k 8
"""

import os
import shutil
import argparse

import numpy as np
from sklearn.cluster import KMeans
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array

IMG_SIZE = (224, 224)
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def extract_features(image_paths, model):
    features = []
    valid_paths = []
    for path in image_paths:
        try:
            img = load_img(path, target_size=IMG_SIZE)
            arr = img_to_array(img)
            arr = preprocess_input(arr)
            features.append(arr)
            valid_paths.append(path)
        except Exception as e:
            print(f"Skipping unreadable image {path}: {e}")

    if not features:
        return np.array([]), []

    batch = np.stack(features)
    embeddings = model.predict(batch, verbose=0)
    return embeddings, valid_paths


def main():
    parser = argparse.ArgumentParser(description="Cluster unlabeled plant photos by visual similarity")
    parser.add_argument("--input-dir", required=True, help="Folder of raw, unlabeled images")
    parser.add_argument("--output-dir", default=None,
                         help="Where to write clustered folders (default: <input-dir>_clustered)")
    parser.add_argument("--k", type=int, default=8, help="Number of clusters to create")
    args = parser.parse_args()

    output_dir = args.output_dir or f"{args.input_dir.rstrip('/')}_clustered"

    image_paths = [
        os.path.join(args.input_dir, f)
        for f in os.listdir(args.input_dir)
        if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS
    ]
    print(f"Found {len(image_paths)} images in {args.input_dir}")

    if len(image_paths) < args.k:
        raise ValueError(
            f"Found only {len(image_paths)} images but requested {args.k} clusters. "
            "Use fewer clusters or add more images."
        )

    print("Loading MobileNetV2 as a feature extractor (pretrained on ImageNet, no fine-tuning needed)...")
    feature_extractor = MobileNetV2(
        input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet", pooling="avg"
    )

    print("Extracting features from all images (this is the slow part, be patient)...")
    embeddings, valid_paths = extract_features(image_paths, feature_extractor)

    print(f"Clustering {len(valid_paths)} images into {args.k} groups...")
    kmeans = KMeans(n_clusters=args.k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    os.makedirs(output_dir, exist_ok=True)
    for cluster_id in range(args.k):
        os.makedirs(os.path.join(output_dir, f"cluster_{cluster_id:02d}"), exist_ok=True)

    for path, label in zip(valid_paths, labels):
        dest = os.path.join(output_dir, f"cluster_{label:02d}", os.path.basename(path))
        shutil.copy2(path, dest)

    print(f"\nDone. Clustered images written to: {output_dir}")
    print("Next steps:")
    print("  1. Open each cluster_XX folder and check what disease/condition it represents")
    print("  2. Rename each folder to a clear label, e.g. cluster_00 -> tomato_early_blight")
    print("  3. Merge folders that represent the same class")
    print("  4. Delete/relabel any cluster that mixes multiple classes together (K-Means")
    print("     isn't perfect — some manual cleanup is expected)")
    print("  5. Once folders are cleanly labeled, run train_classifier.py on this directory")


if __name__ == "__main__":
    main()
