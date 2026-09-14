"""
classification_metrics.py — การวัดผลงานจำแนกและกับดัก Accuracy Paradox
บทที่ 9 · วิชา 06026240 การพัฒนาระบบอัจฉริยะ

ครอบคลุม:
- Confusion Matrix (TP, FP, TN, FN)
- Accuracy, Precision, Recall, Specificity, F1-Score
- Matthews Correlation Coefficient (MCC)
- Accuracy Paradox Demonstration (ชุดข้อมูลไม่สมดุล)
- Cost-sensitive Trade-off Analysis (Precision vs Recall)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def compute_confusion_matrix(
    y_true: List[int | bool | str],
    y_pred: List[int | bool | str],
    pos_label: Any = 1
) -> Dict[str, int]:
    """
    คำนวณ Confusion Matrix 4 ช่อง
    - TP: ทายบวก และจริงบวก (เช่น จับใบเบลอได้ถูกต้อง)
    - FP: ทายบวก แต่จริงลบ (เช่น ตีตกใบที่ใช้ได้จริง -> User สแกนใหม่ / Alarm fatigue)
    - TN: ทายลบ และจริงลบ (เช่น ปล่อยใบที่ชัดเจนผ่านตามปกติ)
    - FN: ทายลบ แต่จริงบวก (เช่น ปล่อยใบเสียหลุดเข้า OCR -> ข้อมูลผิดเข้าฐานข้อมูล)
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"ขนาดของข้อมูลไม่เท่ากัน: {len(y_true)} vs {len(y_pred)}")

    tp = fp = tn = fn = 0
    for true, pred in zip(y_true, y_pred):
        is_true_pos = (true == pos_label)
        is_pred_pos = (pred == pos_label)

        if is_true_pos and is_pred_pos:
            tp += 1
        elif not is_true_pos and is_pred_pos:
            fp += 1
        elif not is_true_pos and not is_pred_pos:
            tn += 1
        else:
            fn += 1

    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn}


def compute_classification_metrics(cm: Dict[str, int]) -> Dict[str, float]:
    """
    คำนวณตัวชี้วัดพื้นฐานทั้งหมดจาก Confusion Matrix
    """
    tp = cm["TP"]
    fp = cm["FP"]
    tn = cm["TN"]
    fn = cm["FN"]
    total = tp + fp + tn + fn

    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    # Matthews Correlation Coefficient (MCC)
    # MCC = (TP*TN - FP*FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))
    numerator = (tp * tn) - (fp * fn)
    denominator_sq = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denominator_sq > 0:
        mcc = numerator / math.sqrt(denominator_sq)
    else:
        mcc = 0.0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "f1": round(f1, 4),
        "mcc": round(mcc, 4),
    }


def analyze_accuracy_paradox(
    n_total: int = 1000,
    n_forged: int = 10
) -> Dict[str, Any]:
    """
    สาธิตกับดัก Accuracy Paradox ตามตัวอย่างในสไลด์หน้า 7
    เอกสาร 1,000 หน้า มีหน้าปลอม 10 หน้า
    โมเดลง่ายๆ ที่ทาย 'ไม่ปลอม' ทุกหน้า จะได้ Accuracy 99%
    แต่ Recall = 0.0 และ MCC = 0.0 บ่งชี้ว่าโมเดลไม่ได้เรียนรู้อะไรเลย
    """
    y_true = [1] * n_forged + [0] * (n_total - n_forged)
    y_pred_naive = [0] * n_total  # โมเดลขี้เกียจ ตอบลบทุกใบ

    cm = compute_confusion_matrix(y_true, y_pred_naive, pos_label=1)
    metrics = compute_classification_metrics(cm)

    return {
        "scenario": f"ตรวจเอกสาร {n_total} หน้า (ปลอม {n_forged} หน้า, ปกติ {n_total - n_forged} หน้า)",
        "model_behavior": "โมเดลทำนายว่า 'ไม่ปลอม' ทั้งหมด",
        "confusion_matrix": cm,
        "metrics": metrics,
        "insight": (
            f"แม้ Accuracy จะสูงถึง {metrics['accuracy'] * 100:.1f}% แต่ Recall = {metrics['recall']} "
            f"และ MCC = {metrics['mcc']} ยืนยันว่าโมเดลไม่สามารถตรวจจับของปลอมได้เลยแม้แต่หน้าเดียว "
            "เมื่อข้อมูลไม่สมดุลเกิน 80:20 ห้ามดู Accuracy เป็นหลัก ให้ดู Recall ของ Rare Class และ MCC เสมอ"
        )
    }
