#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import sys, os

# ให้รันตรงได้: python scripts/rd_vat_cli.py ...
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.rd_client import call_service, call_service_batch
from app.logger import format_record_th, box

def main():
    p = argparse.ArgumentParser(description="RD VAT CLI (single/batch) แสดงผลภาษาไทย")
    p.add_argument("--username", default="anonymous")
    p.add_argument("--password", default="anonymous")
    p.add_argument("--tin", nargs="+", help="เลขประจำตัวผู้เสียภาษี 13 หลัก (ใส่ได้หลายค่า)")
    p.add_argument("--name", default=None, help="ชื่อผู้ประกอบการ (optional)")
    p.add_argument("--province", type=int, default=0, help="ProvinceCode (default 0)")
    p.add_argument("--branch", type=int, default=0, help="BranchNumber (default 0)")
    p.add_argument("--amphur", type=int, default=0, help="AmphurCode (default 0)")
    p.add_argument("--verbose", action="store_true", help="แสดง RAW XML (ตัดย่อ)")
    args = p.parse_args()

    try:
        if args.tin and len(args.tin) > 1:
            records, raw_xml = call_service_batch(
                username=args.username,
                password=args.password,
                TINs=args.tin,
            )
        else:
            tin = args.tin[0] if args.tin else None
            records, raw_xml = call_service(
                username=args.username,
                password=args.password,
                TIN=tin,
                Name=args.name,
                ProvinceCode=args.province,
                BranchNumber=args.branch,
                AmphurCode=args.amphur,
            )
    except Exception as e:
        print("เกิดข้อผิดพลาดระหว่างเรียก RD:", repr(e))
        sys.exit(1)

    if args.verbose:
        preview = raw_xml[:4000] + ("...(truncated)" if raw_xml and len(raw_xml) > 4000 else "")
        print(box("RAW XML (Preview)", preview if preview else "-"))

    if not records:
        print("ไม่พบข้อมูล")
        return

    total = len(records)
    if total > 1:
        print(f"\nพบทั้งหมด {total} รายการ\n")

    for i, rec in enumerate(records, 1):
        title = f"ผลลัพธ์ {i}/{total}" if total > 1 else "ผลลัพธ์"
        print(box(title, format_record_th(rec)))

if __name__ == "__main__":
    main()
