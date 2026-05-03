"""示例内存服务，实现基础 CRUD。"""

from typing import List, Optional
from app.models.example import ExampleCreate, ExampleUpdate, ExampleResponse

class ExampleService:
    """示例数据服务。"""
    def __init__(self):
        self._items = {}
        self._counter = 1

    async def create(self, data: ExampleCreate) -> ExampleResponse:
        item_id = self._counter
        self._counter += 1
        self._items[item_id] = {"id": item_id, **data.model_dump()}
        return ExampleResponse(**self._items[item_id])

    async def get(self, item_id: int) -> Optional[ExampleResponse]:
        item = self._items.get(item_id)
        return ExampleResponse(**item) if item else None

    async def list_all(self) -> List[ExampleResponse]:
        return [ExampleResponse(**item) for item in self._items.values()]

    async def update(self, item_id: int, data: ExampleUpdate) -> Optional[ExampleResponse]:
        item = self._items.get(item_id)
        if not item:
            return None
        update_data = data.model_dump(exclude_unset=True)
        item.update(update_data)
        return ExampleResponse(**item)

    async def delete(self, item_id: int) -> bool:
        return self._items.pop(item_id, None) is not None

example_service = ExampleService()
