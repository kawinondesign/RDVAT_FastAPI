
import json, sys
from app.logger import format_record_th, box

def main():
    raw = sys.stdin.read()
    obj = json.loads(raw)
    data = obj.get("data") or []
    if not data:
        print("ไม่พบข้อมูลใน data")
        return
    for i, rec in enumerate(data, 1):
        print(box(f"Record {i}/{len(data)}", format_record_th(rec)))

if __name__ == "__main__":
    main()
