from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

# Optional: Enum for status if strict validation is desired elsewhere,
# but schemas will use str as per spec for CertificateRequestAdminUpdate.
class RequestStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ISSUED = "issued" # Status after successful generation
    FAILED = "failed" # Status if generation fails post-approval

class CertificateRequestBase(BaseModel):
    common_name: str = Field(..., example="example.com")
    distinguished_name_json: Optional[Dict[str, str]] = Field(None, example={"O": "My Org", "OU": "IT", "L": "City", "ST": "State", "C": "US"})
    sans: Optional[List[str]] = Field(None, example=["dns:example.com", "dns:www.example.com", "ip:192.168.1.1"])
    ekus: Optional[List[str]] = Field(None, example=["1.3.6.1.5.5.7.3.1", "1.3.6.1.5.5.7.3.2"]) # OIDs for Server Auth, Client Auth
    requested_days: int = Field(default=365, gt=0, le=3650) # e.g., 1 to 10 years
    public_key_pem: str = Field(..., example="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----")

class CertificateRequestCreate(CertificateRequestBase):
    pass

class CertificateRequestRead(CertificateRequestBase):
    id: int
    user_id: int
    status: str = Field(example=RequestStatusEnum.PENDING.value)
    rejection_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CertificateRequestAdminUpdate(BaseModel):
    status: str = Field(..., example=RequestStatusEnum.APPROVED.value) # e.g., "approved", "rejected"
    rejection_reason: Optional[str] = None

# Schema for the response when a certificate is successfully issued
class IssuedCertificateDetails(BaseModel):
    certificate_pem: str
    pfx_available: bool # Placeholder, PFX generation is separate
    message: str

class CertificateActionResponse(BaseModel):
    request_status: CertificateRequestRead
    issued_certificate_details: Optional[IssuedCertificateDetails] = None


# --- Schemas for Subtask 15 ---

class IssuedCertificateRead(BaseModel):
    id: int
    user_id: int
    request_id: int
    common_name: str # This will need to be populated from the related request in the endpoint logic
    serial_number: str
    issued_at: datetime
    expires_at: datetime
    # pem_data: str # Usually not included in list views for brevity, but available for download endpoint

    class Config:
        from_attributes = True

class CACreate(BaseModel):
    name: str = Field(..., example="My Organization Root CA")
    description: Optional[str] = None
    pem_data: str = Field(..., example="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----") # PEM bundle for the CA
    is_active_root: bool = Field(default=False)
    # expires_at: Optional[datetime] = None # This can be derived from pem_data upon creation/update

class CARead(CACreate):
    id: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None # Will be populated from the certificate data

    class Config:
        from_attributes = True

class PemToPfxRequest(BaseModel):
    pem_cert_chain: str = Field(..., description="PEM encoded certificate chain (user cert first, then intermediates).")
    private_key: str = Field(..., description="PEM encoded private key for the user certificate.")
    # pfx_password will be derived from username or a default policy

class PemToPfxResponse(BaseModel):
    pfx_filename: str = Field(example="user_cert.pfx")
    message: str = Field(default="PFX bundle created successfully.")
    # The actual PFX data will be streamed as a file response, not in JSON.
