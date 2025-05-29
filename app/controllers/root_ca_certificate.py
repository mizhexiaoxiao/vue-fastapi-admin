from typing import Optional
from app.core.crud import CRUDBase
from app.models.certificates import RootCACertificate
from app.schemas.certificates import RootCACertificateCreate, RootCACertificateUpdate # Assuming Update schema exists or is Base

class RootCACertificateController(CRUDBase[RootCACertificate, RootCACertificateCreate, RootCACertificateUpdate]):
    def __init__(self):
        super().__init__(model=RootCACertificate)

    async def get_active_issuer(self) -> Optional[RootCACertificate]:
        """Fetches an active Root CA configured for issuing."""
        return await self.model.filter(is_issuer=True).first()

root_ca_controller = RootCACertificateController()
