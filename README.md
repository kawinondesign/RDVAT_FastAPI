# RD VAT FastAPI & CLI

โปรเจคนี้เป็น **FastAPI Service** และ **Python CLI Tool** สำหรับเชื่อมต่อกับ  
**VAT Service ของกรมสรรพากร (RD Web Service)**  
สามารถตรวจสอบผู้ประกอบการที่จดทะเบียนภาษีมูลค่าเพิ่ม (VAT) ได้ทั้งแบบ **ครั้งละ 1 ราย** และ **ครั้งละหลายราย (Batch)**  

---

## 🚀 คุณสมบัติ (Features)

- REST API (FastAPI) ครอบ SOAP Service ของกรมสรรพากร
- รองรับการตรวจสอบทีละ 1 ราย หรือหลายรายพร้อมกัน
- CLI (`rd_vat_cli.py`) ใช้งานผ่าน Terminal
- Log แสดง SOAP Request และ Response
- เลือกแสดง RAW XML สำหรับ Debug ได้
- แสดงผลลัพธ์ภาษาไทย

# RD VAT Proxy (FastAPI) 

Proxy แบบ REST สำหรับเรียก **VAT Service** ของกรมสรรพากร และมี endpoint สำหรับ passthrough SOAP raw

- RD VAT Endpoint: `https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx`
- ใช้ username/password = `anonymous` ตามคู่มือ
- สร้าง Postman collection, Dockerfile, docker-compose

## Run (Local)

```bash
python -m venv .venv
.venv\Scripts\activate   # บน Windows
pip install -r requirements.txt
```


## การรัน API
```bash
uvicorn app.main:app --reload --port 8000
```
เปิดดู API Docs ได้ที่ `http://127.0.0.1:8000/docs`


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
  "TIN": "0205543000870",
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
  "TINs": ["0205543000870","0115552010743","0105541031361","0107548000579","0115557002595"]
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
Import `RD VAT postman_collection.json` แล้วยิงได้

## Logging แสดง Request/Response บน Terminal
- ค่า Default ต์จะ log SOAP **Request (Preview)** และแต่ละ **Response Record** ในรูปแบบหัวข้อภาษาไทย
- ปรับระดับ log ได้ด้วย env `LOG_LEVEL` (เช่น DEBUG/INFO/WARN).

```bash
LOG_LEVEL=INFO uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## CLI สำหรับเรียกและแสดงผลใน Terminal โดยตรง
```bash
# ภายในโปรเจกต์ (แนะนำให้ติดตั้ง deps ตามขั้นตอน Run Local ก่อน)
python scripts/rd_vat_cli.py --tin 0205543000870
```
