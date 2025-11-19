from enum import Enum
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class TamanoProductoEnum(str, Enum):
    pequeno = "pequeño"
    mediano = "mediano"
    grande = "grande"
    extra_grande = "extra_grande"


class ProductoBase(BaseModel):
    nombre: str
    descripcion: str
    precio: float
    categoria_id: int
    disponible: bool = True
    tamano: Optional[TamanoProductoEnum] = None
    ingredientes: Optional[List[str]] = None
    calorias: Optional[int] = None


class ProductoIn(ProductoBase):
    pass


class ProductoOut(ProductoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
