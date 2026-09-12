from typing import List, Dict, Any

class MetricsCalculator:
    @staticmethod
    def calculate_pii_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return {
            "pii_precision_pct": round(precision * 100, 2),
            "pii_recall_pct": round(recall * 100, 2),
            "pii_f1_score": round(f1, 4)
        }

    @staticmethod
    def calculate_minimum_disclosure_score(
        available_sensitive: int,
        unnecessary_exposed: int
    ) -> float:
        if available_sensitive == 0:
            return 1.0
        mds = 1.0 - (unnecessary_exposed / available_sensitive)
        return max(0.0, round(mds, 4))

    @staticmethod
    def calculate_privacy_utility_efficiency(
        mds: float,
        task_success_rate: float
    ) -> float:
        pue = mds * task_success_rate
        return round(pue, 4)

    @staticmethod
    def generate_p1_multimodal_evaluation_report(
        dom_extraction_accuracy_pct: float,
        visual_perception_accuracy_pct: float,
        tp: int, fp: int, fn: int,
        redaction_precision_pct: float,
        cpu_usage_pct: float, ram_usage_mb: float,
        perception_ms: float, ocr_ms: float, mde_ms: float, firewall_ms: float, network_ms: float, remote_vlm_ms: float,
        available_sensitive: int, unnecessary_exposed: int, task_success: bool,
        backend_used: str = "webgpu",
        fast_path: bool = False
    ) -> Dict[str, Any]:

        pii_stats = MetricsCalculator.calculate_pii_metrics(tp, fp, fn)
        mds = MetricsCalculator.calculate_minimum_disclosure_score(available_sensitive, unnecessary_exposed)
        pue = MetricsCalculator.calculate_privacy_utility_efficiency(mds, 1.0 if task_success else 0.0)

        total_e2e_ms = perception_ms + ocr_ms + mde_ms + firewall_ms + network_ms + remote_vlm_ms

        return {
            "reclassified_accuracy_metrics": {
                "dom_context_extraction_accuracy_pct": dom_extraction_accuracy_pct,
                "visual_perception_accuracy_pct": visual_perception_accuracy_pct,
                "pii_precision_pct": pii_stats["pii_precision_pct"],
                "pii_recall_pct": pii_stats["pii_recall_pct"],
                "redaction_precision_pct": redaction_precision_pct
            },
            "system_performance": {
                "avg_cpu_pct": cpu_usage_pct,
                "peak_ram_mb": ram_usage_mb,
                "fast_path_used": fast_path,
                "ml_backend": backend_used
            },
            "signature_project_metrics": {
                "minimum_disclosure_score": mds,
                "privacy_utility_efficiency": pue
            },
            "latency_breakdown_ms": {
                "perception_ms": round(perception_ms, 2),
                "ocr_ms": round(ocr_ms, 2),
                "mde_ms": round(mde_ms, 2),
                "firewall_ms": round(firewall_ms, 2),
                "network_ms": round(network_ms, 2),
                "remote_vlm_ms": round(remote_vlm_ms, 2),
                "total_e2e_latency_ms": round(total_e2e_ms, 2)
            }
        }
