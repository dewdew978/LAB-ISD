# Lab 6 — Evaluation Pipeline (Field / Page / Category Level)

สคริปต์สำหรับประเมินผล OCR + course-extraction pipeline ของ 3 โปรแกรม
(**AIT / IT / DSBA**) แบบครบ 3 ระดับ: Field Level, Page Level, Category Level

ไฟล์หลัก: **`Evaluate_all_standalone.py`**
เป็นไฟล์ **standalone ไฟล์เดียว** — รวม `extract_courses()` (เดิมจาก
`src/ocr_system/field_extraction.py`) และ `evaluate_courses()` (เดิมจาก
`src/ocr_system/evaluation.py`) เข้ามาไว้ในไฟล์เดียวกันแล้ว **ไม่ต้องมี
โฟลเดอร์ `src/ocr_system/` อีกต่อไป**

---

## 1. สิ่งที่สคริปต์ทำ

| ระดับ | อธิบาย |
|---|---|
| **1. Field Level** | เทียบ code recall + credits exact-match ของแต่ละแผนการเรียน/หมวดวิชา (ใช้ `evaluate_courses()`) |
| **2. Page Level** | เทียบเลขหน้าที่ pipeline ค้นเจอ กับเลขหน้าจริงตาม ground truth ครบทั้ง AIT / IT / DSBA (จาก `Map_page_all.csv`) |
| **3. Category Level** | สรุปผลรวมแยกตามหมวด: DSBA coop, DSBA no_coop, IT coop, IT no_coop, AIT, หมวดศึกษาทั่วไป (ต่อโปรแกรม), ข้อบังคับ |

---

## 2. ความต้องการของระบบ

- **Python 3.7 ขึ้นไป** (ใช้ `from __future__ import annotations` ในไฟล์แล้ว
  จึงรองรับ type hint แบบ `str | None` แม้ใช้ Python รุ่นเก่ากว่า 3.10)
- **ไม่ต้องติดตั้งไลบรารีเพิ่มเติมใดๆ** — ใช้แค่ standard library
  (`json`, `re`, `csv`, `pathlib`, `collections`, `dataclasses`)
  ไม่ต้องติดตั้ง `jiwer` หรือ `python-Levenshtein` เพราะสคริปต์นี้ใช้แค่
  `evaluate_courses()` ไม่ได้ใช้ path CER/WER ที่พึ่งพา 2 แพ็กเกจนั้น

ตรวจเวอร์ชัน Python ที่ใช้:

```bash
python3 --version
```

---

## 3. โครงสร้างไฟล์ที่ต้องมี

วางไฟล์ `Evaluate_all_standalone.py` ไว้ที่ root ของโปรเจกต์ ร่วมกับ
โฟลเดอร์ `data/ground_truth/` และ `outputs/` ตามนี้:

```
your_project/
├── Evaluate_all_standalone.py
├── data/
│   └── ground_truth/
│       ├── AIT/
│       │   └── AIT_academic_plan.json
│       ├── IT/
│       │   ├── IT_academic_plan_coop.json
│       │   └── IT_academic_plan_no_coop.json
│       ├── DSBA/
│       │   ├── DSBA_academic_plan_coop.json
│       │   └── DSBA_academic_plan_no_coop.json
│       ├── general_education_ground_truth.json
│       ├── rules_ground_truth.json
│       └── Map_page_all.csv
└── outputs/
    ├── fulldoc_AIT_ocr.json
    ├── fulldoc_it_ocr.json
    └── fulldoc_dsba_ocr.json
```

> ถ้าไฟล์ใดหายไป สคริปต์จะพิมพ์ `[warn] ไม่พบ <path>` แล้วข้ามส่วนนั้นไป
> (ไม่ crash) — ตรวจ log ตอนรันเพื่อดูว่ามีส่วนไหนถูกข้ามบ้าง

---

## 4. วิธีรัน

```bash
cd your_project
python3 Evaluate_all_standalone.py
```

## 5. ผลลัพธ์ (Output)

หลังรันเสร็จจะได้ไฟล์ในโฟลเดอร์ `outputs/`:

| ไฟล์ | เนื้อหา |
|---|---|
| `eval_field_level.json` | ผล code recall / credits match ของทุกแผน + ข้อบังคับ |
| `eval_page_level.csv` | ผลเทียบเลขหน้า (precision / recall / f1 / exact_match) ต่อรายวิชา/ข้อบังคับ |
| `eval_category_summary.csv` | สรุปผลรวมทุกระดับ แยกตามหมวด/โปรแกรม |

พร้อมสรุปผลพิมพ์ลง console ทั้ง 3 ระดับด้วย

---

## 6. Troubleshooting

**`TypeError: unsupported operand type(s) for | ...`**
Python เวอร์ชันเก่ากว่า 3.10 — ไฟล์นี้แก้แล้วด้วย
`from __future__ import annotations` (บรรทัดแรกๆ ของไฟล์) ถ้ายังเจอ error
เดิม ให้เช็คว่าใช้ `Evaluate_all_standalone.py` เวอร์ชันล่าสุดหรือยัง

**`[warn] ไม่พบ ...`**
ไม่ใช่ error แต่เป็นการแจ้งว่าไฟล์ ground truth หรือ OCR ที่ระบุใน
`OCR_FILES` / `COURSE_GT_FILES` / `GT_DIR` ยังไม่มีอยู่จริงตาม path
ที่คาดไว้ — ตรวจสอบโครงสร้างโฟลเดอร์ตามข้อ 3

**ผล Page Level ว่างทั้งหมด**
ตรวจว่ามีไฟล์ `data/ground_truth/Map_page_all.csv` และคอลัมน์ `program`,
`pages`, `code`, `name_th`, `source_gt` ครบตามที่สคริปต์คาดหวัง

---

รายละเอียดเต็มอยู่ใน docstring ต้นไฟล์ `Evaluate_all_standalone.py`