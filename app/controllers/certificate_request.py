from app.core.crud import CRUDBase
from app.models.certificates import CertificateRequest
from app.schemas.certificates import CertificateRequestCreate # For creation
# For updates, we might use a different schema or Pydantic's model_dump with exclude_unset
from pydantic import BaseModel # Fallback for Update schema type hint

class CertificateRequestController(CRUDBase[CertificateRequest, CertificateRequestCreate, BaseModel]): # Using BaseModel as placeholder for Update
    def __init__(self):
        super().__init__(model=CertificateRequest)

    # Add specific methods if needed, e.g., find by user
    async def get_by_user(self, user_id: int):
        return await self.model.filter(requested_by_id=user_id).all()

certificate_request_controller = CertificateRequestController()
