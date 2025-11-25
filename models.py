# configuración de FastAPI con SQLModel para manejar una base de datos SQLite dentro de este mismo archivo

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import date
from enum import Enum

app = FastAPI() # instanciar FastAPI

# --------------------------
# OBJETOS BASE (INTERNOS)
# --------------------------

# clase de sexo
class Sexo(str, Enum):
    masculino = "masculino"
    femenino = "femenino"
    otro = "otro"

# clase base de paciente
class PacienteBase (SQLModel):
    sNombre: str
    sApellido: str
    dFechaNacimiento: date
    eSexo: Sexo

# clase base de alergia
class AlergiaBase (SQLModel):
    sTitulo: str
    sDescripcion: str | None = None # nulleable

class EnfermedadBase (SQLModel):
    sTitulo: str
    sDescripcion: str | None = None

# --------------------------
# TABLAS LINK (MUCHOS A MUCHOS)
# --------------------------

# objetos de tabla muchos a muchos paciente-alergia
class PacienteAlergiaLink (SQLModel, table=True):
    pacienteID: int | None = Field(default=None, foreign_key="paciente.pacienteID", primary_key=True)
    alergiaID: int | None = Field(default=None, foreign_key="alergia.alergiaID", primary_key=True)

# objetos de tabla muchos a muchos paciente-enfermedad
class PacienteEnfermedadLink (SQLModel, table=True):
    pacienteID: int | None = Field(default=None, foreign_key="paciente.pacienteID", primary_key=True)
    enfermedadID: int | None = Field(default=None, foreign_key="enfermedad.enfermedadID", primary_key=True)

# --------------------------
# TABLAS PRINCIPALES
# --------------------------

# objetos de la tabla SQL de pacientes
class Paciente (PacienteBase, table=True):
    pacienteID: int = Field(default=None, primary_key=True)

    # relación con alergias lógica interna: no crea una columna en la tabla de pacientes sino que SQLModel generará las filas correspondientes en la tabla link
    alergias: list["Alergia"] | None = Relationship(
        back_populates="pacientes",
        link_model=PacienteAlergiaLink
        )
    
    # relación con enfermedades
    enfermedades: list["Enfermedad"] | None = Relationship(
        back_populates="pacientes",
        link_model=PacienteEnfermedadLink
        )

# objetos de la tabla SQL de alergias
class Alergia (AlergiaBase, table=True):
    alergiaID: int = Field(default=None, primary_key=True)

    # relación con pacientes
    pacientes: list["Paciente"] | None = Relationship(
        back_populates="alergias",
        link_model=PacienteAlergiaLink
    )

# objetos de la tabla SQL de enfermedades
class Enfermedad (EnfermedadBase, table=True):
    enfermedadID: int = Field(default=None, primary_key=True)

    # relación con pacientes
    pacientes: list["Paciente"] | None = Relationship(
        back_populates="enfermedades",
        link_model=PacienteEnfermedadLink
    )