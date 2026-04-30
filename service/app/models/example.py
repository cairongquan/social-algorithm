from pydantic import BaseModel
from typing import Optional

class ExampleBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExampleCreate(ExampleBase):
    pass

class ExampleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ExampleResponse(ExampleBase):
    id: int

    class Config:
        from_attributes = True
