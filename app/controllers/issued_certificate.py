from app.core.crud import CRUDBase
from app.models.certificates import IssuedCertificate
# Define Create/Update schemas if direct creation/update of IssuedCertificate is needed
# For now, IssuedCertificates are created as part of the CertificateRequest approval flow.
from pydantic import BaseModel # Fallback for Create/Update schema type hints

class IssuedCertificateController(CRUDBase[IssuedCertificate, BaseModel, BaseModel]): # Using BaseModel as placeholder
    def __init__(self):
        super().__init__(model=IssuedCertificate)

    async def get_by_serial_number(self, serial_number: str):
        return await self.model.filter(serial_number=serial_number).first()

issued_certificate_controller = IssuedCertificateController()
