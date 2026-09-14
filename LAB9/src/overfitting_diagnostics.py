"""
overfitting_diagnostics.py — การตรวจจับและแก้ปัญหา Overfitting
บทที่ 9 · วิชา 06026240 การพัฒนาระบบอัจฉริยะ

ครอบคลุม:
- Learning Curve Analyzer (ตรวจจุดที่ Val Loss เริ่มดีดขึ้นขณะ Train Loss ลดลง)
- Slice Analysis (วิเคราะห์ผลแยกตามกลุ่ม/หลักสูตรเพื่อจับ Shortcut Learning)
- Seed Sensitivity Test (ทดสอบความแปรปรวนจาก Random Seed)
- Ensemble Simulator (4 รูปแบบ: Bagging, Boosting, Stacking, Voting)
- Diagnostic Engine: ตรวจโรคและจ่ายยาแก้ให้ถูกจุด (ห้ามแก้ผิดโรคระหว่าง Overfitting กับ Underfitting)
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Tuple


def analyze_learning_curve(
    train_losses: List[float],
    val_losses: List[float]
) -> Dict[str, Any]:
    """
    วิเคราะห์ Learning Curve ตามสไลด์หน้า 24-25:
    - หาจุดต่ำสุดของ Validation Loss (Best Epoch / Early Stopping Point)
    - ตรวจจับจุดที่เริ่มเกิด Overfitting
    - สรุปสถานะว่าเป็น Underfitting, Good Fit หรือ Overfitting
    """
    if len(train_losses) != len(val_losses) or len(train_losses) == 0:
        raise ValueError("จำนวน epoch ของ train และ val ต้องเท่ากันและมากกว่า 0")

    min_val_loss = min(val_losses)
    best_epoch = val_losses.index(min_val_loss) + 1
    final_train_loss = train_losses[-1]
    final_val_loss = val_losses[-1]

    # ตรวจสอบว่าหลังจากจุดต่ำสุด Val Loss มีการลอยตัวสูงขึ้นอย่างต่อเนื่องหรือไม่
    overfit_detected = False
    patience_counter = 0
    inflection_epoch = best_epoch

    for ep, (t_loss, v_loss) in enumerate(zip(train_losses, val_losses), 1):
        if ep > best_epoch and v_loss > min_val_loss:
            patience_counter += 1
            if patience_counter >= 3 and t_loss < train_losses[best_epoch - 1]:
                overfit_detected = True
                inflection_epoch = best_epoch
                break

    # วินิจฉัยสภาวะ
    gap = final_val_loss - final_train_loss
    if final_train_loss > 1.0 and final_val_loss > 1.0:
        state = "Underfitting (โมเดลง่ายเกินไป หรือเทรนน้อยเกินไป ชุดฝึกก็แย่ ชุดตรวจสอบก็แย่)"
    elif overfit_detected or gap > (final_train_loss * 1.2):
        state = f"Overfitting (โมเดลเริ่มจำข้อสอบเก่าที่ Epoch {inflection_epoch} Val loss ดีดขึ้นแต่ Train loss ยังลง)"
    else:
        state = "Good Fit (โมเดลเรียนรู้ลักษณะทั่วไปได้ดี ความต่างระหว่าง Train และ Val อยู่ในเกณฑ์เหมาะสม)"

    return {
        "total_epochs": len(train_losses),
        "best_epoch": best_epoch,
        "min_validation_loss": round(min_val_loss, 4),
        "final_train_loss": round(final_train_loss, 4),
        "final_val_loss": round(final_val_loss, 4),
        "generalization_gap": round(gap, 4),
        "is_overfitting": overfit_detected,
        "diagnosis": state,
        "recommendation": (
            f"ควรใช้ Early Stopping ตัดการเทรนที่ Epoch {best_epoch} (patience=5-10) "
            "พร้อมพิจารณาเพิ่ม Data Augmentation หรือ Dropout" if overfit_detected else "โมเดลมีเสถียรภาพดี"
        )
    }


def perform_slice_analysis(
    slices: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Slice Analysis (สไลด์หน้า 25)
    แยกวิเคราะห์ประสิทธิภาพตามแหล่งข้อมูล / หลักสูตร (เช่น DSBA, IT, AIT, BIT)
    เพื่อตรวจสอบว่าโมเดลเก่งเฉพาะแหล่งข้อมูลเดิม (Shortcut Learning) หรือไม่
    """
    scores = {name: metrics.get("f1_score", metrics.get("accuracy", 0.0)) for name, metrics in slices.items()}
    values = list(scores.values())
    if not values:
        return {}

    mean_score = statistics.mean(values)
    stdev_score = statistics.stdev(values) if len(values) > 1 else 0.0
    min_slice = min(scores, key=scores.get)
    max_slice = max(scores, key=scores.get)
    disparity = scores[max_slice] - scores[min_slice]

    is_shortcut = (disparity > 0.15)

    return {
        "slice_scores": scores,
        "mean_score": round(mean_score, 4),
        "standard_deviation": round(stdev_score, 4),
        "score_disparity": round(disparity, 4),
        "highest_slice": f"{max_slice} ({scores[max_slice]:.4f})",
        "lowest_slice": f"{min_slice} ({scores[min_slice]:.4f})",
        "has_shortcut_learning": is_shortcut,
        "insight": (
            f"พบความเหลื่อมล้ำสูง ({disparity*100:.1f}%) ระหว่าง {max_slice} กับ {min_slice} "
            "โมเดลอาจเรียนรู้ลักษณะเฉพาะของเอกสารบางชุด (Shortcut Learning) แทนที่จะเข้าใจเนื้อหาจริง"
            if is_shortcut else "ประสิทธิภาพกระจายตัวสม่ำเสมอข้ามทุกกลุ่มข้อมูล ไม่พบ Shortcut Learning"
        )
    }


def simulate_ensemble(
    predictions_per_model: List[List[Any]],
    method: str = "voting"
) -> List[Any]:
    """
    Ensemble Simulator (สไลด์หน้า 27)
    จำลองการรวมผลจากหลายโมเดล:
    - voting: โหวตเสียงข้างมาก
    - averaging: เฉลี่ยความน่าจะเป็นหรือค่าตัวเลข
    """
    n_samples = len(predictions_per_model[0])
    ensemble_results = []

    for i in range(n_samples):
        sample_preds = [m[i] for m in predictions_per_model]
        if method == "voting":
            # Majority voting
            winner = max(set(sample_preds), key=sample_preds.count)
            ensemble_results.append(winner)
        elif method == "averaging":
            # Numeric averaging
            avg_val = sum(float(x) for x in sample_preds) / len(sample_preds)
            ensemble_results.append(avg_val)

    return ensemble_results


def diagnose_and_prescribe(
    train_score: float,
    val_score: float,
    metric_name: str = "Accuracy"
) -> Dict[str, Any]:
    """
    ระบบตรวจวินิจฉัยและจ่ายยาแก้ให้ถูกโรค (สไลด์หน้า 28)
    ป้องกันการนำวิธีแก้ Overfitting ไปใช้กับ Underfitting
    """
    gap = train_score - val_score

    if train_score < 0.70 and val_score < 0.70:
        condition = "Underfitting (โมเดลยังเรียนรู้ไม่พอ)"
        prescriptions = [
            "1. เพิ่มขนาดหรือความลึกของโมเดล (Model Capacity)",
            "2. ลด Regularization และลด Dropout ลง",
            "3. ฝึกนานขึ้น (Train longer) หรือปรับ Learning Rate",
            "4. เพิ่ม Feature ที่มีข้อมูลชี้นำมากขึ้น",
            "5. ตรวจสอบ Preprocessing ว่าทำลายข้อมูลหรือไม่ (เช่น ย่อรูปจนอ่านไม่ออก)",
            "6. ในงาน LLM: ใช้โมเดลที่ใหญ่ขึ้น หรือเพิ่ม Context ให้เพียงพอ"
        ]
        forbidden = "ห้ามเพิ่ม Dropout, ห้ามลดขนาดโมเดล, ห้ามหยุดเทรนเร็วขึ้น เพราะจะยิ่งทำให้ Underfit หนักขึ้น"
    elif gap > 0.15:
        condition = "Overfitting (โมเดลจำชุดฝึกมากเกินไปจนความสามารถบนชุดทดสอบลดลง)"
        prescriptions = [
            "1. เพิ่มข้อมูลตัวอย่างจริง (Data Collection) — ได้ผลดีที่สุดเสมอ",
            "2. Data Augmentation (หมุน, ปรับแสง, Noise สมจริง)",
            "3. Early Stopping (หยุดฝึกที่จุด Val Loss ต่ำสุด)",
            "4. Transfer Learning (แช่แข็งชั้นต้น ฝึกเฉพาะชั้นท้าย)",
            "5. ลดขนาดโมเดล หรือเพิ่ม Regularization (L1/L2, Dropout 0.2-0.5)",
            "6. ในงาน LLM: ลด Few-shot ที่เจาะจงเกินไป และเขียน Prompt ให้เป็นกฎเกณฑ์ทั่วไป",
            "7. Ensemble (รวมผลหลายโมเดลเพื่อลดความแปรปรวน)"
        ]
        forbidden = "ห้ามขยายขนาดโมเดลให้ใหญ่ขึ้น และห้ามเทรนนานขึ้นโดยไม่มี Early Stopping"
    else:
        condition = "Well Balanced (โมเดลมีความสมดุลและ Generalization ดี)"
        prescriptions = [
            "1. รักษาสภาพแวดล้อมและ Hyperparameters เดิมไว้",
            "2. ตรวจสอบ Slice Analysis เพิ่มเติมเพื่อเช็กความเที่ยงตรงเฉพาะกลุ่ม"
        ]
        forbidden = "ไม่ต้องปรับลดขนาดหรือเพิ่ม Regularization เพิ่มเติมอย่างก้าวกระโดด"

    return {
        "condition": condition,
        "train_score": train_score,
        "val_score": val_score,
        "generalization_gap": round(gap, 4),
        "prescriptions": prescriptions,
        "warning_contraindicated": forbidden
    }
