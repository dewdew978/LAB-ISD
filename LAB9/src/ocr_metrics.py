"""
ocr_metrics.py — การวัดผลงานข้อความและ OCR (CER, WER, Exact Match)
บทที่ 9 · วิชา 06026240 การพัฒนาระบบอัจฉริยะ

ครอบคลุม:
- Edit Distance (Levenshtein Distance: S, D, I)
- CER (Character Error Rate) ระดับตัวอักษร
- WER (Word Error Rate) ระดับคำ โดยใช้ pythainlp ตัดคำภาษาไทย
- Exact Match Ratio (EM)
- การวิเคราะห์เชิงเปรียบเทียบว่าทำไม CER ต่ำ แต่ WER สูงได้ (เจ็บจริงในงานปฏิบัติงาน)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

try:
    import pythainlp
    HAS_PYTHAINLP = True
except ImportError:
    HAS_PYTHAINLP = False


def levenshtein_ops(ref: List[Any], hyp: List[Any]) -> Tuple[int, int, int]:
    """
    คำนวณการแก้ไขระดับหน่วย (Substitution, Deletion, Insertion)
    โดยใช้ Dynamic Programming
    """
    m, n = len(ref), len(hyp)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # Deletion
                    dp[i][j - 1],      # Insertion
                    dp[i - 1][j - 1]   # Substitution
                )

    # Backtracking เพื่อแจงนับ S, D, I
    i, j = m, n
    s = d = ins = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hyp[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            s += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            d += 1
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            ins += 1
            j -= 1
        else:
            break

    return s, d, ins


def compute_cer(reference: str, hypothesis: str) -> Dict[str, Any]:
    """
    คำนวณ CER = (S + D + I) / N (ระดับตัวอักษร)
    """
    ref_chars = list(reference)
    hyp_chars = list(hypothesis)
    n = len(ref_chars)
    if n == 0:
        return {"cer": 0.0 if len(hyp_chars) == 0 else 1.0, "S": 0, "D": 0, "I": len(hyp_chars), "N": 0}

    s, d, ins = levenshtein_ops(ref_chars, hyp_chars)
    cer = (s + d + ins) / n
    return {"cer": round(cer, 4), "S": s, "D": d, "I": ins, "N": n}


def tokenize_thai_or_english(text: str) -> List[str]:
    """
    ตัดคำภาษาไทยและอังกฤษ
    หากมี pythainlp จะใช้ newmm
    หากไม่มี จะแยกตามช่องว่าง
    """
    if HAS_PYTHAINLP:
        words = pythainlp.word_tokenize(text, engine="newmm", keep_whitespace=False)
        return [w.strip() for w in words if w.strip()]
    return text.split()


def compute_wer(reference: str, hypothesis: str) -> Dict[str, Any]:
    """
    คำนวณ WER = (S + D + I) / N (ระดับคำ)
    """
    ref_words = tokenize_thai_or_english(reference)
    hyp_words = tokenize_thai_or_english(hypothesis)
    n = len(ref_words)
    if n == 0:
        return {"wer": 0.0 if len(hyp_words) == 0 else 1.0, "S": 0, "D": 0, "I": len(hyp_words), "N": 0}

    s, d, ins = levenshtein_ops(ref_words, hyp_words)
    wer = (s + d + ins) / n
    return {"wer": round(wer, 4), "S": s, "D": d, "I": ins, "N": n}


def evaluate_text_ocr(reference: str, hypothesis: str) -> Dict[str, Any]:
    """
    ประเมินข้อความทั้ง CER, WER และ Exact Match
    พร้อมวิเคราะห์ตัวอย่างตามสไลด์หน้า 15
    """
    cer_res = compute_cer(reference, hypothesis)
    wer_res = compute_wer(reference, hypothesis)
    em = (reference.strip() == hypothesis.strip())

    insight = ""
    if cer_res["cer"] < 0.05 and wer_res["wer"] > 0.15:
        insight = (
            f"CER = {cer_res['cer']*100:.1f}% ดูดีมาก แต่ WER = {wer_res['wer']*100:.1f}% สูง "
            "เนื่องจากผิดเพียงตัวอักษรเดียวแต่ทำให้คำหรือรหัสวิชาทั้งคำถือว่าผิดทั้งหมด "
            "ในการทำงานจริงเจ้าหน้าที่ต้องตามแก้ไขทั้งหน่วย จึงเจ็บปวดระดับ WER"
        )

    return {
        "reference": reference,
        "hypothesis": hypothesis,
        "exact_match": em,
        "CER": cer_res["cer"],
        "WER": wer_res["wer"],
        "char_stats": {"S": cer_res["S"], "D": cer_res["D"], "I": cer_res["I"], "N": cer_res["N"]},
        "word_stats": {"S": wer_res["S"], "D": wer_res["D"], "I": wer_res["I"], "N": wer_res["N"]},
        "insight": insight
    }
