# Lab 8B: การพัฒนาระบบสกัดข้อมูลหลักสูตรสู่ฐานข้อมูลเชิงสัมพันธ์และระบบตอบคำถามด้วย Text-to-SQL (NL2SQL)
วิชา 06026240 การพัฒนาระบบอัจฉริยะ (Intelligent System Development)  
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง (KMITL)

---

## สมาชิกกลุ่ม (Group Members) - Luksuitpiti

| ลำดับ | รหัสนักศึกษา | ชื่อ - นามสกุล | สาขาวิชา |
|:---:|:---:|:---|:---:|
| 1 | 67070098 | ปวริศ ปัญสิงห์ | DSBA |
| 2 | 67070141 | ภูวิศ ทรายทอง | DSBA |
| 3 | 67070190 | สุวิจักขณ์ กุลฉัตลานนท์ | DSBA |
| 4 | 67070307 | ปิติ หยาง | DSBA |

---

## บทนำและวัตถุประสงค์ (Overview and Objectives)

โปรเจกต์นี้เป็นการต่อยอดจาก Lab 7B ซึ่งทำการสกัดข้อมูลแผนการศึกษาจากเล่มหลักสูตรด้วยโมเดล OCR และ Large Language Model (LLM) ใน Lab 8B ข้อมูลที่ได้จะถูกนำเข้าสู่กระบวนการจัดเก็บในฐานข้อมูลเชิงสัมพันธ์ (Relational Database) และสร้างระบบถามตอบภาษาธรรมชาติด้วยเทคนิค Text-to-SQL

ระบบรองรับและครอบคลุม **4 หลักสูตรของคณะเทคโนโลยีสารสนเทศ (KMITL)**:
1. **DSBA** (Data Science and Business Analytics - วิทยาการข้อมูลและการวิเคราะห์เชิงธุรกิจ สหกิจศึกษา) — 135 หน่วยกิต 4 ปี
2. **IT** (Information Technology - เทคโนโลยีสารสนเทศ สหกิจศึกษา) — 129 หน่วยกิต 4 ปี
3. **AIT** (Artificial Intelligence Technology - เทคโนโลยีปัญญาประดิษฐ์) — 120 หน่วยกิต 4 ปี
4. **BIT** (Business Information Technology - เทคโนโลยีสารสนเทศทางธุรกิจ สหกิจศึกษา) — 126 หน่วยกิต 4 ปี

### วัตถุประสงค์หลัก
1. **Multi-Program Structured Data Modeling**: ออกแบบ Schema ด้วย Pydantic และ SQLite รองรับการเชื่อมโยงหลายหลักสูตรในฐานข้อมูลเดียวกันผ่าน Foreign Keys (`program_id`) และ Constraints
2. **การแก้ไขข้อจำกัดของ LLM ด้านการคำนวณ**: แทนที่จะให้ LLM ทำหน้าที่คำนวณตัวเลขและนับจำนวนหน่วยกิตโดยตรง ซึ่งมักเกิดข้อผิดพลาด (Hallucination) ระบบจะส่งต่อให้ฐานข้อมูล SQL ทำการคำนวณผ่าน Database View (`v_semester_credits`, `v_plan`) เพื่อความถูกต้องแม่นยำ 100%
3. **Data Consistency Verification**: พัฒนาระบบตรวจสอบความสอดคล้องตามกฎระเบียบของหลักสูตร 7 ข้อ (CHK1 - CHK7) รองรับการตรวจสอบแยกรายหลักสูตรและภาพรวม
4. **Natural Language to SQL (NL2SQL) with Security Guard**: แปลงคำถามภาษาไทยเป็นคำสั่ง SQL ภายใต้ระบบรักษาความปลอดภัย Guard SQL ที่ป้องกันคำสั่งแก้ไขข้อมูล (เช่น DROP, UPDATE, DELETE) และจำกัดปริมาณข้อมูลที่ดึง
5. **Automated Benchmarking**: ประเมินประสิทธิภาพระบบด้วยชุดคำถามทองคำ (Golden Questions) ครอบคลุมทั้ง DSBA, IT, AIT และ BIT

---

## สถาปัตยกรรมระบบ (System Architecture)

```text
[ผลลัพธ์การสกัด / ข้อมูลหลักสูตร DSBA, IT, AIT (JSON)]
                          |
                          v
        [Pydantic Schema Validation & Repair Loop]
                          |
                          v
         [SQLite Database Engine (curriculum.db)]
           - Tables: program, course, plan_item, prerequisite
           - Views : v_plan, v_semester_credits (พร้อม program_id)
                          |
                          +---> [Consistency Verification: CHK1 - CHK7] ---> verify.json
                          |
                          v
            [Natural Language Question (ภาษาไทย)]
                          |
                          v
        [LLM (qwen3:4b via Ollama) -> Text-to-SQL Prompt]
                          |
                          v
        [Guard SQL Verification (SELECT only, Row Limit 200)]
                          |
                          v
            [Execute Query on curriculum.db]
                          |
                          v
        [SQL Results -> LLM Answer Synthesis -> Final Answer]
```

---

## โครงสร้างฐานข้อมูลและ Views (Database Schema and Views)

### 1. ตารางข้อมูลหลัก (Core Tables)
- **program**: ข้อมูลหลักสูตร (`program_id`, `name_th`, `name_en`, `degree`, `total_credits`, `years`)
- **course**: คำอธิบายรายวิชา (`code`, `name_th`, `name_en`, `credits`, `lecture_h`, `lab_h`, `self_h`, `description_th`)
- **plan_item**: แผนการลงทะเบียนเรียนรายภาคการศึกษา (`id`, `program_id`, `year`, `semester`, `code`, `credits`, `alt_group`, `note`)
- **prerequisite**: ความสัมพันธ์เงื่อนไขรายวิชา (`code`, `requires`, `kind`)

### 2. มุมมองฐานข้อมูล (Database Views)
- **v_plan**: รวมข้อมูลรายวิชาในแผนเข้ากับชื่อวิชาจากตาราง course พร้อมระบุ `program_id` เพื่อให้สามารถกรองตามหลักสูตรได้อย่างถูกต้อง
- **v_semester_credits**: คำนวณผลรวมหน่วยกิตและจำนวนวิชาต่อภาคเรียนแยกตามหลักสูตร (`program_id`, `year`, `semester`) โดยใช้กลไก `alt_group` ป้องกันการนับซ้ำของวิชาเลือก

---

## การตรวจสอบความสอดคล้อง 7 ข้อ (Data Consistency Verification)

| รหัส | กฎการตรวจสอบ | DSBA | IT | AIT | BIT | รายละเอียดและข้อยกเว้นทางเทคนิค |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| CHK1 | หน่วยกิตรวมของแผนเท่ากับที่ประกาศไว้ | ❌ | ❌ | ❌ | ❌ | แผนรายเทอมรวมไม่เท่ากับหน่วยกิตประกาศ เนื่องจากวิชาเลือกเสรีและวิชายืดหยุ่นไม่ได้ล็อกเทอมตายตัว |
| CHK2 | ทุกรหัสวิชาในแผนมีคำอธิบายรายวิชา | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | รหัสวิชาในแผนทุกรายการมีคำอธิบายรายวิชาครบถ้วน |
| CHK3 | รูปแบบรหัสวิชาเป็นตัวเลข 8 หลัก | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | รหัสวิชาถูกต้องตามมาตรฐาน สจล. 8 หลักทุกรายการ |
| CHK4 | หน่วยกิตในแผนตรงกับคำอธิบายรายวิชา | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | จำนวนหน่วยกิตตรงกันทุกวิชา |
| CHK5 | วิชาบังคับก่อนอยู่ภาคเรียนก่อนวิชาหลัก | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | ลำดับภาคเรียนของ Prerequisite ถูกต้องทุกคู่ภายในหลักสูตร |
| CHK6 | ไม่มีวิชาซ้ำในภาคเรียนเดียวกัน | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | ✔️ ผ่าน | ไม่มีรายการวิชาซ้ำซ้อนในเทอมเดียวกัน |
| CHK7 | ภาระหน่วยกิตต่อภาคเรียนอยู่ระหว่าง 9-22 | ❌ | ❌ | ❌ | ❌ | **DSBA**: ปี 4/1 มี 3 หน่วยกิต (โครงงาน 2)<br>**IT**: ปี 2/2 มี 30 หน่วยกิต (แบ่งแขนงความเชี่ยวชาญ)<br>**AIT**: ปี 3/2 มี 4 หน่วยกิต, ปี 4/1 มี 3 หน่วยกิต<br>**BIT**: ปี 4/1 มี 6 หน่วยกิต (รายวิชาเฉพาะ) |

---

## การประเมินผลด้วยชุดคำถามทองคำ (Golden Questions Evaluation)

ชุดคำถามที่ใช้ในการวัดผลมีจำนวน 60 ข้อ ครอบคลุมทั้ง DSBA, IT, AIT และ BIT (หลักสูตรละ 15 ข้อ) ประกอบด้วยคำถามระดับง่าย กลาง ยาก และคำถามเชิงปฏิเสธ (Negative Testing)

### สรุปผลการทดสอบ (Benchmark Results)

| รายการประเมิน | จำนวนข้อ | ผ่าน | อัตราความสำเร็จ |
|:---|:---:|:---:|:---:|
| หลักสูตร DSBA (ข้อเท็จจริง แผนการเรียน และ Prerequisite) | 15 | 15 | 100% |
| หลักสูตร IT (ข้อเท็จจริง แผนการเรียน และ Prerequisite) | 15 | 15 | 100% |
| หลักสูตร AIT (ข้อเท็จจริง แผนการเรียน และ Prerequisite) | 15 | 15 | 100% |
| หลักสูตร BIT (ข้อเท็จจริง แผนการเรียน และ Prerequisite) | 15 | 15 | 100% |
| **ภาพรวมการสร้าง SQL (SQL Execution Rate)** | **60** | **60** | **100%** |
| **ภาพรวมความถูกต้องของคำตอบ (Answer Accuracy)** | **60** | **60** | **100%** |

### ตัวอย่างคำถามและผลลัพธ์ Text-to-SQL
1. **ถามหน่วยกิตหลักสูตร BIT**:
   - คำถาม: `หลักสูตร BIT มีทั้งหมดกี่หน่วยกิต`
   - SQL: `SELECT total_credits FROM program WHERE program_id LIKE '%BIT%' LIMIT 1`
   - คำตอบ: `126 หน่วยกิต`
2. **ถามหน่วยกิตหลักสูตร IT**:
   - คำถาม: `หลักสูตร IT มีทั้งหมดกี่หน่วยกิต`
   - SQL: `SELECT total_credits FROM program WHERE program_id LIKE '%IT%' OR name_th LIKE '%สารสนเทศ%' LIMIT 1`
   - คำตอบ: `129 หน่วยกิต`
3. **ถามหน่วยกิตหลักสูตร AIT**:
   - คำถาม: `หลักสูตร AIT มีทั้งหมดกี่หน่วยกิต`
   - SQL: `SELECT total_credits FROM program WHERE program_id LIKE '%AIT%' OR name_th LIKE '%ปัญญาประดิษฐ์%' LIMIT 1`
   - คำตอบ: `120 หน่วยกิต`
4. **ถาม Prerequisite ของ AIT**:
   - คำถาม: `วิชา 06046401 ต้องเรียนวิชาใดมาก่อน`
   - SQL: `SELECT requires FROM prerequisite WHERE code='06046401' AND kind='pre' LIMIT 200`
   - คำตอบ: `06046400 (CALCULUS 1)`
5. **ถาม Prerequisite ของ IT**:
   - คำถาม: `วิชา 06066102 ต้องเรียนวิชาใดมาก่อน`
   - SQL: `SELECT requires FROM prerequisite WHERE code='06066102' AND kind='pre' LIMIT 200`
   - คำตอบ: `06066101`
6. **ถามชั่วโมงปฏิบัติการของวิชา BIT**:
   - คำถาม: `วิชา 06036100 มีชั่วโมงปฏิบัติการกี่ชั่วโมง`
   - SQL: `SELECT lab_h FROM course WHERE code='06036100' LIMIT 1`
   - คำตอบ: `2 ชั่วโมง`
7. **คำถามที่ไม่พบข้อมูลในหลักสูตร (Negative Testing)**:
   - คำถาม: `วิชา 06036999 ชื่ออะไร`
   - SQL: `SELECT name_th FROM course WHERE code='06036999' LIMIT 1`
   - คำตอบ: `ไม่พบข้อมูลนี้ในเล่มหลักสูตร`

---

## โครงสร้างโฟลเดอร์ (Directory Structure)

```text
Lab8b_ocr_system/
├── README.md                          # เอกสารคำอธิบายโปรเจกต์ Lab 8B
├── run_lab8b.py                       # สคริปต์รันกระบวนการทั้งหมด (รองรับ --program all|DSBA|IT|AIT|BIT)
├── lab7_metrics.py                    # โมดูลคำนวณ CER / WER สำหรับ Lab 7B
├── data/
│   ├── ground_truth/                  # ข้อมูลเฉลยหลักสูตรแยกตามโฟลเดอร์ IT, AIT, DSBA, BIT
│   │   ├── IT/IT_academic_plan_coop.json
│   │   ├── AIT/AIT_academic_plan.json
│   │   ├── DSBA/DSBA_academic_plan_coop.json
│   │   └── BIT/BIT_academic_plan_coop.json
│   ├── ground_truth_C/                # ข้อมูลเฉลยหลักสูตร (DSBA, IT, AIT, BIT)
│   ├── gold_questions_DSBA.json       # ชุดคำถามทองคำ DSBA
│   ├── gold_questions_IT.json         # ชุดคำถามทองคำ IT
│   ├── gold_questions_AIT.json        # ชุดคำถามทองคำ AIT
│   ├── gold_questions_BIT.json        # ชุดคำถามทองคำ BIT
│   └── gold_questions_combined.json   # ชุดคำถามทองคำรวม
├── src/
│   └── ocr_system/
│       ├── lab7b_curriculum.py        # สคริปต์สกัดข้อมูลเอกสาร (Lab 7B Pipeline)
│       ├── lab8b_curriculum_db.py     # สคริปต์จัดการฐานข้อมูลและ Text-to-SQL
│       └── schemas.py                 # Data classes สำหรับผลลัพธ์ OCR
└── work/
    ├── lab7b_run/
    │   └── pred_vlm.json              # ผลการสกัดข้อมูลหลักสูตร DSBA
    └── lab8b_run/
        ├── curriculum.db              # ฐานข้อมูล SQLite รวม 4 หลักสูตร (DSBA, IT, AIT, BIT)
        ├── curriculum_DSBA.db         # ฐานข้อมูลเฉพาะหลักสูตร DSBA
        ├── curriculum_IT.db           # ฐานข้อมูลเฉพาะหลักสูตร IT
        ├── curriculum_AIT.db          # ฐานข้อมูลเฉพาะหลักสูตร AIT
        ├── curriculum_BIT.db          # ฐานข้อมูลเฉพาะหลักสูตร BIT
        ├── curriculum.json            # ข้อมูลหลักสูตร JSON
        ├── curriculum_IT.json         # ข้อมูลหลักสูตร IT JSON
        ├── curriculum_AIT.json        # ข้อมูลหลักสูตร AIT JSON
        ├── curriculum_BIT.json        # ข้อมูลหลักสูตร BIT JSON
        ├── schema/
        │   ├── curriculum.schema.json # JSON Schema (Pydantic Model Dump)
        │   └── schema.sql             # คำสั่ง SQL DDL และ Views
        ├── verify.json                # ผลการตรวจสอบความสอดคล้อง 7 ข้อ (รวม 4 หลักสูตร)
        ├── verify_IT.json             # ผลการตรวจสอบความสอดคล้องหลักสูตร IT
        ├── verify_AIT.json            # ผลการตรวจสอบความสอดคล้องหลักสูตร AIT
        ├── verify_BIT.json            # ผลการตรวจสอบความสอดคล้องหลักสูตร BIT
        ├── gold_questions.json        # ชุดคำถามทดสอบทองคำ
        └── eval_result.json           # ผลการประเมินความแม่นยำ Text-to-SQL (100% Correct)
```

---

## การติดตั้งและการใช้งาน (Installation and Usage)

### 1. ความต้องการของระบบ (Prerequisites)
- Python: เวอร์ชัน 3.10 ขึ้นไป
- Ollama: ติดตั้งและเปิด service บนเครื่องตัวเองที่พอร์ต 11434 (`ollama serve`)
- โมเดล LLM:
  ```bash
  ollama pull qwen3:4b
  ```

### 2. คำสั่งตรวจสอบสภาพแวดล้อม
```bash
python3 src/ocr_system/lab8b_curriculum_db.py check
```

### 3. คำสั่งรัน Selftest (ตรวจสอบ Schema, กฎตรวจ และ Guard SQL)
```bash
python3 src/ocr_system/lab8b_curriculum_db.py selftest
```

### 4. การรันกระบวนการทั้งหมด (เลือกหลักสูตรได้)

**รันรวมทั้ง 3 หลักสูตร (DSBA, IT, AIT)**:
```bash
python3 run_lab8b.py --skip-lab7
```

**รันเฉพาะหลักสูตร IT**:
```bash
python3 run_lab8b.py --skip-lab7 --program IT
```

**รันเฉพาะหลักสูตร AIT**:
```bash
python3 run_lab8b.py --skip-lab7 --program AIT
```

**รันเฉพาะหลักสูตร DSBA**:
```bash
python3 run_lab8b.py --skip-lab7 --program DSBA
```

### 5. การทดสอบถามคำถามรายข้อ (Ad-hoc Query)
```bash
# ถามเกี่ยวกับหลักสูตร IT
python3 src/ocr_system/lab8b_curriculum_db.py ask \
  -d work/lab8b_run/curriculum.db \
  -q "หลักสูตร IT มีกี่หน่วยกิต"

# ถามเกี่ยวกับหลักสูตร AIT
python3 src/ocr_system/lab8b_curriculum_db.py ask \
  -d work/lab8b_run/curriculum.db \
  -q "หลักสูตร AIT ปี 1 เทอม 1 เรียนกี่หน่วยกิต"

# ถามเงื่อนไข Prerequisite
python3 src/ocr_system/lab8b_curriculum_db.py ask \
  -d work/lab8b_run/curriculum.db \
  -q "วิชา 06046401 ต้องเรียนวิชาใดมาก่อน"
```

### 6. การรันประเมินผลชุดคำถามทองคำ
```bash
python3 src/ocr_system/lab8b_curriculum_db.py eval \
  -d work/lab8b_run/curriculum.db \
  -q work/lab8b_run/gold_questions.json \
  -o work/lab8b_run/eval_result.json
```
