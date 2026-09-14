# Lab 9: การประเมินผลระบบและการตรวจจับ Overfitting (Evaluation & Overfitting)

> **วิชา 06026240 การพัฒนาระบบอัจฉริยะ (Intelligent System Development)**  
> ผู้สอน: ดร.ภัทราภรณ์ วัฒนชีพ  
> คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง

โปรเจกต์นี้เป็นการนำทฤษฎีและแนวปฏิบัติตาม **Chapter 9: Evaluation and Overfitting** มาสร้างเป็นระบบประเมินผล วิเคราะห์คุณภาพตัวชี้วัด และตรวจสอบ Overfitting แบบครบวงจร ทั้งในรูปแบบสาธิตทางทฤษฎี และการนำไปเชื่อมโยงประเมินระบบงานจริง (ระบบสกัดและสืบค้นหลักสูตร Lab 7B & Lab 8B)

---

## 📂 โครงสร้างโฟลเดอร์ (Project Structure)

```text
LAB9/
├── README.md                          # เอกสารคู่มือและรายงานผล Lab 9
├── run_lab9.py                        # สคริปต์หลักสำหรับสั่งประเมินผลทั้งหมด
├── silde/                             # สไลด์บทเรียนของอาจารย์
│   └── ch9_EvaluationAndOverfitting (1).pdf
├── src/                               # ซอร์สโค้ดระบบการวัดผลตามมาตรฐานบทที่ 9
│   ├── classification_metrics.py      # Confusion Matrix, P/R/F1, Specificity, MCC, Accuracy Paradox
│   ├── continuous_metrics.py          # MAE, MSE, RMSE, MAPE, Huber Loss
│   ├── ocr_metrics.py                 # Levenshtein Edit Distance, CER, WER (Thai NLP)
│   ├── llm_pipeline_metrics.py        # JSON valid, Schema pass, SQL exec, Negative testing
│   ├── overfitting_diagnostics.py     # Learning curve, Slice analysis, Seed variance, Ensemble
│   └── lab9_evaluator.py              # ตัวประสานงานประเมินผลและสร้างรายงาน
└── outputs/                           # ผลลัพธ์การประเมิน
    ├── evaluation_summary.json        # ข้อมูลสรุปตัวชี้วัดรูปแบบ JSON
    └── evaluation_report.md           # รายงานสรุปการประเมินฉบับสมบูรณ์
```

---

## 🎯 สรุปเนื้อหาและตัวชี้วัดสำคัญ (Key Metrics)

### 1. งานจำแนก (Classification) & กับดัก Accuracy Paradox
- **Confusion Matrix**: จำแนกผลเป็น $TP, FP, TN, FN$
  - $FP$ (เตือนผิด/ตีตกของดี): ก่อให้เกิด *Alarm Fatigue* ผู้ใช้ต้องสแกนใหม่
  - $FN$ (ปล่อยหลุด): ปล่อยข้อมูลผิดเข้าสู่ฐานข้อมูล
- **เลือกดูเมื่อไหร่?**:
  - **เน้น Precision**: เมื่องานเตือนผิดมีราคาสูง (เช่น ระบบตอบคำถาม ต้องไม่ตอบมั่ว)
  - **เน้น Recall**: เมื่องานปล่อยหลุดมีราคาสูง (เช่น ตรวจสอบวิชาตกหล่น)
- **Accuracy Paradox**: กรณีข้อมูลไม่สมดุล (Imbalance 99:1) โมเดลที่ทายลบทุกตัวจะได้ Accuracy 99% แต่ Recall = 0 จึงต้องใช้ **Matthews Correlation Coefficient (MCC)** ควบคู่เสมอ:
  $$\text{MCC} = \frac{TP \times TN - FP \times FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}}$$

---

### 2. งานทำนายค่าต่อเนื่อง (Regression)
- **MAE**: ค่าเฉลี่ยความคลาดเคลื่อน เข้าใจง่าย หน่วยตรงกับข้อมูลจริง
- **RMSE**: ยกกำลังสองก่อนเฉลี่ย ลงโทษจุดที่ผิดพลาดรุนแรง
- **RMSE - MAE Gap**: หาก Gap มีค่าสูง บ่งชี้ว่ามี Outlier หรือมีบางจุดที่พังหนัก
- **Huber Loss (Smooth L1)**: ใช้คุมการเทรนเมื่อมี Outlier (ชิ้นส่วนผสมระหว่าง MSE และ MAE ตามค่า $\delta$)

---

### 3. งานข้อความและ OCR (CER vs WER)
- คำนวณจาก Levenshtein Edit Distance ($S$ = แทนที่, $D$ = ลบ, $I$ = แทรก):
  $$\text{CER / WER} = \frac{S + D + I}{N}$$
- **CER**: ระดับตัวอักษร
- **WER**: ระดับคำ (ตัดคำภาษาไทยด้วย `pythainlp` newmm)
- **Insight**: แม้ CER จะต่ำมาก (เช่น 2.6%) แต่ WER อาจสูงถึง 33.3% เพราะการผิดเพียงตัวอักษรเดียวทำให้เสียทั้งคำ ในระบบงานจริงเจ้าหน้าที่ต้องตามแก้ไขทั้งหน่วย จึงเจ็บปวดระดับ WER

---

### 4. งาน LLM Pipeline และ Text-to-SQL (ประเมินโปรเจกต์จริง ⭐)
วัดคุณภาพทีละขั้นตอนตามหลักสไลด์หน้า 17–19:
1. **Valid SQL Rate**: โมเดลเขียนไวยากรณ์ SQL รันผ่านโดยไม่มี Syntax error
2. **Execution Accuracy**: รัน SQL บนฐานข้อมูลจริงแล้ว ผลลัพธ์ตรงกับคำตอบมาตรฐาน
3. **Abstain Rate (Negative Testing)**: ความสามารถในการตอบว่า *"ไม่พบข้อมูลนี้ในเล่มหลักสูตร"* เมื่อถามวิชาหรือเงื่อนไขที่ไม่มีจริง

---

### 5. การตรวจจับและรักษา Overfitting (อย่าแก้ผิดโรค)
- **นิยาม**: Overfitting คือการจำข้อสอบเก่าแทนที่จะเป็นการเรียนรู้
- **Learning Curve**: ตรวจสอบจุดที่ Validation Loss เริ่มดีดตัวสูงขึ้นขณะที่ Train Loss ยังคงลดลงอย่างต่อเนื่อง
- **แนวทางรักษาเรียงตามลำดับ**:
  1. เพิ่มข้อมูลจริง (Data Collection)
  2. Data Augmentation
  3. Early Stopping (หยุดที่ Best Epoch)
  4. Transfer Learning / Dropout / Regularization
  5. Ensemble (Voting, Bagging, Boosting, Stacking)
- **⚠️ ข้อควรระวัง**: ยารักษา Overfitting จะทำให้ Underfitting แย่ลง ห้ามจ่ายยาผิดโรค

---

## 🏆 ผลลัพธ์การประเมินโปรเจกต์จริง (Multi-Curriculum Benchmark)

ผลการรันจริงบนฐานข้อมูลหลักสูตรทั้ง 4 สาขา (DSBA, IT, AIT, BIT) บันทึกใน [`outputs/evaluation_report.md`](outputs/evaluation_report.md):

| หลักสูตร (Curriculum Slice) | จำนวนข้อสอบ | Valid SQL Rate | Execution Accuracy | ข้อสอบเชิงปฏิเสธ (Abstain) |
| :--- | :---: | :---: | :---: | :---: |
| **DSBA** | 45 | 100.0% | **100.0%** | 100.0% |
| **IT** | 45 | 100.0% | **100.0%** | 100.0% |
| **AIT** | 45 | 100.0% | **100.0%** | 100.0% |
| **BIT** | 45 | 100.0% | **100.0%** | 100.0% |
| **รวมทุกหลักสูตร (Combined Overall)** | **180** | **100.0%** | **100.0%** | **100.0%** |

> **ผล Slice Analysis:** Disparity = 0.00 ยืนยันว่าโมเดลไม่มี Shortcut Learning และมีความเที่ยงตรงข้ามทุกหลักสูตรอย่างสมบูรณ์แบบ

---

## 💻 วิธีการรันโปรแกรม (Execution)

รันชุดประเมินผลและสร้างรายงาน Markdown:
```bash
python run_lab9.py
```

รันเฉพาะส่วนสาธิตทฤษฎีบทที่ 9:
```bash
python run_lab9.py --demo-only
```

รันเฉพาะส่วนประเมินโปรเจกต์หลักสูตร:
```bash
python run_lab9.py --curriculum-only
```
