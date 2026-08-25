# Lab 7B: การสกัดข้อมูลแผนการศึกษาจากเล่มหลักสูตรด้วย Local LLM & VLM Pipeline
**วิชา 06026240 การพัฒนาระบบอัจฉริยะ (Intelligent System Development)**  
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง (KMITL)

---

## 👥 สมาชิกกลุ่ม (Group Members) — Luksuitpiti (ลูกศิษย์ปิติ)

| ลำดับ | รหัสนักศึกษา | ชื่อ - นามสกุล | สาขาวิชา |
|:---:|:---:|:---|:---:|
| 1 | **67070098** | ภาวริศ พันธ์สิงห์ (Pawarit Pansing) | DSBA |
| 2 | **67070141** | ภวัต วรวิทยานลิน (Phawat Worawittyanalin) | DSBA |
| 3 | **67070190** | วรเมธ กลิ่นลือชา (Worameth Klinluecha) | DSBA |
| 4 | **67070307** | ศุภณัฐ ฉ่ำชื่น (Suphanat Chamchuen) | DSBA |

---

## 🎯 วัตถุประสงค์ของโปรเจกต์ (Project Objectives)

1. **สกัดข้อมูลโครงสร้างแผนการศึกษา (Structured Information Extraction)** จากเอกสารเล่มหลักสูตร (PDF) เช่น รหัสวิชา, ชื่อวิชา (ภาษาไทย/อังกฤษ), จำนวนหน่วยกิต, หมวดวิชา, ชั้นปี/ภาคการศึกษา และเงื่อนไขรายวิชา
2. **พัฒนาระบบแบบ Local & Offline 100%** ผ่านการเชื่อมต่อกับ [Ollama](https://ollama.com/) เพื่อความเป็นส่วนตัวของข้อมูล ความสามารถในการทำซ้ำ (Reproducibility) และประหยัดค่าใช้จ่าย
3. **เปรียบเทียบประสิทธิภาพของ Pipeline 2 รูปแบบ**:
   - **Text Pipeline**: ดึงข้อความดิจิทัลจาก PDF โดยตรง แล้วส่งเข้า Text LLM เพื่อจัดโครงสร้างเป็น JSON
   - **VLM Pipeline**: แปลงหน้าเอกสารเป็นรูปภาพ -> ใช้ Vision-Language Model (OCR) แปลงเป็น Markdown -> ส่งเข้า Text LLM จัดโครงสร้าง
4. **วัดผลความแม่นยำอย่างเป็นระบบ (Benchmarking & Evaluation)**: ใช้ตัวชี้วัด CER (Character Error Rate), WER (Word Error Rate) ร่วมกับ PyThaiNLP Tokenizer และ Exact Match Accuracy โดยใช้โมดูลวัดผลกลาง `lab7_metrics.py`

---

## 📂 โครงสร้างโฟลเดอร์และไฟล์ (Project Structure)

```text
lab7_final/
├── README.md                           # เอกสารคำอธิบายโปรเจกต์และการใช้งาน
├── lab7_metrics.py                     # โมดูลคำนวณ CER / WER / Alignment สำหรับวัดผลมาตรฐาน
└── groupB_curriculum/
    ├── README.md                       # เอกสารคำอธิบายของ Lab 7B
    ├── lab7b_curriculum.py             # สคริปต์หลักสำหรับรันกระบวนการสกัดข้อมูลและประเมินผล
    ├── data/
    │   └── DSBA_curriculum.pdf         # เอกสารเล่มหลักสูตรฉบับเต็ม (Input PDF)
    ├── gt/
    │   └── DSBA_academic_plan_coop.json # ข้อมูลเฉลยแผนการศึกษาหลักสูตร DSBA (Ground Truth)
    └── output/                         # ผลลัพธ์จากการรันและประเมินผล
        ├── pred_text.json              # แผนการศึกษาที่สกัดได้จาก Text Pipeline
        ├── pred_vlm.json               # แผนการศึกษาที่สกัดได้จาก VLM Pipeline
        ├── intermediate_vlm.md         # ข้อความ Markdown ดิบที่ได้จากขั้นตอน VLM OCR
        ├── comparison.csv              # ตารางเปรียบเทียบผลการวัดผลของแต่ละ Attribute
        └── evaluation.json             # ผลการประเมินความแม่นยำฉบับละเอียด (Error breakdown)
```

---

## ⚙️ สถาปัตยกรรมและ Pipelines การทำงาน

```text
[ เอกสารหลักสูตร PDF ]
        │
        ├──► (1) Text Pipeline:  [ PDF Text Extraction ] ──► [ Prompt + Text LLM (qwen3:4b) ] ──► [ pred_text.json ]
        │
        └──► (2) VLM Pipeline:   [ Render PDF Page Image ] ──► [ VLM (typhoon-ocr1.5-3b) ] 
                                                                         │
                                                                   [ intermediate_vlm.md ]
                                                                         │
                                                                   [ Text LLM (qwen3:4b) ] ──► [ pred_vlm.json ]
                                                                         │
                                 ┌───────────────────────────────────────┴─────────────────────────┐
                                 ▼                                                                 ▼
                    [ Evaluation & Metrics ] ◄── [ Ground Truth (DSBA_academic_plan_coop.json) ] ──┘
                                 │
                    ├── comparison.csv
                    └── evaluation.json
```

1. **Text Pipeline (`--pipeline text`)**:
   - อาศัยข้อความที่ฝังอยู่ในไฟล์ Digital PDF โดยตรง
   - แบ่งข้อความเป็นส่วน (Chunk) ตามจำนวนหน้าที่กำหนด
   - ส่งข้อความพร้อม Prompt ควบคุม Strict JSON Schema ไปยัง Text LLM
   - รวดเร็วและมีความแม่นยำสูงเมื่อเอกสารต้นทางมี Text Layer สมบูรณ์
2. **VLM Pipeline (`--pipeline vlm`)**:
   - เรนเดอร์หน้า PDF ให้เป็นรูปภาพความละเอียดสูง
   - ใช้โมเดล Vision-Language Model (`scb10x/typhoon-ocr1.5-3b`) ในการทำ Document OCR ออกมาเป็น Markdown Table
   - ส่ง Markdown Table ให้ Text LLM (`qwen3:4b`) แปลงเป็น JSON โครงสร้างตามที่ต้องการ

---

## 🛠️ ความต้องการของระบบและการติดตั้ง (Prerequisites & Setup)

### 1. เครื่องมือและไลบรารีที่จำเป็น
- **Python**: 3.10 ขึ้นไป
- **Ollama**: ติดตั้งจาก [ollama.com](https://ollama.com) และเปิด service ไว้ที่พอร์ต `11434`
- ติดตั้ง Python Packages ที่ต้องใช้:
  ```bash
  pip install pythainlp pypdf pdfplumber pymupdf requests tqdm tabulate
  ```

### 2. ดาวน์โหลดโมเดล Local LLM ใน Ollama
```bash
# โมเดล Vision-Language สำหรับ OCR ภาษาไทย/อังกฤษ
ollama pull scb10x/typhoon-ocr1.5-3b

# โมเดล Text สำหรับดึงและแปลงโครงสร้าง JSON
ollama pull qwen3:4b
```

---

## 🚀 วิธีการใช้งานและคำสั่งรัน (Usage)

เข้าไปที่โฟลเดอร์ `groupB_curriculum`:
```bash
cd lab7_final/groupB_curriculum
```

### 1. ตรวจสอบความพร้อมของสภาพแวดล้อมและโมเดล
```bash
python3 lab7b_curriculum.py --check
```

### 2. รันสกัดข้อมูลด้วย Text Pipeline
```bash
python3 lab7b_curriculum.py     --input data/DSBA_curriculum.pdf     --gt gt/DSBA_academic_plan_coop.json     --pipeline text     --out output/
```

### 3. รันสกัดข้อมูลด้วย VLM Pipeline
```bash
python3 lab7b_curriculum.py     --input data/DSBA_curriculum.pdf     --gt gt/DSBA_academic_plan_coop.json     --pipeline vlm     --out output/
```

### 4. รันทุก Pipeline พร้อมประเมินผลเปรียบเทียบ
```bash
python3 lab7b_curriculum.py     --input data/DSBA_curriculum.pdf     --gt gt/DSBA_academic_plan_coop.json     --pipeline all     --out output/
```

> **เคล็ดลับ (Tip)**: สามารถระบุเฉพาะหน้าที่เป็นตารางแผนการศึกษาเพื่อประหยัดเวลาการประมวลผลได้ เช่น:
> ```bash
> python3 lab7b_curriculum.py -i data/DSBA_curriculum.pdf --pages 42-58 -g gt/DSBA_academic_plan_coop.json --pipeline all
> ```

---

## 📊 สรุปผลการประเมินประสิทธิภาพ (Evaluation Results)

ผลการทดสอบเปรียบเทียบระหว่าง **Text Pipeline** และ **VLM Pipeline** (อ้างอิงจาก `output/comparison.csv`):

| Pipeline | แอตทริบิวต์ (Attribute) | จำนวนรายการ (Items) | CER ↓ | WER ↓ | Exact Match Acc ↑ | ขาด (Missing) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Text** | **รหัสวิชา** | 90 | **0.6393** | - | **36.67%** | 57 |
| **Text** | **ชื่อวิชา (ภาษาไทย) ⭐** | 90 | **0.7163** | **0.7473** | **30.00%** | 57 |
| **Text** | **หน่วยกิต** | 90 | **0.6679** | - | **36.67%** | 57 |
| **Text** | **ปี/ภาคการศึกษา** | 90 | **0.6333** | - | **36.67%** | 57 |
| **Text** | **วิชาบังคับก่อน** | 33 | **0.2222** | - | **84.85%** | 0 |
| **Text** | **ปี/ภาคยืดหยุ่น** | 33 | **0.0000** | - | **100.00%** | 0 |
| *VLM* | *รหัสวิชา* | 90 | 0.9126 | - | 8.89% | 82 |
| *VLM* | *ชื่อวิชา (ภาษาไทย) ⭐* | 90 | 0.9364 | 0.9460 | 6.67% | 82 |
| *VLM* | *หน่วยกิต* | 90 | 0.9326 | - | 7.78% | 83 |
| *VLM* | *ปี/ภาคการศึกษา* | 90 | 0.9111 | - | 8.89% | 82 |
| *VLM* | *หมวดวิชา* | 90 | 1.0000 | - | 0.00% | 90 |

---

## 🔍 การวิเคราะห์และข้อสังเกต (Observations & Discussion)

1. **Text Pipeline มีประสิทธิภาพเหนือกว่าอย่างมีนัยสำคัญ**:
   - เมื่อเอกสารหลักสูตรเป็น Digital PDF ที่มีข้อความฝังอยู่ การดึงข้อความโดยตรงส่งผลให้ Text LLM สามารถทำความเข้าใจและแปลงเป็น JSON ได้ถูกต้องและรวดเร็วกว่ามาก
   - ค่าความถูกต้องของวิชาบังคับก่อน (Prerequisite) และปี/ภาคยืดหยุ่นสูงถึง **84.85% - 100%**
2. **ปัญหาและข้อจำกัดของ VLM Pipeline**:
   - **OCR Error & Hallucination**: ในกรณีที่ตารางในหน้า PDF มีความซับซ้อน โมเดล OCR (`scb10x/typhoon-ocr1.5-3b`) อาจเกิดการติด Loop โค้ด LaTeX (เช่น `\usetikzlibrary`) ทำให้ผลลัพธ์ข้อความดิบ (`intermediate_vlm.md`) สูญหาย
   - ส่งผลให้ขั้นตอน Text LLM ถัดไปเกิดอาการ Hallucination พยายามเดารหัสวิชาและข้อมูลขึ้นมาเอง
3. **แนวทางการปรับปรุง**:
   - ควรกำหนดสโคปของหน้าเอกสาร (`--pages`) ให้เจาะจงเฉพาะหน้าตารางแผนการศึกษาเพื่อลดภาระของ Context Length
   - ปรับ Prompt แบบ Few-shot และบังคับห้ามคาดเดาข้อมูลที่ไม่ปรากฏในข้อความต้นทาง
