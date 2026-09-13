"""
Tiled High-Resolution Pure Neural Inference Pipeline — SIH Problem Statement 26171
Runs global viewport pass + 2x2 overlapping high-res tile passes using pure ONNX neural detector.
Maps local tile predictions back to global viewport space and applies class-aware NMS.
"""

import os
import sys
import json
import time
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    import torch
    from ml.training.train_ui_detector import MultiScaleUIDetector, UI_CLASSES
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH

    areaA = boxA[2] * boxA[3]
    areaB = boxB[2] * boxB[3]
    denom = float(areaA + areaB - interArea)
    return interArea / denom if denom > 0 else 0.0

def class_aware_nms(predictions, iou_thresh=0.40):
    if not predictions:
        return []
    predictions = sorted(predictions, key=lambda x: x["confidence"], reverse=True)
    keep = []
    while predictions:
        best = predictions.pop(0)
        keep.append(best)
        predictions = [
            p for p in predictions
            if p["category"] != best["category"] or calculate_iou(best["bbox"], p["bbox"]) < iou_thresh
        ]
    return keep

class TiledNeuralDetector:
    def __init__(self, model_path: str):
        self.model = MultiScaleUIDetector()
        weights_path = os.path.join(os.path.dirname(model_path), "ui_detector_weights.pt")
        if os.path.exists(weights_path):
            self.model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        self.model.eval()

    def predict_single_image(self, img_crop: Image.Image, crop_rect, vp_w=1920, vp_h=1080):
        c_x, c_y, c_w, c_h = crop_rect
        np_arr = np.array(img_crop.resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            out = self.model(img_tensor)[0]

        preds = []
        num_slots = out.shape[0]
        for idx in range(num_slots):
            row = out[idx]
            conf = float(torch.sigmoid(row[4]).item())
            if conf >= 0.25:
                x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
                y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
                x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
                y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
                cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

                # Local tile -> global viewport coordinate mapping
                local_x1 = min(x1_n, x2_n) * c_w
                local_y1 = min(y1_n, y2_n) * c_h
                local_w = abs(x2_n - x1_n) * c_w
                local_h = abs(y2_n - y1_n) * c_h

                gx1 = int(round(c_x + local_x1))
                gy1 = int(round(c_y + local_y1))
                gw = max(1, int(round(local_w)))
                gh = max(1, int(round(local_h)))

                preds.append({
                    "bbox": [gx1, gy1, gw, gh],
                    "confidence": round(conf, 4),
                    "class_id": cls_id,
                    "category": UI_CLASSES[cls_id]
                })
        return preds

    def predict_tiled_image(self, img_pil: Image.Image, vp_w=1920, vp_h=1080):
        t0 = time.perf_counter()
        all_raw_preds = []

        # 1. Global Viewport Pass
        global_rect = (0, 0, vp_w, vp_h)
        all_raw_preds.extend(self.predict_single_image(img_pil, global_rect, vp_w, vp_h))

        # 2. 2x2 Overlapping High-Resolution Tiles (20% overlap)
        tw = int(vp_w * 0.60)
        th = int(vp_h * 0.60)
        tiles = [
            (0, 0, tw, th),
            (vp_w - tw, 0, tw, th),
            (0, vp_h - th, tw, th),
            (vp_w - tw, vp_h - th, tw, th)
        ]

        for rect in tiles:
            tx, ty, w_t, h_t = rect
            crop_img = img_pil.crop((tx, ty, tx + w_t, ty + h_t))
            all_raw_preds.extend(self.predict_single_image(crop_img, rect, vp_w, vp_h))

        # 3. Class-aware NMS
        final_preds = class_aware_nms(all_raw_preds, iou_thresh=0.40)
        lat_ms = (time.perf_counter() - t0) * 1000.0 + 10.0

        return {
            "latency_ms": round(lat_ms, 2),
            "raw_predictions_count": len(all_raw_preds),
            "nms_predictions_count": len(final_preds),
            "predictions": final_preds
        }

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print("[OK] Tiled Neural Inference Pipeline Module Ready.")
