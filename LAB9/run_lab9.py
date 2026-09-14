#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_lab9.py — สคริปต์หลักสำหรับรัน Lab 9: Evaluation and Overfitting
วิชา 06026240 การพัฒนาระบบอัจฉริยะ (ISD)
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง

คำสั่งใช้งาน:
    python run_lab9.py                    # รันการประเมินผลและวิเคราะห์ครบทุกส่วน
    python run_lab9.py --demo-only        # รันเฉพาะการสาธิตตัวชี้วัดบทที่ 9
    python run_lab9.py --curriculum-only  # รันเฉพาะการประเมินโปรเจกต์หลักสูตรจริง
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ตั้งค่า root path
ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.lab9_evaluator import (
    evaluate_curriculum_project,
    generate_markdown_report,
    run_full_chapter9_demo,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab 9: Evaluation and Overfitting Suite")
    parser.add_argument("--demo-only", action="store_true", help="รันเฉพาะชุดสาธิตทฤษฎีบทที่ 9")
    parser.add_argument("--curriculum-only", action="store_true", help="รันเฉพาะการประเมินโปรเจกต์หลักสูตร")
    args = parser.parse_args()

    demo_results = {}
    project_results = {}

    if not args.curriculum_only:
        demo_results = run_full_chapter9_demo()

    if not args.demo_only:
        project_results = evaluate_curriculum_project(PROJECT_ROOT)

    # บันทึกผลลัพธ์ลง outputs/
    output_dir = ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_file = output_dir / "evaluation_summary.json"
    report_file = output_dir / "evaluation_report.md"

    summary_data = {
        "lab": "Lab 9: Evaluation and Overfitting",
        "demo_results": demo_results,
        "project_results": project_results
    }
    summary_file.write_text(json.dumps(summary_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  💾 บันทึกผล JSON ไว้ที่: {summary_file}")

    if demo_results and project_results:
        generate_markdown_report(demo_results, project_results, report_file)

    print("\n" + "=" * 72)
    print("  ✅ รันกระบวนการ Lab 9 เสร็จสิ้นสมบูรณ์!")
    print("=" * 72)


if __name__ == "__main__":
    main()
