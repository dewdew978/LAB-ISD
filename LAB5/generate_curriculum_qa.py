"""
generate_curriculum_qa.py
==========================
สร้างไฟล์ 2 ชนิดจาก "เล่มหลักสูตร" (curriculum book) ที่ OCR ไว้แล้ว + ground truth ที่มีอยู่ในโปรเจกต์:

  1) Map_page_<program>.csv  และไฟล์รวม Map_page_all.csv
     แมพว่า ground truth แต่ละรายการ (รายวิชา / วิชาศึกษาทั่วไป / ข้อบังคับ) ของหลักสูตรไหน
     มาจากหน้าใดบ้างในเล่มหลักสูตร (curriculum book) ของหลักสูตรนั้น ๆ
     คอลัมน์: source_gt, program, code, name_th, name_en, year, semester, pages

  2) Qa_<program>.csv  และไฟล์รวม Qa_all.csv
     คำถาม-คำตอบที่หาคำตอบได้จาก ground truth ข้างต้น พร้อมระบุหน้าอ้างอิง (source_pages)
     และเลข "ข้อ" ของข้อบังคับถ้ามี (article_no) คอลัมน์: category, question, answer, source_pages, article_no
     หมายเหตุ: article_no เป็นการค้นแบบ best-effort จากเลข "ข้อ..." ที่อยู่ใกล้ตำแหน่งพบหมวดนั้นในหน้า
     เอกสารต้นฉบับใช้เลขไทยและ OCR อ่านเพี้ยนได้ง่าย จึงควรตรวจทานอีกครั้งก่อนใช้งานจริง

หลักการค้นหาหน้า:
  - เลขหน้า "จริง" ของเอกสาร คือเลขที่อยู่บรรทัดแรกของแต่ละหน้า OCR (ไม่ใช่เลขหน้าลำดับที่ OCR
    ประมวลผล) เช่นเดียวกับที่ใช้ใน Evaluate_all.py
  - รายวิชา: ค้นหาด้วย "รหัสวิชา" (code) เพราะรหัสวิชาเป็นตัวเลข OCR อ่านได้แม่นกว่าชื่อวิชาภาษาไทย
  - ข้อบังคับ: ค้นหาด้วย "ชื่อหมวดข้อบังคับ" (category) เพราะเป็นข้อความ ไม่ใช่ตัวเลขที่ OCR อาจอ่านผิด

วิธีใช้:
    python generate_curriculum_qa.py

Input ที่ต้องมีอยู่แล้วในโปรเจกต์:
    outputs/fulldoc_<program>_ocr.json                              ผล OCR เต็มเล่มของแต่ละหลักสูตร
    data/ground_truth/<PROGRAM>/<PROGRAM>_academic_plan_*.json      แผนการเรียนของแต่ละหลักสูตร
    data/ground_truth/general_education_ground_truth.json          วิชาศึกษาทั่วไป (ใช้ร่วมกันทุกหลักสูตร)
    data/ground_truth/rules_ground_truth.json                      ข้อบังคับแยกตามหลักสูตร

Output (เขียนลงโฟลเดอร์ outputs/):
    Map_page_<program>.csv, Map_page_all.csv
    Qa_<program>.csv, Qa_all.csv
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "outputs"
GT_DIR = ROOT / "data" / "ground_truth"
OUT_DIR.mkdir(exist_ok=True)

MAP_FIELDS = ["source_gt", "program", "code", "name_th", "name_en", "year", "semester", "pages"]
QA_FIELDS = ["category", "question", "answer", "source_pages", "article_no"]

# ชื่อโปรแกรมใน ground truth ("DSBA", "IT", ...) -> ตัวย่อที่ใช้ตั้งชื่อไฟล์ fulldoc_<x>_ocr.json
PROGRAM_TO_BOOK_KEY = {
    "DSBA": "dsba",
    "IT": "it",
    "AIT": "AIT",
    "BIT": "bit",
}


# ----------------------------------------------------------------------
# 1) โหลดเล่มหลักสูตร (curriculum book) ที่ OCR ไว้แล้ว
# ----------------------------------------------------------------------

def normalize(s: Any) -> str:
    return re.sub(r"\s+", "", str(s)) if s is not None else ""


THAI_DIGITS = "๐๑๒๓๔๕๖๗๘๙"


def thai_to_arabic(s: str) -> str:
    """แปลงเลขไทย (๐-๙) ในสตริงให้เป็นเลขอารบิก"""
    return "".join(str(THAI_DIGITS.index(c)) if c in THAI_DIGITS else c for c in s)


def fix_thai_sara_am(text: str) -> str:
    """OCR มักอ่านสระ 'ำ' (SARA AM, U+0E33) แยกเป็น NIKHAHIT (ํ) + SARA AA (า)
    ทำให้ substring ที่มี 'ำ' ปกติหาไม่เจอ แก้โดยรวมสองตัวนี้กลับเป็น 'ำ' ตัวเดียว"""
    return text.replace("\u0e4d\u0e32", "\u0e33")


ARTICLE_RE = re.compile(r"ข้อ\s*([0-9๐-๙]+(?:\.[0-9๐-๙]+)*)")


def nearest_article_numbers(text: str, needle: str, window: int = 500, max_results: int = 3) -> list[str]:
    """หาเลข 'ข้อ...' ที่อยู่ใกล้ตำแหน่งที่พบ needle มากที่สุดในหน้านั้น (best-effort เท่านั้น
    เพราะเอกสารต้นฉบับใช้เลขไทยและ OCR อ่านเพี้ยนได้ง่าย ควรตรวจทานอีกครั้งก่อนใช้งานจริง)"""
    idx = text.find(needle)
    if idx == -1:
        return []
    candidates = []
    for m in ARTICLE_RE.finditer(text):
        distance = min(abs(m.start() - idx), abs(m.end() - idx))
        if distance <= window:
            candidates.append((distance, thai_to_arabic(m.group(1))))
    candidates.sort(key=lambda x: x[0])
    seen, result = set(), []
    for _, num in candidates:
        if num not in seen:
            seen.add(num)
            result.append(num)
        if len(result) >= max_results:
            break
    return result


def printed_page_number(text: str) -> str | None:
    """บรรทัดแรกของแต่ละหน้า OCR มักเป็นเลขหน้าจริงที่พิมพ์อยู่ในเอกสาร"""
    for line in text.strip().split("\n"):
        line = line.strip()
        if line:
            m = re.match(r"^\d{1,4}$", line)
            return m.group() if m else None
    return None


def load_curriculum_book(path: Path) -> dict[str, str]:
    """โหลด OCR เต็มเล่ม 1 ไฟล์ -> {เลขหน้าที่พิมพ์จริง: ข้อความรวมของหน้านั้น}
    ถ้าหน้าไหนหาเลขหน้าจริงไม่เจอ จะใช้ 'ocr<เลขลำดับ>' แทน เพื่อไม่ให้ข้อมูลหาย"""
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    pages_by_printed: dict[str, list[str]] = defaultdict(list)
    for page in doc.get("pages", []):
        text = fix_thai_sara_am(page.get("text", ""))
        printed = printed_page_number(text)
        key = printed if printed else f"ocr{page.get('page')}"
        pages_by_printed[key].append(text)
    return {key: "\n".join(chunks) for key, chunks in pages_by_printed.items()}


def discover_curriculum_books() -> dict[str, dict[str, str]]:
    """หาไฟล์ outputs/fulldoc_<program>_ocr.json ทั้งหมด
    คืนค่า {program_key: {printed_page: text}} เช่น {'dsba': {...}, 'it': {...}, 'AIT': {...}}"""
    books: dict[str, dict[str, str]] = {}
    for path in sorted(OUT_DIR.glob("fulldoc_*_ocr.json")):
        m = re.match(r"fulldoc_(.+)_ocr\.json", path.name)
        if not m:
            continue
        program_key = m.group(1)
        books[program_key] = load_curriculum_book(path)
    return books


def book_for_program(books: dict[str, dict[str, str]], program: str) -> dict[str, str] | None:
    key = PROGRAM_TO_BOOK_KEY.get(program.upper())
    if key and key in books:
        return books[key]
    for k, v in books.items():
        if k.lower() == program.lower():
            return v
    return None


def find_pages(needle: str, book_pages: dict[str, str] | None) -> set[str]:
    """หาเลขหน้าจริง (printed) ที่มีข้อความ needle ปรากฏอยู่ในเนื้อหาของหน้านั้น"""
    if not needle or not book_pages:
        return set()
    return {printed for printed, text in book_pages.items() if needle in text}


def page_sort_key(p: str):
    return (0, int(p)) if p.isdigit() else (1, p)


def join_pages(pages: set[str]) -> str:
    return ";".join(sorted(pages, key=page_sort_key))


# ----------------------------------------------------------------------
# 2) โหลด ground truth
# ----------------------------------------------------------------------

def load_course_plans() -> list[dict[str, Any]]:
    """โหลด <PROGRAM>_academic_plan_*.json จากทุกโฟลเดอร์ data/ground_truth/<PROGRAM>/"""
    plans = []
    if not GT_DIR.exists():
        return plans
    for program_dir in sorted(GT_DIR.iterdir()):
        if not program_dir.is_dir():
            continue
        for plan_path in sorted(program_dir.glob(f"{program_dir.name}_academic_plan_*.json")):
            with plan_path.open("r", encoding="utf-8") as f:
                plans.append(json.load(f))
    return plans


def load_general_education() -> dict[str, Any] | None:
    path = GT_DIR / "general_education_ground_truth.json"
    if not path.exists():
        print(f"[warn] ไม่พบ {path} - ข้ามหมวดศึกษาทั่วไป")
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_rules() -> dict[str, Any] | None:
    path = GT_DIR / "rules_ground_truth.json"
    if not path.exists():
        print(f"[warn] ไม่พบ {path} - ข้ามข้อบังคับ")
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------
# 3) สร้างแถว Map_page + Qa สำหรับ "รายวิชา" ตามแผนการเรียนของแต่ละหลักสูตร
# ----------------------------------------------------------------------

def build_course_rows(plans: list[dict[str, Any]], books: dict[str, dict[str, str]]):
    map_rows, qa_rows = [], []
    for plan in plans:
        program = plan.get("program", "")
        plan_name = plan.get("plan", "")
        book = book_for_program(books, program)
        if book is None:
            print(f"[skip] ไม่มีเล่มหลักสูตร (curriculum book) ของ {program} - ข้ามหลักสูตรนี้ทั้งหมด")
            continue
        source_gt = f"{program} {plan_name} (academic_plan_{normalize(plan_name)})".strip()

        for course in plan.get("courses", []):
            code = str(course.get("code") or "")
            name_th = course.get("name_th") or ""
            name_en = course.get("name_en") or ""
            pages = find_pages(code, book)

            map_rows.append({
                "source_gt": source_gt,
                "program": program,
                "code": code,
                "name_th": name_th,
                "name_en": name_en,
                "year": course.get("year") or "",
                "semester": course.get("semester") or "",
                "pages": join_pages(pages),
            })

            if pages and course.get("credits"):
                display_name = name_en or name_th
                question = (
                    f'วิชา {display_name} ({code}) อยู่ในชั้นปีและภาคการศึกษาใด '
                    f'และมีหน่วยกิตเท่าไร? (หลักสูตร {program} แผน {plan_name})'
                )
                answer = (
                    f'ปี {course.get("year")} ภาคการศึกษาที่ {course.get("semester")} '
                    f'หน่วยกิต {course.get("credits")}'
                )
                qa_rows.append({
                    "category": "รายวิชา",
                    "question": question,
                    "answer": answer,
                    "source_pages": join_pages(pages),
                    "article_no": "",
                })
    return map_rows, qa_rows


# ----------------------------------------------------------------------
# 4) สร้างแถว Map_page + Qa สำหรับ "หมวดศึกษาทั่วไป" (ใช้ร่วมกันทุกหลักสูตร)
# ----------------------------------------------------------------------

def build_general_education_rows(gen_ed: dict[str, Any] | None, books: dict[str, dict[str, str]]):
    map_rows, qa_rows = [], []
    if not gen_ed:
        return map_rows, qa_rows

    for program_key, book in books.items():
        for course in gen_ed.get("courses", []):
            code = str(course.get("code") or "")
            pages = find_pages(code, book)
            if not pages:
                continue  # ไม่พบในเล่มนี้เลย ไม่ต้องบันทึกแถวเปล่า

            name_th = course.get("name_th") or ""
            name_en = course.get("name_en") or ""

            map_rows.append({
                "source_gt": "หมวดศึกษาทั่วไป (general_education)",
                "program": program_key,
                "code": code,
                "name_th": name_th,
                "name_en": name_en,
                "year": "",
                "semester": "",
                "pages": join_pages(pages),
            })

            display_name = name_en or name_th
            question = f'วิชา {display_name} ({code}) เป็นวิชาบังคับหรือวิชาเลือก และมีหน่วยกิตเท่าไร?'
            answer = f'{course.get("type") or "ไม่ระบุ"}, หน่วยกิต {course.get("credits") or "ไม่ระบุ"}'
            qa_rows.append({
                "category": "หมวดศึกษาทั่วไป",
                "question": question,
                "answer": answer,
                "source_pages": join_pages(pages),
                "article_no": "",
            })
    return map_rows, qa_rows


# ----------------------------------------------------------------------
# 5) สร้างแถว Map_page + Qa สำหรับ "ข้อบังคับ" แยกตามหลักสูตร
# ----------------------------------------------------------------------

def category_search_variants(category: str) -> list[str]:
    """เอกสาร มคอ.2 จริงบางหมวดไม่มีคำว่า 'เกณฑ์' นำหน้า และบางหมวดมี '/' หรือวงเล็บภาษาอังกฤษ
    ต่อท้าย (เช่น 'เกณฑ์ภาคทัณฑ์ (probation)') จึงลองหลายรูปแบบก่อนสรุปว่าไม่พบหน้าเลย"""
    variants = [category]
    no_prefix = re.sub(r"^เกณฑ์", "", category)
    if no_prefix != category:
        variants.append(no_prefix)
    no_paren = re.sub(r"\s*\([^)]*\)\s*$", "", no_prefix).strip()
    if no_paren and no_paren not in variants:
        variants.append(no_paren)
    if "/" in no_paren:
        variants.extend(part.strip() for part in no_paren.split("/") if part.strip())
    # dedupe รักษาลำดับเดิม
    seen, ordered = set(), []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            ordered.append(v)
    return ordered


def build_rules_rows(rules_gt: dict[str, Any] | None, books: dict[str, dict[str, str]]):
    map_rows, qa_rows = [], []
    if not rules_gt:
        return map_rows, qa_rows

    for program, criteria in rules_gt.get("programs", {}).items():
        book = book_for_program(books, program)
        if book is None:
            print(f"[skip] ไม่มีเล่มหลักสูตร (curriculum book) ของ {program} - ข้ามข้อบังคับของหลักสูตรนี้")
            continue
        for crit in criteria:
            category = crit.get("category", "")

            # ลองหาแบบหลายรูปแบบ ใช้รูปแบบแรกที่เจอหน้าจริง
            pages: set[str] = set()
            matched_needle = category
            for variant in category_search_variants(category):
                found = find_pages(variant, book)
                if found:
                    pages, matched_needle = found, variant
                    break

            map_rows.append({
                "source_gt": "ข้อบังคับ (rules)",
                "program": program,
                "code": "",
                "name_th": category,
                "name_en": "",
                "year": "",
                "semester": "",
                "pages": join_pages(pages),
            })

            # หาเลข "ข้อ..." ที่อยู่ใกล้ตำแหน่งที่พบหมวดนี้มากที่สุดในแต่ละหน้า (best-effort)
            article_numbers: list[str] = []
            for printed_page in pages:
                article_numbers += nearest_article_numbers(book[printed_page], matched_needle)
            article_no = ";".join(dict.fromkeys(article_numbers))  # unique รักษาลำดับ

            values = crit.get("values") or []
            if pages and values:
                value_text = ", ".join(
                    f'{v["label"]}: {v["value"]}' for v in values if v.get("value") not in (None, "")
                )
                if value_text:
                    answer = value_text
                    if crit.get("summary"):
                        answer = f'{answer} ({crit["summary"]})'
                    qa_rows.append({
                        "category": "ข้อบังคับ",
                        "question": f'{category} ของหลักสูตร {program} กำหนดไว้อย่างไร?',
                        "answer": answer,
                        "source_pages": join_pages(pages),
                        "article_no": article_no,
                    })
    return map_rows, qa_rows


# ----------------------------------------------------------------------
# 6) เขียนไฟล์ CSV (รวมทุกหลักสูตร + แยกไฟล์ต่อหลักสูตร)
# ----------------------------------------------------------------------

def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_by_program(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("program", "unknown") or "unknown"].append(row)
    return grouped


def main() -> None:
    books = discover_curriculum_books()
    if not books:
        print(f"[warn] ไม่พบไฟล์ outputs/fulldoc_*_ocr.json เลย - จะไม่พบหน้าใด ๆ ทั้งหมด")
    else:
        print(f"พบเล่มหลักสูตร (curriculum book) ที่ OCR แล้ว: {sorted(books.keys())}")

    plans = load_course_plans()
    gen_ed = load_general_education()
    rules_gt = load_rules()

    map_rows, qa_rows = [], []

    course_map, course_qa = build_course_rows(plans, books)
    map_rows += course_map
    qa_rows += course_qa

    gened_map, gened_qa = build_general_education_rows(gen_ed, books)
    map_rows += gened_map
    qa_rows += gened_qa

    rules_map, rules_qa = build_rules_rows(rules_gt, books)
    map_rows += rules_map
    qa_rows += rules_qa

    # ไฟล์รวมทุกหลักสูตร
    write_csv(OUT_DIR / "Map_page_all.csv", MAP_FIELDS, map_rows)
    write_csv(OUT_DIR / "Qa_all.csv", QA_FIELDS, qa_rows)

    # ไฟล์แยกตามหลักสูตร (แมพหน้า curriculum book ของแต่ละหลักสูตรแยกกัน)
    for program, rows in split_by_program(map_rows).items():
        write_csv(OUT_DIR / f"Map_page_{program}.csv", MAP_FIELDS, rows)

    # Qa แยกตามหลักสูตรก็ทำได้ แต่ Qa บางข้อไม่มี program ตรง ๆ (เช่นวิชาศึกษาทั่วไปนับรวมทุกหลักสูตร)
    # จึงแยกจาก source_pages ที่มีอยู่แล้วพอ ไม่ต้อง derive program ซ้ำ

    print()
    print(f"เขียน Map_page_all.csv           {len(map_rows)} แถว")
    print(f"เขียน Qa_all.csv                 {len(qa_rows)} แถว")
    n_courses_found = sum(1 for r in map_rows if r["pages"])
    print(f"  - พบหน้าอ้างอิงจริง             {n_courses_found}/{len(map_rows)} แถว")
    print()
    print("ไฟล์ที่สร้าง (ในโฟลเดอร์ outputs/):")
    for path in sorted(OUT_DIR.glob("Map_page_*.csv")):
        print(f"  {path.name}")
    for path in sorted(OUT_DIR.glob("Qa_*.csv")):
        print(f"  {path.name}")


if __name__ == "__main__":
    main()
