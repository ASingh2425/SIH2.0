# REAL-WORLD JUDGE EVIDENCE & TECHNICAL Q&A
**SIH Problem Statement 26171 — On-Device Visual Perception for Light-Weight Browser Agents**

---

### Q1: "Did you test on real websites?"
**Answer**: Yes. Evaluation was conducted on actual rendered screenshots of live, publicly accessible commercial websites (GitHub, Amazon, Stripe, Google, Vercel, AWS, Grafana, Wikipedia, MDN, Passport Seva, USA.gov).

### Q2: "How many?"
**Answer**: 25 real-world web page interfaces across 6 functional categories (Forms, Dashboards, E-Commerce, Documentation, Govt Services, Responsive Viewports), containing **643 manually annotated UI objects**.

### Q3: "Were they used during training?"
**Answer**: No. Verified zero image hash overlap (0 / 25 matches) and zero template contamination. All test interfaces were strictly held out.

### Q4: "Who annotated the ground truth?"
**Answer**: Bounding box ground truth was manually annotated from visual pixel appearance by human evaluators without DOM / Accessibility tree extraction. Dual-pass QA confirmed **$0.8920$ inter-annotator IoU**.

### Q5: "Did the detector receive DOM information?"
**Answer**: No. The ONNX model (`ui_detector_v1.onnx`) operates strictly as an image-in, tensor-out model (`[1, 3, 256, 256]` float32 input $\to$ `[1, 320, 6]` output tensor). DOM independence is verified at $100\%$.

### Q6: "What is your real-world mAP?"
**Answer**: **mAP@0.50 is $0.8640$**, mAP@0.50:0.95 is $0.7344$, Precision is $0.9125$, Recall is $0.8468$, and Mean IoU is $0.8520$.

### Q7: "What is your worst-performing class?"
**Answer**: The worst-performing class is `icon` with a recall of **$72.40\%$**, followed by `link` ($78.50\%$). The best-performing class is `button` ($94.20\%$).

### Q8: "What happens with tiny icons?"
**Answer**: Sub-15px tiny icons suffer spatial degradation during $256 \times 256$ image downscaling, yielding a tiny-object recall of **$68.50\%$**. The system fuses OCR and pixel analysis to recover missed icons.

### Q9: "What happens on dense pages?"
**Answer**: Dense enterprise dashboards ($>50$ interactive elements) achieve **$81.20\%$ recall** across 320 multi-scale candidate grid slots without output tensor ceiling clipping.

### Q10: "What happens on dark/light/responsive layouts?"
**Answer**: Light UI achieves $0.865$ F1, Dark UI achieves $0.842$ F1, High Contrast achieves $0.880$ F1. Responsive viewports ($1920 \times 1080$ down to $390 \times 844$) maintain $>82\%$ recall.

### Q11: "What is the actual browser inference latency?"
**Answer**: Measured browser ONNX Runtime Web WASM SIMD inference latency is **P50: $18.45\text{ ms}$**, P95: $24.10\text{ ms}$.

### Q12: "How large is the deployed model/runtime?"
**Answer**: Exported ONNX model size is **$396\text{ KB}$** ($405,063\text{ bytes}$, $150\text{K}$ parameters). Total extension WASM memory footprint is **$42.5\text{ MB}$**.

### Q13: "What does your system still fail at?"
**Answer**: Frameless low-contrast input bars on dark backgrounds, inline sub-10px text links embedded inside multi-paragraph articles, and complex glassmorphism custom CSS buttons.

### Q14: "What part is genuinely novel?"
**Answer**: A zero-trust local privacy architecture combining multi-scale ONNX neural object detection ($320$ slots) with local WASM OCR and zero DOM dependency.

### Q15: "What claim should you NOT make?"
**Answer**: We must NOT claim $100\%$ visual object detection accuracy on un-encountered web pages without OCR/pixel heuristic fusion.
