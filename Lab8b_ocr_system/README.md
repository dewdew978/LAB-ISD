# Lab 8B: การพัฒนาระบบสกัดข้อมูลหลักสูตรสู่ฐานข้อมูลเชิงสัมพันธ์และระบบตอบคำถามด้วย Text-to-SQL (NL2SQL)
06026240 Intelligent System Development  
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง (KMITL)

---

## Luksuitpiti
67070098  ปวริศ ปัญสิงห์  DSBA  

## บทนำและวัตถุประสงค์ (Overview and Objectives)

โปรเจกต์นี้เป็นการต่อยอดจาก Lab 7B ซึ่งทำการสกัดข้อมูลแผนการศึกษาจากเล่มหลักสูตรด้วยโมเดล OCR และ Large Language Model (LLM) ใน Lab 8B ข้อมูลที่ได้จะถูกนำเข้าสู่กระบวนการจัดเก็บในฐานข้อมูลเชิงสัมพันธ์ (Relational Database) และสร้างระบบถามตอบภาษาธรรมชาติด้วยเทคนิค Text-to-SQL

### วัตถุประสงค์หลัก
1. Structured Data Modeling: ออกแบบ Schema ด้วย Pydantic เพื่อตรวจสอบความถูกต้องของข้อมูล (Data Validation) และแปลงข้อมูลเข้าสู่ฐานข้อมูล SQLite พร้อม Foreign Keys และ Constraints
2. การแก้ไขข้อจำกัดของ LLM ด้านการคำนวณ: แทนที่จะให้ LLM ทำหน้าที่คำนวณตัวเลขและนับจำนวนหน่วยกิตโดยตรง ซึ่งมักเกิดข้อผิดพลาด (Hallucination) ระบบจะส่งต่อให้ฐานข้อมูล SQL ทำการคำนวณผ่าน Database View เพื่อความถูกต้องแม่นยำ 100%
3. Data Consistency Verification: พัฒนาระบบตรวจสอบความสอดคล้องตามกฎระเบียบของหลักสูตร 7 ข้อ (CHK1 - CHK7) เพื่อค้นหาข้อผิดพลาดของข้อมูลก่อนนำไปใช้งานจริง
4. Natural Language to SQL (NL2SQL) with Security Guard: แปลงคำถามภาษาไทยเป็นคำสั่ง SQL ภายใต้ระบบรักษาความปลอดภัย Guard SQL ที่ป้องกันคำสั่งแก้ไขข้อมูล (เช่น DROP, UPDATE, DELETE) และจำกัดปริมาณข้อมูลที่ดึง
5. Automated Benchmarking: ประเมินประสิทธิภาพระบบด้วยชุดคำถามทองคำ (Golden Questions) 

---

## สถาปัตยกรรมระบบ (System Architecture)

```text
[ผลลัพธ์การสกัดจาก Lab 7B (JSON)]
              |
              v
[Pydantic Schema Validation & Repair Loop]
              |
              v
[SQLite Database Engine (curriculum.db)]
  - Tables: program, course, plan_item, prerequisite
  - Views : v_plan, v_semester_credits
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
- program: ข้อมูลหลักสูตร (รหัสหลักสูตร, ชื่อภาษาไทย/อังกฤษ, หน่วยกิตรวม, จำนวนปีการศึกษา)
- course: คำอธิบายรายวิชา (รหัสวิชา 8 หลัก, ชื่อวิชา, หน่วยกิต, จำนวนชั่วโมงบรรยาย/ปฏิบัติ/ศึกษาด้วยตนเอง)
- plan_item: แผนการลงทะเบียนเรียนรายภาคการศึกษา (ชั้นปี, ภาคเรียน, รหัสวิชา, หน่วยกิต, alt_group, หมายเหตุ)
- prerequisite: ความสัมพันธ์เงื่อนไขรายวิชา (รหัสวิชา, วิชาบังคับก่อนหรือเรียนควบ, ชนิดความสัมพันธ์ pre/co)

### 2. มุมมองฐานข้อมูล (Database Views)
- v_plan: รวมข้อมูลรายวิชาในแผนเข้ากับชื่อวิชาจากตาราง course เพื่อลดความซับซ้อนในการ JOIN ของ LLM
- v_semester_credits: คำนวณผลรวมหน่วยกิตและจำนวนวิชาต่อภาคเรียน โดยใช้กลไก alt_group เพื่อป้องกันการนับซ้ำของวิชาเลือกประเภทอย่างใดอย่างหนึ่ง

---

## การตรวจสอบความสอดคล้อง 7 ข้อ (Data Consistency Verification)

ระบบตรวจสอบความถูกต้องของข้อมูลในฐานข้อมูลผ่านกฎ 7 ข้อ:

| รหัส | กฎการตรวจสอบ | ผลลัพธ์ | รายละเอียดทางเทคนิค |
|:---:|:---|:---:|:---|
| CHK1 | หน่วยกิตรวมของแผนเท่ากับที่ประกาศไว้ | ไม่ผ่าน | แผนรายเทอมรวมได้ 108 หน่วยกิต จากที่ประกาศไว้ 135 หน่วยกิต เนื่องจากวิชาเลือกเสรีและวิชาหมวดยืดหยุ่นไม่ได้ระบุลงในเทอมตายตัว |
| CHK2 | ทุกรหัสวิชาในแผนมีคำอธิบายรายวิชา | ผ่าน | ข้อมูลรหัสวิชาในแผนมีคำอธิบายครบถ้วนทุกรายการ |
| CHK3 | รูปแบบรหัสวิชาเป็นตัวเลข 8 หลัก | ผ่าน | ถูกต้องตามมาตรฐานของ สจล. ทุกรายการ |
| CHK4 | หน่วยกิตในแผนตรงกับคำอธิบายรายวิชา | ผ่าน | จำนวนหน่วยกิตตรงกันทุกวิชา |
| CHK5 | วิชาบังคับก่อนอยู่ภาคเรียนก่อนวิชาหลัก | ผ่าน | ลำดับภาคเรียนของวิชา Prerequisite ถูกต้องทุกคู่ |
| CHK6 | ไม่มีวิชาซ้ำในภาคเรียนเดียวกัน | ผ่าน | ไม่มีรายการวิชาซ้ำซ้อนในเทอมเดียวกัน |
| CHK7 | ภาระหน่วยกิตต่อภาคเรียนอยู่ระหว่าง 9-22 | ไม่ผ่าน | ภาคเรียนปี 4/1 มี 3 หน่วยกิต เนื่องจากเป็นเทอมที่มีเฉพาะวิชาโครงงาน 2 |

---

## การประเมินผลด้วยชุดคำถามทองคำ (Golden Questions Evaluation)

ชุดคำถามที่ใช้ในการวัดผลถูกสร้างขึ้นโดยอ้างอิงจากเอกสาร luksuitpiti_Project_Proposal_2_Curriculum_QA.pdf หัวข้อที่ 5 (หน้า 3-8) โดยแบ่งความยากออกเป็น 3 ระดับ รวมทั้งสิ้น 45 ข้อ

### สรุปผลการทดสอบ

| รายการประเมิน | จำนวนข้อ | ผ่าน | อัตราความสำเร็จ |
|:---|:---:|:---:|:---:|
| ระดับง่าย (Easy) - ข้อเท็จจริงและคุณลักษณะรายวิชา | 18 | 18 | 100% |
| ระดับกลาง (Medium) - ความสัมพันธ์ Prerequisite และแผนการเรียน | 14 | 14 | 100% |
| ระดับยาก (Hard) - ห่วงโซ่วิชาต่อเนื่องและการปฏิเสธคำถาม | 13 | 13 | 100% |
| ภาพรวมการสร้าง SQL (SQL Execution Rate) | 45 | 45 | 100% |
| ภาพรวมความถูกต้องของคำตอบ (Answer Accuracy) | 45 | 45 | 100% |

### ตัวอย่างคำถามทดสอบตามระดับความยาก

#### 1. ระดับง่าย (Easy)
- หลักสูตรนี้มีทั้งหมดกี่หน่วยกิต -> 135 หน่วยกิต
- หลักสูตรนี้ใช้เวลาเรียนกี่ปี -> 4 ปี
- วิชา 06026200 มีกี่หน่วยกิต -> 3 หน่วยกิต
- วิชา 06026200 เรียนชั้นปีที่เท่าไร -> ปี 1
- วิชา 90644007 เรียนภาคการศึกษาใด -> ภาคการศึกษาที่ 1
- ปี 1 เทอม 1 เรียนกี่หน่วยกิต -> 21 หน่วยกิต

#### 2. ระดับกลาง (Medium)
- ต้องเรียนวิชาอะไรมาก่อนจึงจะลงเรียน 06026212 ได้ -> 06066300 (DATABASE SYSTEM CONCEPTS)
- วิชา 06066300 เรียนชั้นปีที่เท่าไร -> ปี 2
- วิชาไหนบ้างที่ต้องเรียน 06066300 มาก่อน -> 06026212 (DATA WAREHOUSING) และ 06026213 (BIG DATA SYSTEMS)
- ต้องเรียนวิชาอะไรมาก่อนจึงจะลงเรียน 06026215 ได้ -> 06026214 (โครงงาน 1)

#### 3. ระดับยาก (Hard)
- ต้องเรียนวิชาอะไรมาก่อนจึงจะลงเรียน 06026201 ได้ -> 06026200 (CALCULUS 1)
- วิชาไหนบ้างที่ต้องเรียน 06026200 มาก่อน -> 06026201 (CALCULUS 2)
- ต้องเรียนวิชาอะไรมาก่อนจึงจะลงเรียน 06066102 ได้ -> 06066101 (BUSINESS FUNDAMENTALS)
- วิชา 06026999 ชื่ออะไร -> ไม่พบข้อมูลนี้ในเล่มหลักสูตร (Negative Test)

---

## โครงสร้างโฟลเดอร์ (Directory Structure)

```text
Lab8b_ocr_system/
├── README.md                          # เอกสารคำอธิบายโปรเจกต์ Lab 8B
├── run_lab8b.py                       # สคริปต์หลักสำหรับรันกระบวนการทั้งหมด
├── lab7_metrics.py                    # โมดูลคำนวณ CER / WER สำหรับ Lab 7B
├── data/
│   ├── ground_truth_C/
│   │   └── DSBA_academic_plan_coop.json # ข้อมูลเฉลยแผนการศึกษาหลักสูตร DSBA
│   └── input_C/                       # ไฟล์ภาพตัวอย่างสำหรับทดสอบสกัด
├── src/
│   └── ocr_system/
│       ├── lab7b_curriculum.py        # สคริปต์สกัดข้อมูลเอกสาร (Lab 7B Pipeline)
│       ├── lab8b_curriculum_db.py     # สคริปต์จัดการฐานข้อมูลและ Text-to-SQL
│       └── schemas.py                 # Data classes สำหรับผลลัพธ์ OCR
└── work/
    ├── lab7b_run/
    │   ├── pred_vlm.json              # ผลการสกัดข้อมูลหลักสูตรฉบับสมบูรณ์
    │   └── gold_questions_gt.json     # ชุดคำถามทองคำสำรอง
    └── lab8b_run/
        ├── curriculum.db              # ฐานข้อมูล SQLite ที่พร้อมใช้งาน
        ├── curriculum.json            # ข้อมูลหลักสูตรในรูปแบบ JSON ตาม Schema
        ├── curriculum.conversion.json # รายงานการแปลงข้อมูลจาก Lab 7B
        ├── schema/
        │   ├── curriculum.schema.json # JSON Schema (Pydantic Model Dump)
        │   └── schema.sql             # คำสั่ง SQL DDL และ Views
        ├── verify.json                # ผลการตรวจสอบความสอดคล้อง 7 ข้อ
        ├── gold_questions.json        # ชุดคำถามทดสอบทองคำ 45 ข้อ
        └── eval_result.json           # ผลการประเมินความแม่นยำ Text-to-SQL
```

---

## การติดตั้งและการใช้งาน (Installation and Usage)

### 1. ความต้องการของระบบ (Prerequisites)
- Python: เวอร์ชัน 3.10 ขึ้นไป
- Ollama: ติดตั้งและเปิด service บนเครื่องตัวเองที่พอร์ต 11434
- ดาวน์โหลดโมเดล LLM ใน Ollama:
  ```bash
  ollama pull qwen3:4b
  ollama pull scb10x/typhoon-ocr1.5-3b
  ```
- ติดตั้งแพ็กเกจ Python ที่จำเป็น:
  ```bash
  pip install pydantic requests pymupdf pdfplumber pythainlp tabulate tqdm
  ```

### 2. คำสั่งตรวจสอบสภาพแวดล้อม
```bash
python3 src/ocr_system/lab8b_curriculum_db.py check
```

### 3. คำสั่งรัน Selftest (ตรวจสอบ Schema, กฎตรวจ และ Guard SQL)
```bash
python3 src/ocr_system/lab8b_curriculum_db.py selftest
```

### 4. การรันกระบวนการทั้งหมดแบบอัตโนมัติ
เข้าไปที่โฟลเดอร์ Lab8b_ocr_system แล้วรันสคริปต์:
```bash
cd Lab8b_ocr_system
python3 run_lab8b.py --skip-lab7
```

### 5. การทดสอบถามคำถามรายข้อ (Ad-hoc Query)
```bash
python3 src/ocr_system/lab8b_curriculum_db.py ask \
  -d work/lab8b_run/curriculum.db \
  -q "ปี 1 เทอม 1 เรียนกี่หน่วยกิต"
```

### 6. การรันประเมินผลด้วยชุดคำถามทองคำ
```bash
python3 src/ocr_system/lab8b_curriculum_db.py eval \
  -d work/lab8b_run/curriculum.db \
  -q work/lab8b_run/gold_questions.json \
  -o work/lab8b_run/eval_result.json
```
