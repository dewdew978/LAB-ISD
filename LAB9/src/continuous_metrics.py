"""
continuous_metrics.py — การวัดผลงานทำนายค่าต่อเนื่อง (Regression)
บทที่ 9 · วิชา 06026240 การพัฒนาระบบอัจฉริยะ

ครอบคลุม:
- MAE (Mean Absolute Error)
- MSE (Mean Squared Error) & RMSE (Root Mean Squared Error)
- Error Spread Analysis (RMSE - MAE) เพื่อจับบริเวณที่พังหนัก
- MAPE (Mean Absolute Percentage Error) พร้อมการป้องกันหารด้วย 0
- Huber Loss (Smooth L1) สำหรับการเทรนที่มี Outlier
"""

from __future__ import annotations

import math
from typing import Any, Dict, List


def mean_absolute_error(y_true: List[float], y_pred: List[float]) -> float:
    """MAE = (1/n) * sum(|y_i - y_hat_i|)"""
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        raise ValueError("ขนาดของข้อมูลไม่ถูกต้องหรือไม่เท่ากัน")
    return sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)


def mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
    """MSE = (1/n) * sum((y_i - y_hat_i)^2)"""
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        raise ValueError("ขนาดของข้อมูลไม่ถูกต้องหรือไม่เท่ากัน")
    return sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true)


def root_mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
    """RMSE = sqrt(MSE)"""
    return math.sqrt(mean_squared_error(y_true, y_pred))


def mean_absolute_percentage_error(
    y_true: List[float],
    y_pred: List[float],
    epsilon: float = 1e-6
) -> float:
    """
    MAPE = (100/n) * sum(|(y_i - y_hat_i) / y_i|)
    ระวัง: หาก y_i เข้าใกล้ 0 ตัวหารจะระเบิดเป็นอนันต์ จึงใช้ epsilon ป้องกัน
    """
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        raise ValueError("ขนาดของข้อมูลไม่ถูกต้องหรือไม่เท่ากัน")
    
    total_pct = 0.0
    for t, p in zip(y_true, y_pred):
        denominator = abs(t) if abs(t) > epsilon else epsilon
        total_pct += abs((t - p) / denominator)
    return (total_pct / len(y_true)) * 100.0


def huber_loss(
    y_true: List[float],
    y_pred: List[float],
    delta: float = 1.0
) -> float:
    """
    Huber Loss (Smooth L1)
    - ถ้า |error| <= delta : 0.5 * error^2 (เหมือน MSE)
    - ถ้า |error| > delta  : delta * |error| - 0.5 * delta^2 (เหมือน MAE)
    """
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        raise ValueError("ขนาดของข้อมูลไม่ถูกต้องหรือไม่เท่ากัน")
    
    losses = []
    for t, p in zip(y_true, y_pred):
        err = abs(t - p)
        if err <= delta:
            losses.append(0.5 * (err ** 2))
        else:
            losses.append((delta * err) - (0.5 * (delta ** 2)))
    return sum(losses) / len(losses)


def evaluate_continuous_predictions(
    y_true: List[float],
    y_pred: List[float],
    delta: float = 1.0
) -> Dict[str, Any]:
    """
    ประเมินตัวชี้วัดทั้งหมดและวิเคราะห์การกระจายตัวของความผิดพลาด
    """
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = math.sqrt(mse)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    huber = huber_loss(y_true, y_pred, delta=delta)

    # วิเคราะห์ความต่างระหว่าง RMSE กับ MAE
    gap = rmse - mae
    if gap > (mae * 1.5):
        diagnostics = (
            f"RMSE ({rmse:.3f}) สูงกว่า MAE ({mae:.3f}) อย่างมีนัยสำคัญ (Gap: {gap:.3f}) "
            "บ่งชี้ว่ามีความผิดพลาดขนาดใหญ่เฉพาะจุด (Severe Outliers / พังหนักบางบริเวณ) "
            "ไม่ควรดูแค่ MAE เพราะค่าเฉลี่ยกลบจุดที่เสียหายรุนแรง"
        )
    else:
        diagnostics = (
            f"RMSE ({rmse:.3f}) ใกล้เคียงกับ MAE ({mae:.3f}) "
            "แสดงว่าความคลาดเคลื่อนกระจายตัวค่อนข้างสม่ำเสมอทั่วทั้งชุดข้อมูล ไม่มี Outlier รุนแรง"
        )

    return {
        "MAE": round(mae, 4),
        "MSE": round(mse, 4),
        "RMSE": round(rmse, 4),
        "MAPE(%)": round(mape, 2),
        "HuberLoss": round(huber, 4),
        "RMSE_MAE_gap": round(gap, 4),
        "diagnostics": diagnostics
    }
