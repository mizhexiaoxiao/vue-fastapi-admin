import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body

from app.models.admin import User
from app.models.certificates import RootCACertificate, CertificateRequest, IssuedCertificate
from app.schemas.certificates import (
    RootCACertificateCreate, RootCACertificateRead, RootCACertificateUpdate,
    RootCACertificateCreate, RootCACertificateRead, RootCACertificateUpdate,
    CertificateRequestCreate, CertificateRequestRead, CertificateRequestUpdateByAdmin, # Added CertificateRequestCreate
    IssuedCertificateRead, CertificateRequestUserRead # Added CertificateRequestUserRead and IssuedCertificateRead
)
from app.controllers import (
    root_ca_controller, certificate_request_controller, issued_certificate_controller
)
from app.core.dependency import current_active_user, get_current_active_superuser # Updated import
from app.core import certificate_utils
from app.settings.config import settings


router = APIRouter(prefix="/certificates", tags=["Certificates"]) # Changed tag for broader scope

# --- Root CA Management Endpoints (Admin Only) ---
# Note: These should ideally be under a sub-router like /admin/root_ca or have more specific admin tags/dependencies
# For now, keeping them here but assuming get_current_active_superuser dependency handles admin restriction.

@router.post("/root_ca", response_model=RootCACertificateRead)
async def upload_root_ca(ca_in: RootCACertificateCreate, uploaded_by: User = Depends(get_current_active_superuser)):
    """
    Upload a new Root CA certificate.
    The private key, if provided, is stored as plain text in this version.
    TODO: Encrypt private_key_pem before storing in encrypted_private_key.
    """
    # For now, directly using ca_in.private_key_pem as the "encrypted" key.
    # In a real scenario, encrypt ca_in.private_key_pem here.
    # The salt would be generated during encryption.
    encrypted_key_placeholder = ca_in.private_key_pem 
    salt_placeholder = "TODO_generate_salt_if_encrypting" if ca_in.private_key_pem else None

    db_ca = await RootCACertificate.create(
        name=ca_in.name,
        certificate_pem=ca_in.certificate_pem,
        encrypted_private_key=encrypted_key_placeholder, # TODO: Encrypt this
        private_key_salt=salt_placeholder, # TODO: Store actual salt
        is_issuer=ca_in.is_issuer,
        uploaded_by_id=uploaded_by.id
    )
    # Manually construct the response to include encrypted_private_key if it exists
    # Pydantic v2 from_attributes should handle this if model fields match schema fields
    return db_ca


@router.get("/root_ca", response_model=List[RootCACertificateRead], dependencies=[Depends(get_current_active_superuser)])
async def list_root_cas(_: User = Depends(get_current_active_superuser)): # Add dependency usage if not using the user object directly
    """List all Root CA certificates."""
    cas = await root_ca_controller.list()
    return cas

@router.get("/root_ca/{ca_id}", response_model=RootCACertificateRead)
async def get_root_ca(ca_id: int, _: User = Depends(get_current_active_superuser)):
    """Get a specific Root CA certificate by ID."""
    ca = await root_ca_controller.get(id=ca_id)
    if not ca:
        raise HTTPException(status_code=404, detail="Root CA not found")
    return ca

@router.put("/root_ca/{ca_id}", response_model=RootCACertificateRead)
async def update_root_ca(ca_id: int, ca_update: RootCACertificateUpdate, _: User = Depends(get_current_active_superuser)):
    """Update a Root CA certificate (e.g., name, is_issuer, or replace cert/key)."""
    ca = await root_ca_controller.get(id=ca_id)
    if not ca:
        raise HTTPException(status_code=404, detail="Root CA not found")

    update_data = ca_update.model_dump(exclude_unset=True)
    
    # TODO: If private_key_pem is updated, it needs to be encrypted before saving.
    if "private_key_pem" in update_data and update_data["private_key_pem"] is not None:
        ca.encrypted_private_key = update_data["private_key_pem"] # Placeholder for encryption
        ca.private_key_salt = "TODO_new_salt" # Placeholder for new salt
        del update_data["private_key_pem"] # Don't try to save private_key_pem directly to model
    elif "private_key_pem" in update_data and update_data["private_key_pem"] is None: # Explicitly clearing the key
        ca.encrypted_private_key = None
        ca.private_key_salt = None
        del update_data["private_key_pem"]


    for field, value in update_data.items():
        setattr(ca, field, value)
    
    await ca.save()
    return ca

@router.delete("/root_ca/{ca_id}", status_code=204)
async def delete_root_ca(ca_id: int, _: User = Depends(get_current_active_superuser)):
    """Delete a Root CA certificate."""
    ca = await root_ca_controller.get(id=ca_id)
    if not ca:
        raise HTTPException(status_code=404, detail="Root CA not found")
    try:
        await root_ca_controller.delete(id=ca_id)
    except Exception as e: # Catching generic exception, specific DB exceptions are better
        # Tortoise ORM raises IntegrityError (e.g. from asyncmy.errors.IntegrityError) for FK violations
        if "FOREIGN KEY constraint failed" in str(e) or "Cannot delete or update a parent row" in str(e): # Adapt based on DB
             raise HTTPException(
                status_code=400, 
                detail="Cannot delete Root CA: It has issued certificates or is referenced elsewhere."
            )
        raise HTTPException(status_code=500, detail=f"Error deleting Root CA: {str(e)}")
    return None


# --- Certificate Request Management Endpoints (Admin Only) ---

@router.get("/requests/admin", response_model=List[CertificateRequestRead], dependencies=[Depends(get_current_active_superuser)])
async def list_all_certificate_requests_admin(_: User = Depends(get_current_active_superuser)):
    """List all certificate requests (for admins)."""
    requests = await certificate_request_controller.list()
    return requests

@router.post("/requests/{request_id}/approve", response_model=IssuedCertificateRead)
async def approve_certificate_request(request_id: int, admin_user: User = Depends(get_current_active_superuser)):
    """Approve a certificate request and issue the certificate."""
    req = await certificate_request_controller.get(id=request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Certificate request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is not in 'pending' state (current: {req.status})")

    issuer_ca_model = await root_ca_controller.get_active_issuer()
    if not issuer_ca_model:
        raise HTTPException(status_code=500, detail="No active issuer CA configured in the system.")
    if not issuer_ca_model.encrypted_private_key or not issuer_ca_model.certificate_pem:
        raise HTTPException(status_code=500, detail="Active issuer CA is missing private key or certificate.")

    try:
        issuer_ca_cert_obj = certificate_utils.load_ca_certificate(issuer_ca_model)
        # TODO: Securely decrypt private key here
        issuer_ca_key_obj = certificate_utils.load_ca_private_key(issuer_ca_model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load issuer CA materials: {str(e)}")

    try:
        (user_private_key_pem, 
         full_chain_pem, 
         serial_hex, 
         valid_from_dt, 
         valid_to_dt, 
         subject_dn_str) = certificate_utils.generate_signed_certificate(
            request_data=req, # Pass the CertificateRequest model instance
            issuer_ca_cert=issuer_ca_cert_obj,
            issuer_ca_key=issuer_ca_key_obj
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate certificate: {str(e)}")

    # TODO: Encrypt user_private_key_pem before storing if system stores it
    # For this subtask, we are not storing the user's private key in IssuedCertificate model directly
    # but it's returned by generate_signed_certificate. If it were to be stored, it would need encryption.
    # UPDATE: Storing it now, with a TODO for encryption.

    # TODO: Store user_private_key_pem securely. Currently stored as plain text.
    # No salt is generated/used for plain text storage. Salt would be part of an encryption process.
    issued_cert = await IssuedCertificate.create(
        serial_number=serial_hex,
        subject_dn=subject_dn_str,
        encrypted_private_key=user_private_key_pem, # Storing the user's private key
        # private_key_salt=None, # Explicitly None as no encryption is done yet
        issuer_dn=issuer_ca_cert_obj.subject.rfc4514_string(),
        valid_from=valid_from_dt,
        valid_to=valid_to_dt,
        certificate_pem=full_chain_pem,
        status="valid",
        request_id=req.id,
        issued_by_ca_id=issuer_ca_model.id,
        issued_by_user_id=admin_user.id
    )

    req.status = "approved"
    req.approved_by_id = admin_user.id
    req.processed_at = datetime.datetime.now(datetime.timezone.utc)
    await req.save()

    return issued_cert


@router.post("/requests/{request_id}/reject", response_model=CertificateRequestRead)
async def reject_certificate_request(
    request_id: int, 
    payload: CertificateRequestUpdateByAdmin, # Using schema for rejection reason
    admin_user: User = Depends(get_current_active_superuser)
):
    """Reject a certificate request."""
    req = await certificate_request_controller.get(id=request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Certificate request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is not in 'pending' state (current: {req.status})")
    
    if payload.status != "rejected":
        raise HTTPException(status_code=400, detail="Invalid status for rejection. Must be 'rejected'.")
    if not payload.rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required when rejecting a request.")

    req.status = "rejected"
    req.rejection_reason = payload.rejection_reason
    req.approved_by_id = admin_user.id # User who actioned it
    req.processed_at = datetime.datetime.now(datetime.timezone.utc)
    await req.save()
    return req


# --- User-Facing Certificate Endpoints ---

@router.post("/requests", response_model=CertificateRequestRead, tags=["Certificates User"])
async def submit_certificate_request(
    request_in: CertificateRequestCreate, 
    current_user: User = Depends(current_active_user)
):
    """
    Submit a new certificate signing request.
    """
    new_request = await CertificateRequest.create(
        common_name=request_in.common_name,
        sans=request_in.sans,
        status="pending", # Initial status
        requested_by_id=current_user.id,
        # created_at and updated_at are handled by TimestampMixin
    )
    # Use the controller to fetch to ensure consistent response model if needed, or directly return
    # For simple create, direct return is fine if model matches schema well.
    # Let's use controller.get() to be consistent with how Read schemas are often populated.
    return await certificate_request_controller.get(id=new_request.id)


@router.get("/requests", response_model=List[CertificateRequestUserRead], tags=["Certificates User"])
async def list_my_certificate_requests(current_user: User = Depends(current_active_user)):
    """
    List all certificate requests submitted by the current user.
    """
    # Using the specific controller method created earlier
    requests = await certificate_request_controller.get_by_user(user_id=current_user.id)
    return requests


# Define a new response model for downloading certificate data
from pydantic import BaseModel
class CertificateDownloadData(BaseModel):
    certificate_pem: str
    private_key_pem: Optional[str] = None # Only if generated by system and user is downloading their own

@router.get("/issued_certificates/{issued_certificate_id}/download", response_model=CertificateDownloadData, tags=["Certificates User"])
async def download_issued_certificate_and_key(
    issued_certificate_id: int,
    current_user: User = Depends(current_active_user)
):
    """
    Download an issued certificate and its private key (if applicable and stored).
    Users can only download certificates requested by them.
    """
    issued_cert = await issued_certificate_controller.get(id=issued_certificate_id)
    if not issued_cert:
        raise HTTPException(status_code=404, detail="Issued certificate not found.")

    # Eagerly load the related request to check ownership
    await issued_cert.fetch_related('request')
    if not issued_cert.request or issued_cert.request.requested_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to download this certificate.")

    if issued_cert.status != "valid": # Or if request.status != "approved"
         # This check might be redundant if only "valid" certs are generally accessible
        raise HTTPException(status_code=400, detail=f"Certificate is not in a downloadable state (status: {issued_cert.status}).")

    # TODO: CRITICAL SECURITY - If issued_cert.encrypted_private_key is stored,
    # it MUST be decrypted here before returning.
    # For this subtask, we assume it's plain text if it were to be populated.
    # The current IssuedCertificate model does not store user's private key directly,
    # generate_signed_certificate returns it but it's not saved in this flow.
    # If it were, here's where decryption would happen:
    user_private_key_pem_decrypted = issued_cert.encrypted_private_key # Placeholder

    return CertificateDownloadData(
        certificate_pem=issued_cert.certificate_pem, # This should be the full chain
        private_key_pem=user_private_key_pem_decrypted # This would be the user's key
    )
