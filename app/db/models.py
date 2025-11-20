"""
Modelos SQLAlchemy para la base de datos
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from decimal import Decimal

Base = declarative_base()


class CategoriaModel(Base):
    """Modelo de base de datos para Categoria"""
    __tablename__ = "categorias"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    tipo = Column(String(50), nullable=False, index=True)  # TipoCategoria enum value
    activa = Column(Boolean, default=True, nullable=False)
    
    # Relación con productos
    productos = relationship("ProductoModel", back_populates="categoria")


class ProductoModel(Base):
    """Modelo de base de datos para Producto"""
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    precio = Column(Float, nullable=False)  # Usamos Float, convertimos a Decimal después
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False, index=True)
    disponible = Column(Boolean, default=True, nullable=False)
    tamano = Column(String(20), nullable=True)  # TamanoProducto enum value o None
    ingredientes = Column(JSON, nullable=True)  # Lista de strings como JSON
    calorias = Column(Integer, nullable=True)
    
    # Relación con categoría
    categoria = relationship("CategoriaModel", back_populates="productos")

