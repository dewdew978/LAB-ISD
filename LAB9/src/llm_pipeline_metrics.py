"""
llm_pipeline_metrics.py — การวัดผลงาน LLM, โครงสร้าง JSON และ Text-to-SQL
บทที่ 9 · วิชา 06026240 การพัฒนาระบบอัจฉริยะ

ครอบคลุม:
- JSON Valid Rate (สัดส่วนที่ parse JSON ได้)
- Schema Pass Rate (สัดส่วนที่ผ่าน Pydantic ตั้งแต่รอบแรก)
- Repair Rate (สัดส่วนที่ต้องวนซ่อม)
- Field-level Precision / Recall (วัดรายฟิลด์ ไม่ใช่แค่รายเอกสาร)
- Coverage & Abstain Rate (การปฏิเสธที่จะเดาเมื่อไม่มีข้อมูล / Negative Testing)
- Valid SQL Rate (สัดส่วน SQL ที่รันผ่านโดยไม่มีข้อผิดพลาด)
- Execution Accuracy (SQL) (ผลลัพธ์ของ SQL ตรงกับเฉลย)
- Faithfulness / Groundedness (คำตอบมาจากเอกสารจริง ไม่แต่งขึ้นเอง)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Set


def evaluate_json_and_schema_quality(
    raw_outputs: List[str],
    validator_func: Any = None
) -> Dict[str, Any]:
    """
    วัดคุณภาพของผลลัพธ์ที่มีโครงสร้าง (สไลด์หน้า 18)
    - JSON valid rate
    - Schema pass rate
    - Repair rate
    """
    total = len(raw_outputs)
    if total == 0:
        return {"total": 0, "json_valid_rate": 0.0, "schema_pass_rate": 0.0}

    valid_json_count = 0
    schema_pass_count = 0

    for text in raw_outputs:
        try:
            parsed = json.loads(text)
            valid_json_count += 1
            if validator_func:
                if validator_func(parsed):
                    schema_pass_count += 1
            else:
                schema_pass_count += 1
        except Exception:
            pass

    return {
        "total_samples": total,
        "json_valid_count": valid_json_count,
        "json_valid_rate": round(valid_json_count / total, 4),
        "schema_pass_count": schema_pass_count,
        "schema_pass_rate": round(schema_pass_count / total, 4),
        "repair_needed_rate": round(1.0 - (schema_pass_count / total), 4)
    }


def evaluate_field_level_precision_recall(
    gt_courses: List[Dict[str, Any]],
    pred_courses: List[Dict[str, Any]],
    key_field: str = "code",
    compare_fields: List[str] = None
) -> Dict[str, Any]:
    """
    วัดความแม่นยำระดับฟิลด์ (Field-level Precision / Recall)
    - Recall สูง = สกัดครบ ไม่ตกหล่น
    - Precision สูง = ไม่เติมของที่ไม่มี (ไม่มีวิชาผี)
    """
    if compare_fields is None:
        compare_fields = ["name_th", "credits", "year", "semester"]

    gt_map = {str(c.get(key_field, "")).strip(): c for c in gt_courses if c.get(key_field)}
    pred_map = {str(c.get(key_field, "")).strip(): c for c in pred_courses if c.get(key_field)}

    gt_keys = set(gt_map.keys())
    pred_keys = set(pred_map.keys())

    matched_keys = gt_keys.intersection(pred_keys)
    missed_keys = gt_keys - pred_keys
    spurious_keys = pred_keys - gt_keys

    p = len(matched_keys) / len(pred_keys) if pred_keys else 0.0
    r = len(matched_keys) / len(gt_keys) if gt_keys else 0.0
    f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

    # ตรวจสอบความถูกต้องรายฟิลด์ของวิชาที่ match กันได้
    field_accuracies = {}
    for f in compare_fields:
        correct_count = 0
        for k in matched_keys:
            gt_val = str(gt_map[k].get(f, "")).strip().lower()
            pred_val = str(pred_map[k].get(f, "")).strip().lower()
            if gt_val == pred_val:
                correct_count += 1
        acc = correct_count / len(matched_keys) if matched_keys else 0.0
        field_accuracies[f] = round(acc, 4)

    return {
        "ground_truth_count": len(gt_keys),
        "prediction_count": len(pred_keys),
        "matched_count": len(matched_keys),
        "missed_count": len(missed_keys),
        "spurious_count": len(spurious_keys),
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1_score": round(f1, 4),
        "field_accuracies": field_accuracies
    }


def evaluate_text_to_sql_execution(
    eval_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    วัดผลลัพธ์ Text-to-SQL (สไลด์หน้า 19):
    1. Valid SQL Rate: สัดส่วนคำสั่ง SQL ที่รันผ่านโดยไม่มี error
    2. Execution Accuracy (SQL): ผลลัพธ์จากการรัน SQL ตรงกับคำตอบที่ควรได้
    3. Abstain / Negative Testing Accuracy: ระบบยอมรับว่าไม่พบข้อมูลเมื่อไม่มีข้อมูลจริง
    """
    total = len(eval_results)
    if total == 0:
        return {"total": 0, "valid_sql_rate": 0.0, "execution_accuracy": 0.0}

    valid_sql_count = 0
    correct_answer_count = 0
    negative_total = 0
    negative_correct = 0

    for item in eval_results:
        # SQL รันผ่าน
        sql_ok = (item.get("error") is None)
        if sql_ok:
            valid_sql_count += 1

        # คำตอบถูก
        is_correct = bool(item.get("correct", False))
        if is_correct:
            correct_answer_count += 1

        # คำถามเชิงปฏิเสธ (Negative Testing เช่น type == 'none')
        expect_type = item.get("expect", {}).get("type")
        if expect_type == "none":
            negative_total += 1
            if is_correct:
                negative_correct += 1

    valid_sql_rate = valid_sql_count / total
    exec_accuracy = correct_answer_count / total
    abstain_accuracy = negative_correct / negative_total if negative_total > 0 else 1.0

    return {
        "total_questions": total,
        "valid_sql_count": valid_sql_count,
        "valid_sql_rate": round(valid_sql_rate, 4),
        "correct_answer_count": correct_answer_count,
        "execution_accuracy": round(exec_accuracy, 4),
        "negative_questions_count": negative_total,
        "abstain_accuracy": round(abstain_accuracy, 4),
        "analysis": {
            "sql_generation": "สมบูรณ์แบบ" if valid_sql_rate == 1.0 else f"ต้องปรับแก้ schema/VIEW (พลาด {total - valid_sql_count} ข้อ)",
            "intent_understanding": "สมบูรณ์แบบ" if exec_accuracy == 1.0 else f"ต้องปรับปรุง Prompt/ตัวอย่าง (ตอบผิด {total - correct_answer_count} ข้อ)"
        }
    }
