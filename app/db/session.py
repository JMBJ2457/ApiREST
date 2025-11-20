"""
Configuración de la sesión de base de datos SQLite
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from core.config import get_settings
import os

settings = get_settings()

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cafeteria.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Crear engine con configuración para SQLite
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # Necesario para SQLite en threads
    poolclass=StaticPool,
    echo=False  # Cambiar a True para ver las queries SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency para obtener una sesión de base de datos.
    Usar con FastAPI Depends()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa las tablas en la base de datos"""
    from db.models import Base
    Base.metadata.create_all(bind=engine)

