
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

ANON = "anonymous"

class VatServiceRequest(BaseModel):
    username: str = Field(default=ANON, description="RD username; use 'anonymous'")
    password: str = Field(default=ANON, description="RD password; use 'anonymous'")
    TIN: Optional[str] = Field(default=None, description="13-digit taxpayer ID, or None")
    Name: Optional[str] = Field(default=None, description="Shop/Company name to search")
    ProvinceCode: int = Field(default=0, description="Province code; 0 = unknown")
    BranchNumber: int = Field(default=0, description="Branch number; 0 = unknown")
    AmphurCode: int = Field(default=0, description="District (amphur) code; 0 = unknown")

class VatServiceBatchRequest(BaseModel):
    username: str = Field(default=ANON)
    password: str = Field(default=ANON)
    TINs: List[str] = Field(default_factory=list, description="List of 13-digit TINs")

class SoapRawRequest(BaseModel):
    xml: str = Field(..., description="Full SOAP envelope XML to send as-is")
    url: str = Field(default="https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx")
    headers: Dict[str, str] = Field(default_factory=lambda: {"Content-Type":"application/soap+xml; charset=utf-8"})

class GenericListResponse(BaseModel):
    count: int
    data: List[dict]
    raw_xml: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
