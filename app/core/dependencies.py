
# Este archivo es que fábrica las dependencias. 
# Su responsabilidad es construir e inyectar los repositorios 
# adecuados según la configuración del entorno.

# En otras palabras:

# No importa qué implementación concreta utilicemos 
# (MemoryRepository, FileRepository, BD, API, etc.),
# la aplicación solo trabaja con las interfaces 
# IProductoRepository e ICategoriaRepository.

import os
from typing import Tuple

from repositories.memory_repository import (
    ProductoMemoryRepository,
    CategoriaMemoryRepository,
)
from repositories.file_repository import (
    ProductoFileRepository,
    CategoriaFileRepository,
)
from services.menu_service import MenuService
from repositories.interfaces import IProductoRepository, ICategoriaRepository
from core.config import get_settings

def get_repositorios() -> Tuple[IProductoRepository, ICategoriaRepository]:
    settings = get_settings()
    backend = settings.REPO_BACKEND
    if backend == "file" or backend == "archivo":
        return ProductoFileRepository(), CategoriaFileRepository()
    return ProductoMemoryRepository(), CategoriaMemoryRepository()


def get_producto_repo() -> IProductoRepository:
    producto_repo, _ = get_repositorios()
    return producto_repo


def get_categoria_repo() -> ICategoriaRepository:
    _, categoria_repo = get_repositorios()
    return categoria_repo


def get_menu_service() -> MenuService:
    producto_repo, categoria_repo = get_repositorios()
    return MenuService(producto_repo, categoria_repo)
