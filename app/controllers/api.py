from app.core.crud import CRUDBase
from app.models.admin import Api
from app.schemas.apis import ApiCreate, ApiUpdate


class ApiController(CRUDBase[Api, ApiCreate, ApiUpdate]):
    def __init__(self):
        super().__init__(model=Api)


api_controller = ApiController()
