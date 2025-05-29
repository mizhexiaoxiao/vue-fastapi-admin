from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import timezone # For utcnow

from app.schemas.certificate import CACreate, CARead
from app.models.admin import User
from app.models.certificate import CertificateAuthority
from app.core.dependency import get_current_super_user

from cryptography import x509
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["CA Management"])

async def _ensure_single_active_root(ca_to_activate: Optional[CertificateAuthority] = None):
    """
    Ensures only one CA is marked as is_active_root.
    If ca_to_activate is provided and is_active_root is True, all others will be deactivated.
    If ca_to_activate is None (e.g. during deletion of an active CA), it ensures no active CA if not intended.
    """
    if ca_to_activate and ca_to_activate.is_active_root:
        active_cas = await CertificateAuthority.filter(is_active_root=True).all()
        for ca in active_cas:
            if ca.id != ca_to_activate.id:
                ca.is_active_root = False
                await ca.save()
    # If ca_to_activate is being deactivated, this function doesn't need to do anything extra here,
    # the calling function will handle setting its is_active_root to False.

def _extract_expiry_from_pem(pem_data: str) -> Optional[datetime]:
    try:
        cert = x509.load_pem_x509_certificate(pem_data.encode(), default_backend())
        return cert.not_valid_after_utc
    except ValueError as e:
        logger.warning(f"Could not parse PEM to extract expiry: {e}")
        return None

@router.post("/", response_model=CARead, status_code=status.HTTP_201_CREATED)
async def create_ca(
    ca_data: CACreate,
    current_admin: User = Depends(get_current_super_user)
):
    """
    Admin: Create a new Certificate Authority.
    If `is_active_root` is true, any other existing active root CAs will be deactivated.
    """
    if await CertificateAuthority.filter(name=ca_data.name).exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CA with this name already exists.")

    expires_at = _extract_expiry_from_pem(ca_data.pem_data)
    if not expires_at and not ca_data.expires_at: # If PEM parsing fails and not provided
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not determine certificate expiry from PEM data. Please ensure PEM is valid or provide expires_at.")
    
    # If expires_at from schema is None, use the one from PEM
    final_expires_at = ca_data.expires_at if ca_data.expires_at else expires_at

    new_ca = await CertificateAuthority.create(
        name=ca_data.name,
        description=ca_data.description,
        pem_data=ca_data.pem_data,
        is_active_root=ca_data.is_active_root,
        expires_at=final_expires_at 
    )

    if new_ca.is_active_root:
        await _ensure_single_active_root(new_ca)
    
    # Re-fetch to include any updates from _ensure_single_active_root if it were to modify new_ca (it doesn't directly)
    # and to ensure the response object is fresh.
    return await CARead.from_tortoise_orm(await CertificateAuthority.get(id=new_ca.id))


@router.get("/", response_model=List[CARead])
async def list_cas(
    current_admin: User = Depends(get_current_super_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Admin: List all Certificate Authorities.
    """
    cas = await CertificateAuthority.all().offset(skip).limit(limit).order_by("-created_at")
    return [await CARead.from_tortoise_orm(ca) for ca in cas]

@router.get("/{ca_id}", response_model=CARead)
async def get_ca_details(
    ca_id: int,
    current_admin: User = Depends(get_current_super_user)
):
    """
    Admin: Get details of a specific Certificate Authority.
    """
    ca = await CertificateAuthority.get_or_none(id=ca_id)
    if not ca:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate Authority not found.")
    return await CARead.from_tortoise_orm(ca)

@router.put("/{ca_id}", response_model=CARead)
async def update_ca(
    ca_id: int,
    ca_data: CACreate, # Reusing CACreate for update, consider a CAUpdate schema if fields differ significantly
    current_admin: User = Depends(get_current_super_user)
):
    """
    Admin: Update an existing Certificate Authority.
    If `is_active_root` is changed to true, any other existing active root CA will be deactivated.
    """
    ca_to_update = await CertificateAuthority.get_or_none(id=ca_id)
    if not ca_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate Authority not found.")

    # Check for name conflict if name is being changed
    if ca_data.name != ca_to_update.name and await CertificateAuthority.filter(name=ca_data.name).exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CA with this name already exists.")

    ca_to_update.name = ca_data.name
    ca_to_update.description = ca_data.description
    
    # If PEM data changes, update it and its expiry
    if ca_data.pem_data != ca_to_update.pem_data:
        expires_at = _extract_expiry_from_pem(ca_data.pem_data)
        if not expires_at:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not determine certificate expiry from new PEM data.")
        ca_to_update.pem_data = ca_data.pem_data
        ca_to_update.expires_at = expires_at
    elif ca_data.expires_at: # Allow manual override/setting of expires_at if PEM not changing
        ca_to_update.expires_at = ca_data.expires_at


    # Handle is_active_root change
    if ca_data.is_active_root != ca_to_update.is_active_root:
        ca_to_update.is_active_root = ca_data.is_active_root
        if ca_to_update.is_active_root:
            await _ensure_single_active_root(ca_to_update)
        # If it was deactivated, and it was the only one, no other action needed by _ensure_single_active_root

    await ca_to_update.save()
    return await CARead.from_tortoise_orm(ca_to_update)


@router.delete("/{ca_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ca(
    ca_id: int,
    current_admin: User = Depends(get_current_super_user)
):
    """
    Admin: Delete a Certificate Authority.
    """
    ca_to_delete = await CertificateAuthority.get_or_none(id=ca_id)
    if not ca_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate Authority not found.")
    
    # Optional: Prevent deletion of an active root CA unless explicitly handled
    # if ca_to_delete.is_active_root:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete an active root CA. Deactivate it first.")

    # Optional: Check for dependencies (e.g., issued certificates by this CA) before deletion
    # This would require adding a relationship from IssuedCertificate back to its CA if not directly linked.
    # For now, direct deletion.

    await ca_to_delete.delete()
    return # FastAPI will return 204 No Content automatically
