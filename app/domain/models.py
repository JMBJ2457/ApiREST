from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal


class TipoCategoria(Enum):
    BEBIDAS_CALIENTES = "bebidas_calientes"
    BEBIDAS_FRIAS = "bebidas_frias"
    POSTRES = "postres"
    SNACKS = "snacks"
    DESAYUNOS = "desayunos"
    ALMUERZO = "almuerzo"


class TamanoProducto(Enum):
    PEQUENO = "pequeño"
    MEDIANO = "mediano"
    GRANDE = "grande"
    EXTRA_GRANDE = "extra_grande"


@dataclass
class Categoria:
    id: int
    nombre: str
    descripcion: str
    tipo: TipoCategoria
    activa: bool = True

    def __str__(self) -> str:
        return f"{self.nombre} - {self.descripcion}"


@dataclass
class Producto:
    id: int
    nombre: str
    descripcion: str
    precio: Decimal
    categoria_id: int
    disponible: bool = True
    tamano: Optional[TamanoProducto] = None
    ingredientes: Optional[List[str]] = None
    calorias: Optional[int] = None

    def __post_init__(self):
        if self.ingredientes is None:
            self.ingredientes = []
        if self.precio <= 0:
            raise ValueError("El precio debe ser mayor a 0")

    def __str__(self) -> str:
        tamano_str = f" ({self.tamano.value})" if self.tamano else ""
        disponible_str = "✅" if self.disponible else "❌"
        return f"{disponible_str} {self.nombre}{tamano_str} - ${self.precio:.2f}"

    def agregar_ingrediente(self, ingrediente: str) -> None:
        if ingrediente not in self.ingredientes:
            self.ingredientes.append(ingrediente)

    def quitar_ingrediente(self, ingrediente: str) -> None:
        if ingrediente in self.ingredientes:
            self.ingredientes.remove(ingrediente)
