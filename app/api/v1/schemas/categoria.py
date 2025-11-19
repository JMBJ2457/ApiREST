from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TipoCategoriaEnum(str, Enum):
    bebidas_calientes = "bebidas_calientes"
    bebidas_frias = "bebidas_frias"
    postres = "postres"
    snacks = "snacks"
    desayunos = "desayunos"
    almuerzo = "almuerzo"


class CategoriaBase(BaseModel):
    nombre: str
    descripcion: str
    tipo: TipoCategoriaEnum
    activa: bool = True


class CategoriaIn(CategoriaBase):
    pass


class CategoriaOut(CategoriaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
