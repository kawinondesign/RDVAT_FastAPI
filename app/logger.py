
import logging
import os
from typing import Dict, Any, List

LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("rd-vat")

TH_LABELS = {
    "NID": "เลขประจำตัวผู้เสียภาษี 13 หลัก (NID)",
    "BranchNumber": "เลขที่สาขา (BranchNumber)",
    "BranchTitle": "คำนำหน้าชื่อ (BranchTitle)",
    "BranchName": "ชื่อสถานประกอบการ (BranchName)",
    "BuildingName": "ชื่ออาคาร (BuildingName)",
    "RoomNumber": "ห้องที่ (RoomNumber)",
    "FloorNumber": "ชั้นที่ (FloorNumber)",
    "VillageName": "หมู่บ้าน (VillageName)",
    "HouseNumber": "เลขที่ตั้งของสถานประกอบการ (HouseNumber)",
    "MooNumber": "หมู่ที่ (MooNumber)",
    "SoiName": "ซอย (SoiName)",
    "StreetName": "ถนน (StreetName)",
    "ThumbolName": "ตำบล (ThumbolName)",
    "AmphurName": "อำเภอ (AmphurName)",
    "ProvinceName": "จังหวัด (ProvinceName)",
    "PostCode": "รหัสไปรษณีย์ (PostCode)",
    "BusinessFirstDate": "วันที่กรมสรรพากรอนุมัติให้เป็นผู้ประกอบการจดทะเบียนภาษีมูลค่าเพิ่ม ซึ่งมีสิทธิ์ออกใบกำกับภาษีซื้อ (BusinessFirstDate)",
}

KEY_ORDER = [
    "NID","BranchNumber","BranchTitle","BranchName","BuildingName","RoomNumber","FloorNumber",
    "VillageName","HouseNumber","MooNumber","SoiName","StreetName","ThumbolName",
    "AmphurName","ProvinceName","PostCode","BusinessFirstDate"
]

def box(title: str, content: str) -> str:
    border = "─" * 80
    return f"┌{border}┐│ {title} │├{border}┤{content}└{border}┘" 


def format_request_preview(xml: str, max_len: int = 2000) -> str:
    s = xml.strip().replace("\n", "")
    if len(s) > max_len:
        s = s[:max_len] + "...(truncated)"
    return box("SOAP Request (Preview)", s)

def _any_text(v):
    if isinstance(v, dict):
        if 'anyType' in v and isinstance(v['anyType'], dict):
            return v['anyType'].get('#text', '-')
        return v.get('#text') or v.get('value') or '-'
    if v is None or v == {}:
        return '-'
    return str(v)

def format_record_th(rec: Dict[str, Any]) -> str:
    # rec may use normalized keys; map back to RD keys for labels if present
    # we accept both original and normalized keys
    def get(*names):
        for n in names:
            if n in rec and rec[n] not in (None, "", {}):
                return str(rec[n])
        return "-"
    lines = []
    norm = {
        'NID': ('NID','vNID','nid'),
        'BranchNumber': ('BranchNumber','vBranchNumber','branch_number'),
        'BranchTitle': ('BranchTitle','vBranchTitleName','branch_title'),
        'BranchName': ('BranchName','vBranchName','branch_name'),
        'BuildingName': ('BuildingName','vBuildingName','building_name'),
        'RoomNumber': ('RoomNumber','vRoomNumber','room_number'),
        'FloorNumber': ('FloorNumber','vFloorNumber','floor_number'),
        'VillageName': ('VillageName','vVillageName','vVillage','vMubanName','vMooName','vVillageNo','vVillageNameTh','vVillageName','vVillageNameTH','vVillage','vMuban'),
        'HouseNumber': ('HouseNumber','vHouseNumber','house_number'),
        'MooNumber': ('MooNumber','vMooNumber','moo_number'),
        'SoiName': ('SoiName','vSoiName','soi_name'),
        'StreetName': ('StreetName','vStreetName','street_name'),
        'ThumbolName': ('ThumbolName','vThumbolName','vThambol','subdistrict_name'),
        'AmphurName': ('AmphurName','vAmphur','district_name'),
        'ProvinceName': ('ProvinceName','vProvince','province_name'),
        'PostCode': ('PostCode','vPostCode','postcode'),
        'BusinessFirstDate': ('BusinessFirstDate','vBusinessFirstDate','business_first_date'),
    }
    for k in KEY_ORDER:
        th = TH_LABELS[k]
        # iterate candidates and extract with _any_text
        val = '-'
        for cand in norm[k]:
            if cand in rec and rec[cand] not in (None, '', {}):
                val = _any_text(rec[cand])
                break
        lines.append(f"{th}: {val}")
    return "\n".join(lines)

def log_records(records: List[Dict[str, Any]]):
    if not records:
        log.info("ไม่มีข้อมูลผลลัพธ์จาก RD (records ว่าง)")
        return
    total = len(records)
    for i, rec in enumerate(records, 1):
        title = f"SOAP Response (Record {i}/{total})" if total > 1 else "SOAP Response"
        content = format_record_th(rec)
        log.info("" + box(title, content))

