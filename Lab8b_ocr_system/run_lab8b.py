"""Run the Lab 7B -> Lab 8B workflow on Windows, macOS, or Linux.

Supports multiple curriculums: DSBA, IT, AIT, or all combined.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAB7 = ROOT / "src" / "ocr_system" / "lab7b_curriculum.py"
LAB8 = ROOT / "src" / "ocr_system" / "lab8b_curriculum_db.py"
LAB7_OUT = ROOT / "work" / "lab7b_run"
LAB8_OUT = ROOT / "work" / "lab8b_run"

PROGRAM_CONFIGS = {
    "DSBA": {
        "program_id": "DSBA-coop",
        "program_name": "วิทยาการข้อมูลและการวิเคราะห์เชิงธุรกิจ (สหกิจศึกษา)",
        "name_en": "Data Science and Business Analytics (DSBA)",
        "total_credits": 135,
        "years": 4,
        "input_gt": ROOT / "data" / "ground_truth_C" / "DSBA_academic_plan_coop.json",
        "input_img": ROOT / "data" / "input_C",
        "gold_q": ROOT / "data" / "gold_questions_DSBA.json",
        "lab7_dir": ROOT / "work" / "lab7b_run_DSBA",
    },
    "IT": {
        "program_id": "IT-coop",
        "program_name": "เทคโนโลยีสารสนเทศ (สหกิจศึกษา)",
        "name_en": "Information Technology (IT)",
        "total_credits": 129,
        "years": 4,
        "input_gt": ROOT / "data" / "ground_truth_C" / "IT_academic_plan_coop.json",
        "input_img": ROOT / "data" / "input_IT",
        "gold_q": ROOT / "data" / "gold_questions_IT.json",
        "lab7_dir": ROOT / "work" / "lab7b_run_IT",
    },
    "AIT": {
        "program_id": "AIT",
        "program_name": "เทคโนโลยีปัญญาประดิษฐ์",
        "name_en": "Artificial Intelligence Technology (AIT)",
        "total_credits": 120,
        "years": 4,
        "input_gt": ROOT / "data" / "ground_truth_C" / "AIT_academic_plan.json",
        "input_img": ROOT / "data" / "input_AIT",
        "gold_q": ROOT / "data" / "gold_questions_AIT.json",
        "lab7_dir": ROOT / "work" / "lab7b_run_AIT",
    },
    "BIT": {
        "program_id": "BIT-coop",
        "program_name": "เทคโนโลยีสารสนเทศทางธุรกิจ (สหกิจศึกษา)",
        "name_en": "Business Information Technology (BIT)",
        "total_credits": 126,
        "years": 4,
        "input_gt": ROOT / "data" / "ground_truth_C" / "BIT_academic_plan_coop.json",
        "input_img": ROOT / "data" / "input_BIT",
        "gold_q": ROOT / "data" / "gold_questions_BIT.json",
        "lab7_dir": ROOT / "work" / "lab7b_run_BIT",
    },
}


def run(*args: object) -> None:
    subprocess.run([sys.executable, *(str(x) for x in args)], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Lab 8B multi-curriculum workflow")
    parser.add_argument("--skip-lab7", action="store_true", help="ข้ามขั้นตอน Lab 7B")
    parser.add_argument("--program", choices=["all", "DSBA", "IT", "AIT", "BIT"], default="all",
                        help="เลือกหลักสูตรที่ต้องการประมวลผล (all, DSBA, IT, AIT, BIT)")
    parser.add_argument("--skip-eval", action="store_true", help="ข้ามขั้นตอน LLM evaluation")
    args = parser.parse_args()

    os.environ.update({
        "PYTHONUTF8": "1",
        "LAB7_CHUNK": "1",
        "LAB7B_NUM_CTX": "4096",
        "LAB7B_NUM_PREDICT": "2000",
        "LAB7B_OCR_NUM_CTX": "4096",
        "LAB7B_OCR_NUM_PREDICT": "1200",
    })
    LAB7_OUT.mkdir(parents=True, exist_ok=True)
    LAB8_OUT.mkdir(parents=True, exist_ok=True)

    # 1) สร้าง Schema DDL & JSON Schema
    run(LAB8, "schema", "-o", LAB8_OUT / "schema")

    programs_to_run = list(PROGRAM_CONFIGS.keys()) if args.program == "all" else [args.program]

    # 2) รัน Lab 7B หากต้องการ (รองรับทุกหลักสูตรที่มีภาพอินพุตและ Ground Truth)
    if not args.skip_lab7:
        for prog_key in programs_to_run:
            cfg = PROGRAM_CONFIGS[prog_key]
            out_dir = cfg["lab7_dir"]
            out_dir.mkdir(parents=True, exist_ok=True)
            if not (out_dir / "pred_vlm.json").exists() and cfg["input_img"].exists():
                run(LAB7, "-i", cfg["input_img"],
                    "-g", cfg["input_gt"],
                    "-p", "vlm", "-o", out_dir)

    # 3) แปลงข้อมูลแต่ละหลักสูตรเข้าสู่ JSON และสร้าง DB แยกรายหลักสูตร
    converted_files = {}
    for prog_key in programs_to_run:
        cfg = PROGRAM_CONFIGS[prog_key]
        candidates = [
            cfg["lab7_dir"] / "pred_vlm.json",
            ROOT / "work" / f"lab7b_run_{prog_key}" / "pred_vlm.json",
            LAB7_OUT / "pred_vlm.json" if prog_key == "DSBA" else None,
            LAB7_OUT / "pred_markdown.json" if prog_key == "DSBA" else None,
        ]
        pred_file = next((p for p in candidates if p and p.exists()), cfg["input_gt"])

        prog_dir = LAB8_OUT / prog_key
        prog_dir.mkdir(parents=True, exist_ok=True)
        prog_json = prog_dir / "curriculum.json"
        prog_db = prog_dir / "curriculum.db"
        prog_verify = prog_dir / "verify.json"

        run(LAB8, "import-lab7b", "-i", pred_file,
            "-o", prog_json,
            "--program-id", cfg["program_id"],
            "--program-name", cfg["program_name"],
            "--name-en", cfg["name_en"],
            "--total-credits", cfg["total_credits"],
            "--years", cfg["years"])

        run(LAB8, "load", "-i", prog_json, "-d", prog_db, "--replace")
        run(LAB8, "verify", "-d", prog_db, "-o", prog_verify)

        if cfg["gold_q"].exists():
            shutil.copyfile(cfg["gold_q"], prog_dir / "gold_questions.json")

        converted_files[prog_key] = prog_json

    # 4) โหลดเข้าสู่ฐานข้อมูลหลัก curriculum.db
    main_db = LAB8_OUT / "curriculum.db"
    main_verify = LAB8_OUT / "verify.json"
    main_gold = LAB8_OUT / "gold_questions.json"
    comb_dir = LAB8_OUT / "combined"
    comb_dir.mkdir(parents=True, exist_ok=True)

    if args.program == "all":
        # โหลดหลักสูตรแรกด้วย --replace และหลักสูตรถัดไปด้วย append (ไม่มี --replace)
        first = True
        for prog_key in programs_to_run:
            load_args = [LAB8, "load", "-i", converted_files[prog_key], "-d", main_db]
            if first:
                load_args.append("--replace")
                first = False
            run(*load_args)

        # ตั้งค่า curriculum.json เป็นหลักสูตร DSBA หรือสร้างภาพรวม
        shutil.copyfile(converted_files["DSBA"], LAB8_OUT / "curriculum.json")

        # ตรวจสอบความถูกต้องของ curriculum.db รวม
        run(LAB8, "verify", "-d", main_db, "-o", main_verify)

        # ใช้ชุดคำถามทองคำรวม
        comb_q = ROOT / "data" / "gold_questions_combined.json"
        if comb_q.exists():
            shutil.copyfile(comb_q, main_gold)

        # ซิงค์เข้าโฟลเดอร์ combined/
        shutil.copyfile(main_db, comb_dir / "curriculum.db")
        shutil.copyfile(LAB8_OUT / "curriculum.json", comb_dir / "curriculum.json")
        shutil.copyfile(main_verify, comb_dir / "verify.json")
        if main_gold.exists():
            shutil.copyfile(main_gold, comb_dir / "gold_questions.json")
    else:
        prog_key = args.program
        prog_dir = LAB8_OUT / prog_key
        shutil.copyfile(prog_dir / "curriculum.json", LAB8_OUT / "curriculum.json")
        shutil.copyfile(prog_dir / "curriculum.db", main_db)
        shutil.copyfile(prog_dir / "verify.json", main_verify)
        if (prog_dir / "gold_questions.json").exists():
            shutil.copyfile(prog_dir / "gold_questions.json", main_gold)

    # 5) ประเมินผลคำถามทองคำ
    if not args.skip_eval:
        if not main_gold.exists() or len(json.loads(main_gold.read_text(encoding="utf-8"))) < 30:
            print(f"\nเพิ่มคำถามใน {main_gold} ให้ครบ 30 ข้อ แล้วรันใหม่")
            return
        eval_out = LAB8_OUT / "eval_result.json"
        run(LAB8, "eval", "-d", main_db, "-q", main_gold, "-o", eval_out)
        if args.program == "all":
            shutil.copyfile(eval_out, comb_dir / "eval_result.json")
        else:
            shutil.copyfile(eval_out, LAB8_OUT / args.program / "eval_result.json")

    print(f"\nเสร็จสิ้นกระบวนการ Lab 8B: {LAB8_OUT}")


if __name__ == "__main__":
    main()
