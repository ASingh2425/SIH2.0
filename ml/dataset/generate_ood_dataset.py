"""
Out-of-Distribution (OOD) Challenge Dataset Generator
SIH Problem Statement 26171 — Non-Negotiable Forensic Rules

Generates held-out OOD test set with zero seed or template overlap with training data.
Contains small-object-heavy scenes, dense interfaces, and novel layout compositions.
"""

import json
import os
import random

UI_CLASSES = [
    "button", "input", "checkbox", "radio", "select",
    "link", "navigation", "card", "image", "icon", "text_block"
]

CLASS_MAP = {name: idx for idx, name in enumerate(UI_CLASSES)}

def generate_ood_scene(scene_id: int, layout_type: str, width=1920, height=1080):
    # Completely independent seed base (90000+)
    random.seed(90000 + scene_id * 3137)
    objects = []

    if layout_type == "dense_dashboard":
        # Sidebar Navigation
        objects.append({
            "id": f"ood_{scene_id}_sidebar",
            "category_id": CLASS_MAP["navigation"],
            "category": "navigation",
            "bbox": [0, 0, 240, height],
            "confidence": 0.95
        })

        # Sidebar icons & links
        for i in range(6):
            objects.append({
                "id": f"ood_{scene_id}_sb_icon_{i}",
                "category_id": CLASS_MAP["icon"],
                "category": "icon",
                "bbox": [25, 40 + i * 60, 24, 24],
                "confidence": 0.94
            })
            objects.append({
                "id": f"ood_{scene_id}_sb_link_{i}",
                "category_id": CLASS_MAP["link"],
                "category": "link",
                "bbox": [65, 42 + i * 60, 130, 20],
                "confidence": 0.92
            })

        # Main Dashboard Cards
        for row in range(2):
            for col in range(3):
                cx = 280 + col * 360
                cy = 40 + row * 340
                objects.append({
                    "id": f"ood_{scene_id}_card_{row}_{col}",
                    "category_id": CLASS_MAP["card"],
                    "category": "card",
                    "bbox": [cx, cy, 330, 300],
                    "confidence": 0.93
                })
                # Checkbox & Radio controls inside dashboard card
                objects.append({
                    "id": f"ood_{scene_id}_cb_{row}_{col}",
                    "category_id": CLASS_MAP["checkbox"],
                    "category": "checkbox",
                    "bbox": [cx + 20, cy + 30, 16, 16],
                    "confidence": 0.95
                })
                objects.append({
                    "id": f"ood_{scene_id}_radio_{row}_{col}",
                    "category_id": CLASS_MAP["radio"],
                    "category": "radio",
                    "bbox": [cx + 100, cy + 30, 16, 16],
                    "confidence": 0.95
                })
                objects.append({
                    "id": f"ood_{scene_id}_btn_{row}_{col}",
                    "category_id": CLASS_MAP["button"],
                    "category": "button",
                    "bbox": [cx + 20, cy + 240, 110, 38],
                    "confidence": 0.96
                })

    elif layout_type == "settings_modal":
        # Background nav
        objects.append({
            "id": f"ood_{scene_id}_bg_nav",
            "category_id": CLASS_MAP["navigation"],
            "category": "navigation",
            "bbox": [0, 0, width, 60],
            "confidence": 0.95
        })

        # Modal Dialog Card
        mw, mh = 650, 550
        mx, my = (width - mw) // 2, (height - mh) // 2
        objects.append({
            "id": f"ood_{scene_id}_modal_card",
            "category_id": CLASS_MAP["card"],
            "category": "card",
            "bbox": [mx, my, mw, mh],
            "confidence": 0.94
        })

        # Close Icon
        objects.append({
            "id": f"ood_{scene_id}_close_icon",
            "category_id": CLASS_MAP["icon"],
            "category": "icon",
            "bbox": [mx + mw - 40, my + 15, 24, 24],
            "confidence": 0.93
        })

        # Form Controls inside Modal
        for i in range(3):
            fy = my + 80 + i * 110
            objects.append({
                "id": f"ood_{scene_id}_input_{i}",
                "category_id": CLASS_MAP["input"],
                "category": "input",
                "bbox": [mx + 30, fy, mw - 60, 40],
                "confidence": 0.94
            })
            objects.append({
                "id": f"ood_{scene_id}_select_{i}",
                "category_id": CLASS_MAP["select"],
                "category": "select",
                "bbox": [mx + 30, fy + 48, 200, 36],
                "confidence": 0.92
            })
            objects.append({
                "id": f"ood_{scene_id}_cb_{i}",
                "category_id": CLASS_MAP["checkbox"],
                "category": "checkbox",
                "bbox": [mx + 250, fy + 56, 18, 18],
                "confidence": 0.95
            })

    else:  # E-commerce / Media Grid
        # Header Nav
        objects.append({
            "id": f"ood_{scene_id}_hdr",
            "category_id": CLASS_MAP["navigation"],
            "category": "navigation",
            "bbox": [0, 0, width, 70],
            "confidence": 0.95
        })

        # Product Cards Grid (4 items)
        for i in range(4):
            px = 80 + i * 440
            py = 120
            objects.append({
                "id": f"ood_{scene_id}_prod_card_{i}",
                "category_id": CLASS_MAP["card"],
                "category": "card",
                "bbox": [px, py, 400, 520],
                "confidence": 0.93
            })
            # Product Image
            objects.append({
                "id": f"ood_{scene_id}_prod_img_{i}",
                "category_id": CLASS_MAP["image"],
                "category": "image",
                "bbox": [px + 20, py + 20, 360, 220],
                "confidence": 0.91
            })
            # Text block
            objects.append({
                "id": f"ood_{scene_id}_prod_tb_{i}",
                "category_id": CLASS_MAP["text_block"],
                "category": "text_block",
                "bbox": [px + 20, py + 255, 360, 50],
                "confidence": 0.90
            })
            # Small Rating Icons
            for r in range(5):
                objects.append({
                    "id": f"ood_{scene_id}_star_{i}_{r}",
                    "category_id": CLASS_MAP["icon"],
                    "category": "icon",
                    "bbox": [px + 20 + r * 22, py + 315, 18, 18],
                    "confidence": 0.94
                })
            # Buy Button
            objects.append({
                "id": f"ood_{scene_id}_buy_btn_{i}",
                "category_id": CLASS_MAP["button"],
                "category": "button",
                "bbox": [px + 20, py + 450, 160, 42],
                "confidence": 0.96
            })

    return {
        "image_id": 9000 + scene_id,
        "layout_type": layout_type,
        "viewport": {"width": width, "height": height},
        "annotations": objects
    }

def main():
    base_dir = os.path.dirname(__file__)

    layout_types = ["dense_dashboard", "settings_modal", "ecommerce_grid"]
    ood_scenes = []

    for idx in range(1, 31):
        layout = layout_types[idx % len(layout_types)]
        scene = generate_ood_scene(idx, layout)
        ood_scenes.append(scene)

    ood_dataset_path = os.path.join(base_dir, "ood_challenge_dataset.json")
    with open(ood_dataset_path, "w") as f:
        json.dump({"split": "ood_challenge", "classes": UI_CLASSES, "samples": ood_scenes}, f, indent=2)

    total_bboxes = sum(len(s["annotations"]) for s in ood_scenes)
    print(f"[OK] Generated OOD Challenge Dataset: {len(ood_scenes)} scenes ({total_bboxes} bboxes) -> '{ood_dataset_path}'")

if __name__ == "__main__":
    main()
