import httpx
import xmltodict
from .logger import log, format_request_preview, log_records
from typing import List, Dict, Optional, Tuple

RD_ENDPOINT = "https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx"
SOAP_NS = "http://www.w3.org/2003/05/soap-envelope"
VAT_NS = "https://rdws.rd.go.th/serviceRD3/vatserviceRD3"

BASE_HEADERS = {
    "Content-Type": "application/soap+xml; charset=utf-8",
}

def _wrap_envelope(body_xml: str) -> str:
    return f"""<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:vat="{VAT_NS}">
<soap:Header/>
<soap:Body>
{body_xml}
</soap:Body>
</soap:Envelope>"""

def _ensure_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]

def _flatten_result(obj: dict) -> List[dict]:
    # Try common RD SOAP shapes and extract a list of dict records
    if not isinstance(obj, dict):
        return []
    # Navigate to Envelope/Body
    body = obj.get("soap:Envelope") or obj.get("Envelope") or obj
    body = body.get("soap:Body") if isinstance(body, dict) else obj.get("soap:Body", {})
    if not isinstance(body, dict):
        body = obj.get("Body", {}) if isinstance(obj, dict) else {}
    # Possible response nodes
    candidates = []
    for k in ["ServiceResponse","vat:ServiceResponse","ServiceArrResponse","vat:ServiceArrResponse","ServiceResult","vat:ServiceResult","ServiceArrResult","vat:ServiceArrResult"]:
        if isinstance(body.get(k), dict):
            candidates.append(body[k])
    if not candidates:
        candidates = [v for v in body.values() if isinstance(v, dict)]
    for node in candidates:
        for v in node.values():
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                return [v]
    diff = body.get("diffgr:diffgram")
    if isinstance(diff, dict):
        for v in diff.values():
            if isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, list): return vv
                    if isinstance(vv, dict): return [vv]
    return []

def _to_plain(d):
    if not isinstance(d, dict):
        return d
    return {k: _to_plain(v) for k, v in d.items()}

def _any_text(v):
    if isinstance(v, dict):
        if "anyType" in v and isinstance(v["anyType"], dict):
            return v["anyType"].get("#text", "-")
        return v.get("#text") or v.get("value") or "-"
    if v is None or v == {}:
        return "-"
    return str(v)

def _normalize_keys(rec: dict) -> dict:
    mapping = {
        # standard keys
        "NID": "nid", "BranchNumber": "branch_number", "BranchTitle": "branch_title", "BranchName": "branch_name",
        "BuildingName": "building_name", "RoomNumber": "room_number", "FloorNumber": "floor_number",
        "VillageName": "village_name", "HouseNumber": "house_number", "MooNumber": "moo_number",
        "SoiName": "soi_name", "StreetName": "street_name", "ThumbolName": "subdistrict_name",
        "AmphurName": "district_name", "ProvinceName": "province_name", "PostCode": "postcode",
        "BusinessFirstDate": "business_first_date",
        # v-* keys
        "vNID": "nid", "vBranchNumber": "branch_number", "vBranchTitleName": "branch_title", "vBranchName": "branch_name",
        "vBuildingName": "building_name", "vRoomNumber": "room_number", "vFloorNumber": "floor_number",
        "vVillageName": "village_name", "vHouseNumber": "house_number", "vMooNumber": "moo_number",
        "vSoiName": "soi_name", "vStreetName": "street_name", "vThumbolName": "subdistrict_name", "vThambol": "subdistrict_name",
        "vAmphur": "district_name", "vProvince": "province_name", "vPostCode": "postcode", "vBusinessFirstDate": "business_first_date",
    }
    out = {}
    for k, v in rec.items():
        key = mapping.get(k, k)
        out[key] = _any_text(v)
    return out

def _request(envelope: str, headers: Dict[str, str], url: str) -> Tuple[str, dict]:
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, content=envelope.encode("utf-8"), headers=headers)
        r.raise_for_status()
        xml_text = r.text
    parsed = xmltodict.parse(xml_text)
    return xml_text, parsed

# ---------- SINGLE LOOKUP ----------
def call_service(username: str, password: str,
                 TIN: Optional[str] = None,
                 Name: Optional[str] = None,
                 ProvinceCode: int = 0,
                 BranchNumber: int = 0,
                 AmphurCode: int = 0,
                 url: str = RD_ENDPOINT,
                 headers: Optional[Dict[str,str]] = None):
    tin_xml = f"<vat:TIN>{TIN}</vat:TIN>" if TIN else "<vat:TIN></vat:TIN>"
    name_xml = f"<vat:Name>{Name}</vat:Name>" if Name else "<vat:Name></vat:Name>"
    body = f"""<vat:Service>
<vat:username>{username}</vat:username>
<vat:password>{password}</vat:password>
{tin_xml}
{name_xml}
<vat:ProvinceCode>{ProvinceCode}</vat:ProvinceCode>
<vat:BranchNumber>{BranchNumber}</vat:BranchNumber>
<vat:AmphurCode>{AmphurCode}</vat:AmphurCode>
</vat:Service>"""
    envelope = _wrap_envelope(body)
    hdrs = dict(BASE_HEADERS)
    if headers: hdrs.update(headers)
    log.info('\n' + format_request_preview(envelope))
    xml_text, parsed = _request(envelope, hdrs, url)
    # Single uses normal flatten
    records = [_normalize_keys(_to_plain(x)) for x in _flatten_result(parsed)]
    log_records(records)
    return records, xml_text

# ---------- BATCH HELPER (columnar → rows) ----------
def _extract_batch_columnar(parsed_root: dict):
    """Pivot columnar ServiceArrResult into list of row dicts.
    รองรับทั้งกรณี:
    - vNID = [anyType, anyType, ...]
    - vNID = {"anyType": [ ... ]}  <-- เคสที่ทำให้ได้ '-' ทั้งหมด
    - vNID = {"anyType": {...}}    <-- เดิมก็รองรับอยู่แล้ว
    """
    try:
        body = parsed_root.get("soap:Envelope", {}).get("soap:Body", {})
        resp = body.get("ServiceArrResponse") or body.get("vat:ServiceArrResponse")
        if not isinstance(resp, dict):
            return None
        result = resp.get("ServiceArrResult") or resp.get("vat:ServiceArrResult")
        if not isinstance(result, dict):
            return None

        cols = {}
        max_len = 0
        for k, v in result.items():
            if v is None:
                continue

            # ✅ ครอบคลุมทุกเคส
            if isinstance(v, dict) and "anyType" in v:
                # anyType อาจเป็น list หรือ ค่าเดียว
                at = v["anyType"]
                if isinstance(at, list):
                    vals = [_any_text(item) for item in at]
                else:
                    vals = [_any_text(at)]
            elif isinstance(v, list):
                vals = [_any_text(item) for item in v]
            else:
                vals = [_any_text(v)]

            cols[k] = vals
            max_len = max(max_len, len(vals))

        if max_len == 0:
            return None

        # สร้างบรรทัดละเรคคอร์ด โดยอิง index
        rows = []
        keys = list(cols.keys())
        for i in range(max_len):
            row = {}
            for k in keys:
                arr = cols.get(k, [])
                row[k] = arr[i] if i < len(arr) else "-"
            rows.append(row)

        return rows
    except Exception:
        return None
    
# ---------- BATCH LOOKUP ----------
def call_service_batch(username: str, password: str, TINs: List[str],
                       url: str = RD_ENDPOINT, headers: Optional[Dict[str,str]] = None):
    tin_items = "".join([f"<vat:string>{t}</vat:string>" for t in TINs])
    body = f"""<vat:ServiceArr>
<vat:username>{username}</vat:username>
<vat:password>{password}</vat:password>
<vat:TINs>
{tin_items}
</vat:TINs>
</vat:ServiceArr>"""
    envelope = _wrap_envelope(body)
    hdrs = dict(BASE_HEADERS)
    if headers: hdrs.update(headers)
    log.info('\n' + format_request_preview(envelope))
    xml_text, parsed = _request(envelope, hdrs, url)
    columnar = _extract_batch_columnar(parsed)
    if isinstance(columnar, list) and columnar:
        records = [_normalize_keys(_to_plain(x)) for x in columnar]
    else:
        records = [_normalize_keys(_to_plain(x)) for x in _flatten_result(parsed)]
    log_records(records)
    return records, xml_text
