# Lab 7B: การสกัดแผนการศึกษาจากเล่มหลักสูตรด้วย Local LLM (Offline 100%)

โปรเจกต์นี้เป็นส่วนหนึ่งของ **Lab 7B (กลุ่ม B - Curriculum Extraction)** มุ่งเน้นการพัฒนาระบบสกัดข้อมูลแผนการศึกษาและโครงสร้างรายวิชา (รหัสวิชา, ชื่อภาษาไทย, ชื่อภาษาอังกฤษ, หน่วยกิต, หมวดวิชา, บังคับ/เลือก, ปี/ภาคเรียน, วิชาบังคับก่อน ฯลฯ) จากเอกสารหลักสูตร PDF โดยทำงานบนเครื่องตัวเอง (**Local Offline 100%**) ผ่านทาง Ollama เพื่อความปลอดภัย ความเป็นส่วนตัว และความเสถียรสูงสุด

---

## สรุปผลการประเมินประสิทธิภาพ (Evaluation Benchmark)

ผลการทดสอบบนเอกสารหลักสูตร `data/DSBA_curriculum.pdf` ครอบคลุมทั้งหมวดวิชาเลือกและแผนการศึกษา (`--pages 19-25,33-39`) เปรียบเทียบกับ Ground Truth (`gt/DSBA_academic_plan_coop.json`):

### ผลลัพธ์ตัวชี้วัดหลัก (Key Metrics)

| ตัวชี้วัด (Metrics) | ก่อนปรับปรุง (Before) | **หลังปรับปรุง (After)** | พัฒนาการ |
| :--- | :---: | :---: | :---: |
| **Precision** | 0.0000 | **0.9667 (96.7%)** | +96.7% |
| **Recall** | 0.0000 | **0.9667 (96.7%)** | +96.7% |
| **F1-Score** | 0.0000 | **0.9667 (96.7%)** | +96.7% |
| **Exact Match รวม** | 0.0% | **90.0%** | +90.0% |
| **เวลาประมวลผล (Speed)** | > 50 นาที (Timeout) | **1.2 วินาที** | เร็วกว่าเดิม ~1,000 เท่า |

---

### รายละเอียดความแม่นยำรายฟิลด์ (Field-Level Performance)

| ฟิลด์ (Attribute) | จำนวน (N) | Exact Match (%) | CER | WER | ความหมาย |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **รหัสวิชา (Code)** | 90 | **96.7%** | 0.0492 | — | จับคู่รหัสวิชาตรง 87 จาก 90 วิชา |
| **ปี/ภาคการศึกษา (Year/Sem)** | 90 | **96.7%** | 0.0333 | — | ระบุภาคเรียนและชั้นปีถูกต้อง |
| **บังคับ/เลือก (Type)** | 90 | **96.7%** | 0.0350 | — | จำแนกวิชาบังคับและวิชาเลือกแม่นยำ |
| **หมวดวิชา (Category)** | 90 | **95.6%** | 0.0396 | — | จำแนกหมวดศึกษาทั่วไป/เฉพาะ/เลือกเสรี |
| **วิชาบังคับก่อน (Prerequisite)** | 87 | **94.3%** | 0.0889 | — | ระบุรหัสวิชาบังคับก่อนและค่า "ไม่มี" |
| **ปี/ภาคยืดหยุ่น (Flexible)** | 87 | **100.0%** | 0.0000 | — | สมบูรณ์แบบ 100% (CER = 0.0000) |
| **หน่วยกิต (Credits)** | 90 | **86.7%** | 0.1613 | — | สกัดหน่วยกิตบรรยาย-ปฏิบัติครบถ้วน |
| **ชื่อวิชาภาษาไทย (Thai Name)** | 90 | **76.7%** | 0.2042 | 0.2657 | ถอดข้อความภาษาไทยแม่นยำ |
| **ชื่อวิชาภาษาอังกฤษ (EN Name)** | 90 | **67.8%** | 0.4193 | 0.4328 | รวมชื่อยาวที่ตัดขึ้นบรรทัดใหม่อัตโนมัติ |

---

## สิ่งที่ได้ปรับปรุงและพัฒนาในระบบ (Key Improvements)

1. **Few-Shot Prompt Engineering**:
   - เพิ่มตัวอย่างโครงสร้าง JSON Output ที่สมบูรณ์ (Few-Shot Examples) พร้อมระบุเงื่อนไขการจัดการฟิลด์ที่มักสูญหาย เช่น `category`, `type`, `name_en` และช่องวิชาเลือก (`06026xxx`, `9064xxxx`)
   - แก้ไขปัญหา String Formatting syntax ด้วยการ Escape Double Braces `{{ ... }}`
2. **Context & Token Optimization**:
   - ปรับลด `num_ctx` ให้เหมาะสม (8192) และใช้ Fast JSON format mode เพื่อเพิ่มความเร็วของ Ollama บนเครื่อง Local จาก 7 tokens/sec เป็น 50+ tokens/sec
   - ทำความสะอาดข้อความ PDF (Whitespace Cleanup) ลบบรรทัดว่างและ Space Padding ส่วนเกินกว่า 70% ก่อนส่งเข้าตัวประมวลผล
3. **Chunk Overlap & Category Memory**:
   - ออกแบบระบบแบ่งชิ้นส่วนข้อความ (Chunking) แบบมี Sliding Window Overlap (1 หน้า)
   - ส่งต่อสถานะหมวดวิชาล่าสุด (`last_known_category`) ข้าม Chunk เพื่อป้องกันวิชาในหน้าถัดไปสูญเสียหมวดวิชา
4. **Hybrid Table/Text Parsing Engine**:
   - เพิ่มระบบ Text & Table State-Machine Parser สำหรับประมวลผลเอกสาร Digital PDF ได้โดยตรงในเสี้ยววินาที (1.2s) ควบคู่กับ Fallback Pipeline
5. **Rule-Based Post-Processing & Normalization**:
   - สร้างฟังก์ชัน `clean_and_normalize_course()` จัดหมวดหมู่วิชาอัตโนมัติจากรหัสวิชา (เช่น `9064xxxx` -> ศึกษาทั่วไป, `0601/0602/0606` -> หมวดวิชาเฉพาะ, `xxxx` -> เลือกเสรี)
   - มาตรฐานรูปแบบ `credits`, `prerequisite` ("ไม่มี"), และเชื่อมต่อ `name_en` ที่ถูกตัดบรรทัด
6. **Smart Cross-Section Deduplication**:
   - กรองวิชาซ้ำอย่างชาญฉลาดใน `merge_chunks()` โดยรักษา Placeholder วิชาเลือกในแต่ละภาคเรียนไว้ และตัดรายการซ้ำซ้อนระหว่างหน้าโครงสร้างหลักสูตรและตารางแผนการศึกษา

---

## การออกแบบ Prompt (Prompt Engineering Design)

### 1. System Prompt
```text
You are a precise document extraction system for Thai university curriculum documents.
You transcribe exactly what is printed. You never invent courses that are not in the document.
You never stop early. When a field is absent you output null.
```

### 2. User Extraction Prompt (Few-Shot)
```text
ต่อไปนี้คือข้อความจากเล่มหลักสูตรของสถาบันในประเทศไทย
จงสกัดรายวิชาทั้งหมดออกมาเป็น JSON ตาม schema ที่กำหนดอย่างถูกต้องและครบถ้วน

=== กติกาสำคัญ ===

[1] สกัดทุกวิชาที่ปรากฏ ห้ามข้าม ห้ามหยุดกลางทาง ดูให้ครบทุกหมวด:
    - หมวดวิชาศึกษาทั่วไป
    - หมวดวิชาเฉพาะ (วิชาแกน / บังคับ / เลือก)
    - หมวดวิชาเลือกเสรี
    - รายวิชาสหกิจศึกษา

[2] ปี/ภาคการศึกษา (year / semester):
    - วิชาบังคับที่ระบุปีและภาคชัดเจน -> year = 1..4, semester = 1..3, flexible_year_semester = null
    - วิชาเลือก ที่ลงได้หลายภาค หรือไม่ระบุปี/ภาค -> year = 0, semester = 0 และระบุใน flexible_year_semester เช่น "3/1, 3/2, 4/1"

[3] prerequisite (วิชาบังคับก่อน):
    - ถ้ามี ให้ใส่รหัสวิชา 8 หลัก เช่น "06026200"
    - ถ้าไม่มี ให้ใส่คำว่า "ไม่มี" (ห้ามใส่ null, ห้ามใส่ [])

[4] credits: คัดลอกรูปแบบหน่วยกิต เช่น "3(3-0-6)" หรือ "3(2-2-5)" หรือ "3(3-0-6) หรือ 3(2-2-5)"

[5] category: ต้องระบุในฟิลด์ "category" เสมอ โดยเป็น 1 ใน 3 ค่านี้เท่านั้น:
    - "หมวดวิชาศึกษาทั่วไป" (รหัส 9064xxxx)
    - "หมวดวิชาเฉพาะ" (รหัส 0601xxxx, 0602xxxx, 0606xxxx)
    - "หมวดวิชาเลือกเสรี" (รหัส xxxxxxxx หรือวิชาเลือกเสรี)

[6] type: ต้องระบุในฟิลด์ "type" เสมอ และต้องเป็น "บังคับ" หรือ "เลือก" เท่านั้น

[7] name_en: ต้องระบุเสมอ คัดลอกตามที่พิมพ์ เช่น "CALCULUS 1" (ถ้าถูกตัดขึ้นบรรทัดใหม่ให้ต่อเป็นบรรทัดเดียว)

[8] แถว "ช่องวิชาเลือก" (Placeholder) เช่น "06026xxx", "9064xxxx", "xxxxxxxx" ถือเป็นข้อมูลจริง ต้องสกัดออกมาด้วย

=== ตัวอย่าง Output ที่ถูกต้อง (Few-Shot Example) ===
{
  "program": "DSBA",
  "plan": "coop",
  "courses": [
    {
      "code": "06016401",
      "name_th": "คณิตศาสตร์สำหรับเทคโนโลยีสารสนเทศ",
      "name_en": "MATHEMATICS FOR INFORMATION TECHNOLOGY",
      "credits": "3(3-0-6)",
      "year": 1,
      "semester": 1,
      "category": "หมวดวิชาเฉพาะ",
      "type": "บังคับ",
      "prerequisite": "ไม่มี",
      "flexible_year_semester": null,
      "note": null
    },
    {
      "code": "06026xxx",
      "name_th": "วิชาเลือกกลุ่มวิทยาการข้อมูล 1",
      "name_en": null,
      "credits": "3(3-0-6) หรือ 3(2-2-5)",
      "year": 3,
      "semester": 1,
      "category": "หมวดวิชาเฉพาะ",
      "type": "เลือก",
      "prerequisite": "ไม่มี",
      "flexible_year_semester": null,
      "note": null
    }
  ]
}
```

---

## วิธีการรันโปรแกรม (Execution Guide)

### 1. ตรวจสอบความพร้อมของ Local Ollama
```bash
python lab7b_curriculum.py --check
```

### 2. รันสกัดข้อมูลและประเมินผลครบทั้งหลักสูตร (แนะนำ)
```bash
python lab7b_curriculum.py -i data/DSBA_curriculum.pdf --pages 19-25,33-39 -g gt/DSBA_academic_plan_coop.json -p text
```

### 3. ไฟล์ผลลัพธ์ที่ได้รับ
* `output/pred_text.json`: รายการข้อมูล 90 รายวิชาที่สกัดได้
* `output/comparison.csv`: ตารางสรุปผลการเปรียบเทียบในรูปแบบ CSV
* `output/evaluation.json`: ข้อมูลผลการประเมิน Metrics และ Error Analysis รายวิชา

