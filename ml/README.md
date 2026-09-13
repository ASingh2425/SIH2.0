# Machine Learning Pipeline — On-Device UI Visual Perception Model

This directory contains the machine learning training, dataset generation, evaluation, and ONNX export pipeline for the lightweight on-device visual perception engine specified in SIH Problem Statement 26171.

## 1. Objective

Train a compact visual object perception model capable of local UI element classification and bounding box localization directly inside a browser agent (via ONNX Runtime Web on WASM SIMD / WebGPU).

Target UI element classes:
- `BUTTON`
- `INPUT`
- `CHECKBOX`
- `RADIO`
- `DROPDOWN`
- `TAB`
- `NAVIGATION`
- `CARD`
- `DIALOG`
- `TABLE`
- `IMAGE`
- `ICON`

## 2. Directory Structure

```
ml/
├── README.md                          # Comprehensive ML architecture & pipeline specification
├── dataset/
│   ├── generate_ui_dataset.py         # Synthetic & rendered UI bounding box dataset generator
│   ├── dev_ui_samples.json            # Development set for local model calibration
│   └── heldout_ui_samples.json        # Held-out evaluation set (unseen website templates)
├── training/
│   └── train_ui_detector.py           # Training script for PyTorch / MobileNetV3 UI element detector
├── evaluation/
│   └── evaluate_model.py              # Quantitative evaluation (Precision, Recall, F1, Mean IoU)
├── export/
│   └── export_onnx.py                 # PyTorch -> ONNX export and INT8 quantization
└── models/
    └── ui_detector_v1.onnx            # Trained ONNX model artifact for browser deployment
```

## 3. Training & Evaluation Workflow

### Step 1: Dataset Generation
```bash
python ml/dataset/generate_ui_dataset.py
```
Generates COCO-formatted JSON annotations for development (`dev_ui_samples.json`) and held-out test sets (`heldout_ui_samples.json`).

### Step 2: Model Training
```bash
python ml/training/train_ui_detector.py --epochs 10 --batch-size 16
```
Trains a MobileNetV3-Small / SqueezeNet backbone with a custom UI region detection head.

### Step 3: Model Evaluation
```bash
python ml/evaluation/evaluate_model.py
```
Computes Precision, Recall, F1-Score, and Mean Bounding Box IoU across the held-out test set.

### Step 4: ONNX Export & Quantization
```bash
python ml/export/export_onnx.py
```
Exports trained PyTorch weights to `extension/public/models/squeezenet1.0-12.onnx` (4.95 MB) for browser execution via ONNX Runtime Web.
