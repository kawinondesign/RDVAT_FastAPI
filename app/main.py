
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import VatServiceRequest, VatServiceBatchRequest, SoapRawRequest, GenericListResponse
from .rd_client import call_service, call_service_batch, RD_ENDPOINT, BASE_HEADERS
import httpx

app = FastAPI(
    title="RD VAT Proxy (SOAP → REST)",
    description="Wrapper เรียก VAT Service (กรมสรรพากร) ผ่าน SOAP แล้วคืน JSON",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/meta")
def meta():
    return {
        "rd_endpoint": RD_ENDPOINT,
        "default_headers": BASE_HEADERS,
        "version": "2.0.0"
    }

@app.post("/vat/service", response_model=GenericListResponse)
def vat_service(body: VatServiceRequest):
    try:
        data, raw_xml = call_service(
            username=body.username,
            password=body.password,
            TIN=body.TIN,
            Name=body.Name,
            ProvinceCode=body.ProvinceCode,
            BranchNumber=body.BranchNumber,
            AmphurCode=body.AmphurCode,
        )
        return GenericListResponse(count=len(data), data=data, raw_xml=raw_xml)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VAT Service error: {e}")

@app.post("/vat/service-batch", response_model=GenericListResponse)
def vat_service_batch(body: VatServiceBatchRequest):
    try:
        data, raw_xml = call_service_batch(
            username=body.username, password=body.password, TINs=body.TINs
        )
        return GenericListResponse(count=len(data), data=data, raw_xml=raw_xml)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VAT Service batch error: {e}")

@app.post("/soap/raw")
def soap_raw(req: SoapRawRequest):
    try:
        headers = dict(req.headers or {})
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/soap+xml; charset=utf-8"
        with httpx.Client(timeout=60.0) as client:
            r = client.post(req.url, content=req.xml.encode("utf-8"), headers=headers)
            return {
                "status_code": r.status_code,
                "headers": dict(r.headers),
                "text": r.text
            }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SOAP passthrough error: {e}")
