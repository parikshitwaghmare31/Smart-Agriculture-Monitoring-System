"""
train_classifier.py
--------------------
OFFLINE training script — run this on your own machine (ideally with a GPU,
but a modern CPU works fine for small-to-medium datasets), NOT on Render.

Trains an image classifier via transfer learning on MobileNetV2 (pretrained
on ImageNet), then exports the result to ONNX format for lightweight
serving in production (see app/services/disease_service.py).

Expected dataset layout — one folder per class, named "<Crop>__<DiseaseLabel>"
(double underscore separates the two parts; use single underscores or
spaces within each part). Images go inside each folder:

    dataset/
      Tomato__Early_Blight/
        img001.jpg
        img002.jpg
        ...
      Tomato__Late_Blight/
        ...
      Tomato__Healthy/
        ...
      Potato__Healthy/
        ...
      Potato__Late_Blight/
        ...

This naming convention lets the dashboard show a "Crop" dropdown (Tomato,
Potato, ...) and look up the matching recommendation entry by
(crop, disease_label) after classification. A public dataset like
PlantVillage (Kaggle) already comes in roughly this shape with light
folder renaming.

Usage:
    pip install -r requirements-training.txt
    python train_classifier.py --data-dir /path/to/dataset --epochs 15

Output (in ml/disease_classifier/models/):
    model.onnx           -> the trained model, upload via Admin Panel
    class_names.json     -> ordered list of {class_name, crop, disease_label}
                            matching the model's output indices
    training_report.json -> accuracy/loss history, upload alongside the
                            model so the Admin Panel can display it
"""

import os
import json
import argparse

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator

IMG_SIZE = (224, 224)
BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "models")


def parse_class_folder_name(folder_name: str) -> dict:
    """
    Splits a folder name like "Tomato__Early_Blight" into crop and
    disease_label, converting inner underscores to spaces for display.
    Folders without "__" are treated as crop="Unknown".
    """
    if "__" in folder_name:
        crop_raw, disease_raw = folder_name.split("__", 1)
    else:
        crop_raw, disease_raw = "Unknown", folder_name

    return {
        "class_name": folder_name,
        "crop": crop_raw.replace("_", " ").strip(),
        "disease_label": disease_raw.replace("_", " ").strip(),
    }


def build_model(num_classes: int) -> tf.keras.Model:
    base = MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet")
    base.trainable = False  # freeze the pretrained backbone initially

    inputs = layers.Input(shape=IMG_SIZE + (3,))
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs)
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def main():
    parser = argparse.ArgumentParser(description="Train the plant disease classifier")
    parser.add_argument("--data-dir", required=True, help="Path to dataset folder (one subfolder per class)")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--fine-tune-epochs", type=int, default=5,
                         help="Additional epochs unfreezing the last layers of MobileNetV2 for fine-tuning")
    args = parser.parse_args()

    datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        validation_split=0.2,
        rotation_range=20,
        horizontal_flip=True,
        zoom_range=0.15,
    )

    train_gen = datagen.flow_from_directory(
        args.data_dir, target_size=IMG_SIZE, batch_size=args.batch_size,
        class_mode="categorical", subset="training",
    )
    val_gen = datagen.flow_from_directory(
        args.data_dir, target_size=IMG_SIZE, batch_size=args.batch_size,
        class_mode="categorical", subset="validation",
    )

    class_names = sorted(train_gen.class_indices, key=train_gen.class_indices.get)
    print(f"Found {len(class_names)} classes: {class_names}")

    model = build_model(len(class_names))

    print("\n=== Phase 1: training classification head (backbone frozen) ===")
    history1 = model.fit(train_gen, validation_data=val_gen, epochs=args.epochs)

    print("\n=== Phase 2: fine-tuning last layers of MobileNetV2 ===")
    base_model = model.layers[1]
    base_model.trainable = True
    for layer in base_model.layers[:-30]:  # keep most of the backbone frozen
        layer.trainable = False
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-5),
                  loss="categorical_crossentropy", metrics=["accuracy"])
    history2 = model.fit(train_gen, validation_data=val_gen, epochs=args.fine_tune_epochs)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Export to ONNX for lightweight production serving ---
    try:
        import tf2onnx
        spec = (tf.TensorSpec((None,) + IMG_SIZE + (3,), tf.float32, name="input"),)
        onnx_path = os.path.join(OUTPUT_DIR, "model.onnx")
        tf2onnx.convert.from_keras(model, input_signature=spec, output_path=onnx_path)
        print(f"Saved ONNX model -> {onnx_path}")
    except ImportError:
        print("tf2onnx not installed — install it with `pip install tf2onnx` and re-run, "
              "or export manually. Saving Keras .h5 as a fallback instead.")
        model.save(os.path.join(OUTPUT_DIR, "model.h5"))

    with open(os.path.join(OUTPUT_DIR, "class_names.json"), "w") as f:
        class_metadata = [parse_class_folder_name(name) for name in class_names]
        json.dump(class_metadata, f, indent=2)

    report = {
        "num_classes": len(class_names),
        "class_names": class_names,
        "phase1_final_val_accuracy": float(history1.history["val_accuracy"][-1]),
        "phase2_final_val_accuracy": float(history2.history["val_accuracy"][-1]),
    }
    with open(os.path.join(OUTPUT_DIR, "training_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nFinal validation accuracy: {report['phase2_final_val_accuracy']:.3f}")
    print(f"\nNext step: upload model.onnx, class_names.json, and training_report.json "
          f"through the Admin Panel's 'Train Custom Model' tab to deploy this to production.")


if __name__ == "__main__":
    main()
