from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response 

from app.schemas.certificate import PemToPfxRequest # PemToPfxResponse is for schema documentation, not direct use here
from app.models.admin import User
from app.core.certs import convert_pem_to_pfx
from app.core.dependency import get_current_active_user

import re # For sanitizing filename
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Certificate Utilities"])

@router.post("/pem-to-pfx", response_class=Response) # Direct Response for file
async def utility_pem_to_pfx(
    request_data: PemToPfxRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Converts a user-provided PEM certificate chain and private key to PFX format.
    The PFX password will be the current user's username.
    """
    if not request_data.pem_cert_chain or not request_data.private_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PEM certificate chain and private key are required.")

    # Use username as PFX password - ensure this policy is acceptable.
    # In a real system, might want a user-provided password or a more complex derived one.
    pfx_password = current_user.username 
    if not pfx_password: # Should not happen for an authenticated user
        logger.error(f"User {current_user.id} attempting PFX conversion has no username.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User profile incomplete, cannot generate PFX password.")

    logger.info(f"User {current_user.username} initiating PEM to PFX conversion.")

    pfx_data = convert_pem_to_pfx(
        user_pem_cert_chain_str=request_data.pem_cert_chain,
        user_private_key_pem_str=request_data.private_key,
        pfx_password=pfx_password 
    )

    if not pfx_data:
        logger.error(f"PFX conversion failed for user {current_user.username}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to convert PEM data to PFX.")

    # Sanitize filename based on username
    safe_filename_base = re.sub(r'[^a-zA-Z0-9._-]', '_', current_user.username)
    if not safe_filename_base:
        safe_filename_base = "certificate_bundle" # Default if username is all non-safe chars
    
    filename = f"{safe_filename_base}.pfx"
    
    logger.info(f"PFX bundle created for user {current_user.username}, filename: {filename}")
    return Response(
        content=pfx_data,
        media_type="application/x-pkcs12",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
