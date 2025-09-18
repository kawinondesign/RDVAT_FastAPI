
# RD VAT Proxy (FastAPI) — v2

Proxy แบบ REST สำหรับเรียก **VAT Service** (SOAP 1.2) ของกรมสรรพากร และมี endpoint สำหรับ passthrough SOAP raw ได้ด้วย

- RD VAT Endpoint: `https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx`
- ใช้ username/password = `anonymous` ตามคู่มือ
- สร้างมาพร้อม Postman collection, Dockerfile, docker-compose

## Run (Local)

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Run (Docker)

```bash
docker build -t rd-vat-fastapi:v2 .
docker run --rm -p 8000:8000 --name rd-vat rd-vat-fastapi:v2
# หรือ
docker compose up --build
```

## Endpoints

### GET /health
ตรวจสอบว่าเซิร์ฟเวอร์ทำงาน

### GET /meta
metadata ของ proxy (RD endpoint, headers)

### POST /vat/service
ตรวจสอบทีละ 1 ราย
```json
{
  "username": "anonymous",
  "password": "anonymous",
  "TIN": "",
  "Name": "",
  "ProvinceCode": 0,
  "BranchNumber": 0,
  "AmphurCode": 0
}
```

### POST /vat/service-batch
ตรวจสอบหลายราย (TINs)
```json
{
  "username": "anonymous",
  "password": "anonymous",
  "TINs": ["0105557074061","0107544000123"]
}
```

### POST /soap/raw
passthrough SOAP ได้โดยตรง (กำหนด xml + url + headers เอง)
```json
{
  "url": "https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx",
  "headers": {"Content-Type":"application/soap+xml; charset=utf-8"},
  "xml": "<soap:Envelope>...ตามต้องการ...</soap:Envelope>"
}
```

## Postman
Import `RD VAT v2.postman_collection.json` แล้วยิงได้ทันที (มีตัวอย่างครบทั้ง REST และ SOAP passthrough)

## หมายเหตุ
- ถ้า RD เปลี่ยนโครงสร้าง XML, โค้ดพาร์สได้หลายรูปแบบที่พบบ่อยแล้ว แต่หากเจอรูปแบบใหม่ ช่วยแนบ `raw_xml` มาเพื่อปรับปรุงตัว parser ได้
- ถ้าต้องการเรียก CommonService เพื่อตรวจรหัสจังหวัด/อำเภอ สามารถต่อยอดเพิ่มโมดูล SOAP แบบเดียวกันในไฟล์ใหม่ได้
- ทดสอบบน Python 3.12 / Uvicorn 2025


## Logging แสดง Request/Response บน Terminal
- ค่าดีฟอลต์จะ log SOAP **Request (Preview)** และแต่ละ **Response Record** ในรูปแบบหัวข้อภาษาไทย
- ปรับระดับ log ได้ด้วย env `LOG_LEVEL` (เช่น DEBUG/INFO/WARN).

ตัวอย่างการรันให้เห็น log ชัด ๆ:
```bash
LOG_LEVEL=INFO uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## CLI สำหรับเรียกและแสดงผลใน Terminal โดยตรง
```bash
# ภายในโปรเจกต์ (แนะนำให้ติดตั้ง deps ตามขั้นตอน Run Local ก่อน)
python scripts/rd_vat_cli.py --tin 0105557074061
# หรือค้นหาด้วยชื่อ
python scripts/rd_vat_cli.py --name "ชื่อร้าน/บริษัท"
```
