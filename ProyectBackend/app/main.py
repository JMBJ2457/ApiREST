# Importamos las librerías necesarias
from fastapi import FastAPI, Depends, HTTPException  # FastAPI para crear la app y manejar rutas HTTP
from pydantic import BaseModel  # Pydantic para definir modelos de datos y validaciones
from sqlalchemy import create_engine, Column, Integer, String  # SQLAlchemy para definir la base de datos
from sqlalchemy.orm import sessionmaker, declarative_base, Session  # sessionmaker para gestionar sesiones y declarative_base para definir el modelo base
from sqlalchemy.future import select  # Se usa para realizar consultas asincrónicas (en caso de ser necesario en un futuro)

# Configuración de la base de datos
DATABASE_URL = "sqlite:///./test.db"  # Utilizamos SQLite para facilitar el desarrollo, pero puedes cambiar a PostgreSQL o MySQL según necesites
# Creamos el motor de la base de datos, SQLite en este caso, y especificamos los argumentos necesarios para su conexió
