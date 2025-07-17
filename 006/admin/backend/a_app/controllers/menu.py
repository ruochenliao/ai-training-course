from typing import Optional

from a_app.core.crud import CRUDBase
from a_app.models.admin import Menu
from a_app.schemas.menus import MenuCreate, MenuUpdate


class MenuController(CRUDBase[Menu, MenuCreate, MenuUpdate]):
    def __init__(self):
        super().__init__(model=Menu)

    async def get_by_menu_path(self, path: str) -> Optional["Menu"]:
        return await self.model.filter(path=path).first()


menu_controller = MenuController()
