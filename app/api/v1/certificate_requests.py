from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

from app.schemas.certificate import (
    CertificateRequestCreate, 
    CertificateRequestRead, 
    CertificateRequestAdminUpdate,
    CertificateActionResponse,
    IssuedCertificateDetails,
    RequestStatusEnum
)
from app.models.admin import User
from app.models.certificate import CertificateRequest, IssuedCertificate
from app.core.certs import generate_x509_certificate
from app.core.dependency import get_current_active_user, get_current_super_user

# For parsing the generated certificate
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Certificate Requests"])

@router.post("/", response_model=CertificateRequestRead, status_code=status.HTTP_201_CREATED)
async def submit_certificate_request(
    request_data: CertificateRequestCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Allows an authenticated user to submit a new certificate signing request.
    """
    # distinguished_name_json needs to be converted to dict if it's a string, or passed as is if dict
    # For now, assuming it's passed as a dict by Pydantic parsing
    
    new_request = await CertificateRequest.create(
        user_id=current_user.id,
        common_name=request_data.common_name,
        distinguished_name_json=request_data.distinguished_name_json,
        sans=request_data.sans,
        ekus=request_data.ekus,
        requested_days=request_data.requested_days,
        public_key_pem=request_data.public_key_pem,
        status=RequestStatusEnum.PENDING.value
    )
    return await CertificateRequestRead.from_tortoise_orm(new_request)

@router.get("/", response_model=List[CertificateRequestRead])
async def list_user_certificate_requests(
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Allows an authenticated user to list their own certificate signing requests.
    """
    requests = await CertificateRequest.filter(user_id=current_user.id).offset(skip).limit(limit).order_by("-created_at").all()
    return [await CertificateRequestRead.from_tortoise_orm(req) for req in requests]

@router.get("/admin/", response_model=List[CertificateRequestRead])
async def admin_list_all_certificate_requests(
    current_admin: User = Depends(get_current_super_user),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None # e.g., "pending", "approved"
):
    """
    Allows an admin to list all certificate signing requests, optionally filtered by status.
    """
    query = CertificateRequest.all()
    if status_filter:
        query = query.filter(status=status_filter)
    
    requests = await query.offset(skip).limit(limit).order_by("-created_at").all()
    return [await CertificateRequestRead.from_tortoise_orm(req) for req in requests]

@router.post("/admin/{request_id}/action", response_model=CertificateActionResponse) # Updated response model
async def admin_act_on_certificate_request(
    request_id: int,
    action_data: CertificateRequestAdminUpdate,
    current_admin: User = Depends(get_current_super_user)
):
    """
    Allows an admin to approve or reject a certificate signing request.
    If approved, a certificate is generated and stored.
    """
    request_obj = await CertificateRequest.get_or_none(id=request_id)
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate request not found.")

    if request_obj.status not in [RequestStatusEnum.PENDING.value]: # Can only act on pending requests
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Cannot act on a request with status: {request_obj.status}"
        )

    issued_cert_details_response: Optional[IssuedCertificateDetails] = None

    if action_data.status == RequestStatusEnum.APPROVED.value:
        if not request_obj.public_key_pem: # Should always be there from creation
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Public key PEM missing in request.")

        logger.info(f"Admin {current_admin.username} attempting to approve request {request_id} for CN {request_obj.common_name}")
        generated_cert_pem = generate_x509_certificate(
            user_common_name=request_obj.common_name,
            subject_alt_names_data=request_obj.sans if request_obj.sans else [],
            ekus_data=request_obj.ekus if request_obj.ekus else [],
            requested_days=request_obj.requested_days,
            public_key_pem=request_obj.public_key_pem
        )

        if not generated_cert_pem:
            request_obj.status = RequestStatusEnum.FAILED.value # Mark as failed if generation fails
            request_obj.rejection_reason = "Certificate generation failed by CA."
            await request_obj.save()
            logger.error(f"Certificate generation failed for request {request_id}, CN: {request_obj.common_name}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Certificate generation failed.")

        try:
            # Parse the generated certificate to extract details
            cert_obj = x509.load_pem_x509_certificate(generated_cert_pem.encode(), default_backend())
            
            await IssuedCertificate.create(
                request_id=request_obj.id,
                user_id=request_obj.user_id, # Denormalized for easier lookup if needed
                serial_number=str(cert_obj.serial_number),
                pem_data=generated_cert_pem, # Store only the issued cert, or chain if generate_x509_certificate returns it
                issued_at=cert_obj.not_valid_before_utc, # Use cert's own validity
                expires_at=cert_obj.not_valid_after_utc,
            )
            request_obj.status = RequestStatusEnum.ISSUED.value
            request_obj.approved_at = datetime.now(timezone.utc)
            request_obj.rejection_reason = None # Clear any prior rejection reason if any
            await request_obj.save()
            logger.info(f"Certificate issued for request {request_id}, CN: {request_obj.common_name}, Serial: {cert_obj.serial_number}")
            
            issued_cert_details_response = IssuedCertificateDetails(
                certificate_pem=generated_cert_pem,
                pfx_available=False, # PFX generation is a separate step/endpoint
                message="Certificate issued successfully."
            )

        except Exception as e: # Catch errors during parsing or DB creation
            logger.error(f"Error processing generated certificate for request {request_id}: {e}")
            request_obj.status = RequestStatusEnum.FAILED.value
            request_obj.rejection_reason = f"Failed to process/store generated certificate: {str(e)}"
            await request_obj.save()
            # Potentially delete already generated cert if it can't be stored? Or mark as failed.
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process/store certificate: {str(e)}")


    elif action_data.status == RequestStatusEnum.REJECTED.value:
        if not action_data.rejection_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejection reason is required when rejecting a request.")
        request_obj.status = RequestStatusEnum.REJECTED.value
        request_obj.rejection_reason = action_data.rejection_reason
        request_obj.approved_at = None # Ensure approved_at is cleared
        await request_obj.save()
        logger.info(f"Admin {current_admin.username} rejected request {request_id} for CN {request_obj.common_name} with reason: {action_data.rejection_reason}")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action status. Must be 'approved' or 'rejected'.")

    updated_request_read = await CertificateRequestRead.from_tortoise_orm(request_obj)
    return CertificateActionResponse(
        request_status=updated_request_read,
        issued_certificate_details=issued_cert_details_response
    )
