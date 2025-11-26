from __future__ import annotations
from fastapi import FastAPI
from sqlmodel import SQLModel, Field
from datetime import date
from enum import Enum

app = FastAPI()

# --------------------------
# OBJETOS BASE (INTERNOS)
# --------------------------

class Sexo(str, Enum):
    masculino = "masculino"
    femenino = "femenino"
    otro = "otro"

class PacienteBase(SQLModel):
    sNombre: str
    sApellido: str
    dFechaNacimiento: date
    eSexo: Sexo

class AlergiaBase(SQLModel):
    sTitulo: str
    sDescripcion: str | None = Field(default=None, nullable=True)

class EnfermedadBase(SQLModel):
    sTitulo: str
    sDescripcion: str | None = Field(default=None, nullable=True)

class Usuario(SQLModel, table=True):
    usuarioID: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    activo: bool = Field(default=True)
    
# --------------------------
# TABLAS LINK (MUCHOS A MUCHOS)
# --------------------------

class PacienteAlergiaLink(SQLModel, table=True):
    pacienteID: int = Field(foreign_key="paciente.pacienteID", primary_key=True)
    alergiaID: int = Field(foreign_key="alergia.alergiaID", primary_key=True)

class PacienteEnfermedadLink(SQLModel, table=True):
    pacienteID: int = Field(foreign_key="paciente.pacienteID", primary_key=True)
    enfermedadID: int = Field(foreign_key="enfermedad.enfermedadID", primary_key=True)

# --------------------------
# TABLAS PRINCIPALES (SIN RELACIONES)
# --------------------------

class Paciente(PacienteBase, table=True):
    pacienteID: int | None = Field(default=None, primary_key=True)

class Alergia(AlergiaBase, table=True):
    alergiaID: int | None = Field(default=None, primary_key=True)

class Enfermedad(EnfermedadBase, table=True):
    enfermedadID: int | None = Field(default=None, primary_key=True)

# --------------------------
# ESQUEMAS DE CREACIÓN
# --------------------------

class PacienteCreate(PacienteBase):
    alergias: list[AlergiaBase] | None = None
    enfermedades: list[EnfermedadBase] | None = None

# --------------------------
# OBJETO DE RESPUESTA
# --------------------------

class PacienteResponse(PacienteBase):
    pacienteID: int
    alergias: list[AlergiaBase] = []
    enfermedades: list[EnfermedadBase] = []