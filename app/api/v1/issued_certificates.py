from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response # For custom PEM response
from typing import List

from app.schemas.certificate import IssuedCertificateRead
from app.models.admin import User
from app.models.certificate import IssuedCertificate, CertificateRequest # To get common_name
from app.core.dependency import get_current_active_user

import re # For sanitizing filename

router = APIRouter(tags=["Issued Certificates"])

@router.get("/", response_model=List[IssuedCertificateRead])
async def list_my_issued_certificates(
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Allows an authenticated user to list their own issued certificates.
    """
    # issued_certs = await IssuedCertificate.filter(user_id=current_user.id).offset(skip).limit(limit).order_by("-issued_at").all()
    
    # To include common_name, we need a join or a subsequent query.
    # For simplicity and to avoid complex ORM queries in this step, let's fetch and then enrich.
    # In a production system, a more optimized query might be preferred.
    
    issued_certs_db = await IssuedCertificate.filter(user_id=current_user.id).select_related('request').offset(skip).limit(limit).order_by("-issued_at").all()
    
    response_list = []
    for cert_db in issued_certs_db:
        common_name = "N/A"
        if cert_db.request and cert_db.request.common_name: # Accessing related CertificateRequest
            common_name = cert_db.request.common_name
        
        response_list.append(
            IssuedCertificateRead(
                id=cert_db.id,
                user_id=cert_db.user_id,
                request_id=cert_db.request_id,
                common_name=common_name,
                serial_number=cert_db.serial_number,
                issued_at=cert_db.issued_at,
                expires_at=cert_db.expires_at
            )
        )
    return response_list

@router.get("/{issued_certificate_id}/download", response_class=Response)
async def download_issued_certificate(
    issued_certificate_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Allows an authenticated user to download their specific issued certificate (PEM format).
    """
    issued_cert = await IssuedCertificate.get_or_none(id=issued_certificate_id).select_related('request')
    if not issued_cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issued certificate not found.")
    
    if issued_cert.user_id != current_user.id and not current_user.is_superuser: # Allow admin to download any for now
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to download this certificate.")

    pem_data = issued_cert.pem_data
    
    common_name = "certificate"
    if issued_cert.request and issued_cert.request.common_name:
        common_name = issued_cert.request.common_name
    
    # Sanitize filename
    safe_filename_base = re.sub(r'[^a-zA-Z0-9._-]', '_', common_name)
    if not safe_filename_base: # Handle cases where CN is all non-safe chars
        safe_filename_base = re.sub(r'[^a-zA-Z0-9._-]', '_', issued_cert.serial_number) or "certificate"

    filename = f"{safe_filename_base}.pem"

    return Response(
        content=pem_data,
        media_type="application/x-pem-file",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
