# LAB-ISD: Intelligent Systems Development Repository

คลังโปรเจกต์และแบบฝึกหัดปฏิบัติการรายวิชา **การพัฒนาระบบอัจฉริยะ (Intelligent Systems Development - ISD)**  
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง (KMITL)

---

## 📂 โครงสร้างโปรเจกต์ (Repository Structure)

```text
LAB-ISD/
├── LAB2/                          # ปฏิบัติการ Lab 2: Web Scraping & Data Extraction
├── LAB5/                          # ปฏิบัติการ Lab 5: Information Extraction / Data Processing
├── LAB6/                          # ปฏิบัติการ Lab 6: Text Processing & Classification
├── groupB_curriculum 2/          # ปฏิบัติการ Lab 7B: การสกัดแผนการศึกษาด้วย Local LLM (กลุ่ม B)
├── lab7_final/                    # ปฏิบัติการ Lab 7 Final Release
└── Lab8b_ocr_system/              # ปฏิบัติการ Lab 8B: จากข้อความที่สกัดได้ สู่ฐานข้อมูลที่ตอบคำถามได้
    ├── data/                      # เอกสารหลักสูตรจริง (PDF) ภาพสแกน และ Ground Truth ทุกหลักสูตร
    │   ├── input_AIT/             # ภาพเอกสารหลักสูตร AIT
    │   ├── input_BIT/             # ภาพเอกสารหลักสูตร BIT (จาก BIT_academic.pdf)
    │   ├── input_C/               # ภาพเอกสารหลักสูตร DSBA
    │   └── input_IT/              # ภาพเอกสารหลักสูตร IT
    ├── src/                       # ซอร์สโค้ดหลักของระบบ
    │   └── ocr_system/            # Pipeline สกัดข้อมูล (Lab 7B) และ Text-to-SQL DB (Lab 8B)
    └── work/                      # ผลลัพธ์การประมวลผล ฐานข้อมูล และ Benchmark ครบ 4 หลักสูตร
```

---

## 🌟 ไฮไลต์หลักของระบบ (Key Components)

### 1. Lab 8B: Curriculum Database & Text-to-SQL System (`Lab8b_ocr_system`)
ระบบแปลงข้อมูลโครงสร้างหลักสูตรและแผนการศึกษาจากการสกัด (Lab 7B) เข้าสู่ฐานข้อมูลเชิงสัมพันธ์ **SQLite** พร้อมกลไกถาม-ตอบภาษาธรรมชาติด้วย **Local LLM (Text-to-SQL)**:
- **รองรับครบ 4 หลักสูตร**: DSBA, IT, AIT และ BIT
- **ความถูกต้องของฐานข้อมูล**: ผ่านเกณฑ์ตรวจสอบความสอดคล้อง 7 ข้อ (Consistency Checks CHK1–CHK7) ครบ 100%
- **ประสิทธิภาพการประเมิน (Benchmark Results)**:
  - **SQL Execution Rate**: 180 / 180 (100%)
  - **Answer Accuracy**: 180 / 180 (100%)
- อ่านรายละเอียดเพิ่มเติมได้ที่: [Lab8b_ocr_system/README.md](Lab8b_ocr_system/README.md)

### 2. Lab 7B: Curriculum Extraction Pipeline (`groupB_curriculum 2` & `Lab8b_ocr_system`)
ระบบสกัดข้อมูลโครงสร้างรายวิชาและแผนการศึกษาจากเอกสาร PDF และภาพสแกนจริง:
- **Precision / Recall / F1-Score**: > 0.99 ทั่วทั้ง 4 หลักสูตร
- ใช้ภาพเอกสารจริงและ Ground Truth สำหรับการตรวจสอบความถูกต้อง

---

## 🚀 วิธีการติดตั้งและเริ่มต้นใช้งาน (Getting Started)

### 1. Clone โปรเจกต์
```bash
git clone https://github.com/dewdew978/LAB-ISD.git
cd LAB-ISD
```

### 2. ติดตั้ง Dependencies สำหรับ Lab 8B / 7B
```bash
cd Lab8b_ocr_system
pip install pydantic tabulate
```

### 3. ตรวจสอบ Ollama Local LLM
ตรวจสอบให้แน่ใจว่า Ollama กำลังทำงานและมีโมเดล `qwen3:4b`:
```bash
ollama list
ollama run qwen3:4b "สวัสดี"
```

### 4. รันระบบถาม-ตอบ Text-to-SQL
```bash
# ตัวอย่าง: ถามข้อมูลหลักสูตร BIT
python src/ocr_system/lab8b_curriculum_db.py ask -d work/lab8b_run/curriculum_BIT.db -q "วิชา 06036100 มีกี่หน่วยกิต"

# ตัวอย่าง: รันการประเมินผลชุดคำถามทองคำ
python src/ocr_system/lab8b_curriculum_db.py eval -d work/lab8b_run/curriculum_BIT.db -q work/lab8b_run/gold_questions_BIT.json -o work/lab8b_run/eval_result_BIT.json
```
