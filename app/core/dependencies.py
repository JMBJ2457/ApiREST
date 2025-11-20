
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
from sqlalchemy.orm import Session

from repositories.memory_repository import (
    ProductoMemoryRepository,
    CategoriaMemoryRepository,
)
from repositories.file_repository import (
    ProductoFileRepository,
    CategoriaFileRepository,
)
from repositories.database_repository import (
    ProductoDatabaseRepository,
    CategoriaDatabaseRepository,
)
from services.menu_service import MenuService
from repositories.interfaces import IProductoRepository, ICategoriaRepository
from core.config import get_settings
from db.session import get_db

def get_repositorios(db: Session = None) -> Tuple[IProductoRepository, ICategoriaRepository]:
    settings = get_settings()
    backend = settings.REPO_BACKEND
    
    if backend == "database":
        if db is None:
            # Si no se proporciona db, crear una nueva sesión
            from db.session import SessionLocal
            db = SessionLocal()
        return ProductoDatabaseRepository(db), CategoriaDatabaseRepository(db)
    elif backend == "file" or backend == "archivo":
        return ProductoFileRepository(), CategoriaFileRepository()
    else:
        return ProductoMemoryRepository(), CategoriaMemoryRepository()


def get_producto_repo(db: Session = None) -> IProductoRepository:
    producto_repo, _ = get_repositorios(db)
    return producto_repo


def get_categoria_repo(db: Session = None) -> ICategoriaRepository:
    _, categoria_repo = get_repositorios(db)
    return categoria_repo


def get_menu_service() -> MenuService:
    """
    Obtiene el servicio de menú con los repositorios apropiados.
    Si REPO_BACKEND=database, crea una nueva sesión automáticamente.
    """
    from core.config import get_settings
    settings = get_settings()
    
    db = None
    if settings.REPO_BACKEND == "database":
        from db.session import SessionLocal
        db = SessionLocal()
    
    producto_repo, categoria_repo = get_repositorios(db)
    return MenuService(producto_repo, categoria_repo)
