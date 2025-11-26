from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from models import (
    PacienteBase, AlergiaBase, EnfermedadBase, 
    Paciente, Alergia, Enfermedad, 
    PacienteCreate, PacienteResponse,
    PacienteAlergiaLink, PacienteEnfermedadLink,
)
from auth import Usuario
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from db import init_db, get_session
from datetime import timedelta

# Importar funciones de autenticación
from auth import (
    crear_access_token, autenticar_usuario, obtener_password_hash,
    obtener_usuario_activo_actual, ACCESS_TOKEN_EXPIRE_MINUTES,
    Token, UsuarioCreate, UsuarioResponse
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# --------------------------
# ENDPOINTS DE AUTENTICACIÓN
# --------------------------

@app.post("/registro", response_model=UsuarioResponse)
async def registrar_usuario(
    usuario_data: UsuarioCreate,
    session: Session = Depends(get_session)
):
    """Registra un nuevo usuario"""
    # Verificar si el usuario ya existe
    statement = select(Usuario).where(Usuario.username == usuario_data.username)
    usuario_existente = session.exec(statement).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Verificar si el email ya existe
    statement = select(Usuario).where(Usuario.email == usuario_data.email)
    email_existente = session.exec(statement).first()
    if email_existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear nuevo usuario
    usuario = Usuario(
        username=usuario_data.username,
        email=usuario_data.email,
        hashed_password=obtener_password_hash(usuario_data.password),
        activo=True
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    
    return UsuarioResponse(
        usuarioID=usuario.usuarioID if usuario.usuarioID else 0,
        username=usuario.username,
        email=usuario.email,
        activo=usuario.activo
    )

@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """Endpoint de login que devuelve un token JWT"""
    usuario = autenticar_usuario(session, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crear_access_token(
        data={"sub": usuario.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/usuarios/me", response_model=UsuarioResponse)
async def leer_usuario_actual(
    usuario_actual: Usuario = Depends(obtener_usuario_activo_actual)
):
    """Obtiene la información del usuario actual"""
    return UsuarioResponse(
        usuarioID=usuario_actual.usuarioID if usuario_actual.usuarioID else 0,
        username=usuario_actual.username,
        email=usuario_actual.email,
        activo=usuario_actual.activo
    )

# --------------------------
# ENDPOINTS DE PACIENTES (PROTEGIDOS)
# --------------------------

@app.post("/paciente", response_model=PacienteResponse)
async def create_paciente(
    paciente_data: PacienteCreate,
    session: Session = Depends(get_session),
    usuario_actual: Usuario = Depends(obtener_usuario_activo_actual)  # Protegido por JWT
):
    """Crea un paciente con sus alergias y enfermedades (requiere autenticación)"""
    try:
        # Crear paciente
        paciente = Paciente(
            sNombre=paciente_data.sNombre,
            sApellido=paciente_data.sApellido, 
            dFechaNacimiento=paciente_data.dFechaNacimiento, 
            eSexo=paciente_data.eSexo
        )
        session.add(paciente)
        session.flush()

        alergias_list = []
        enfermedades_list = []

        # Crear alergias y enlaces
        if paciente_data.alergias:
            for alergia_data in paciente_data.alergias:
                alergia = Alergia(
                    sTitulo=alergia_data.sTitulo,
                    sDescripcion=alergia_data.sDescripcion
                )
                session.add(alergia)
                session.flush()
                
                # Crear enlace - verificar que los IDs existan
                if paciente.pacienteID is not None and alergia.alergiaID is not None:
                    link = PacienteAlergiaLink(
                        pacienteID=paciente.pacienteID,
                        alergiaID=alergia.alergiaID
                    )
                    session.add(link)
                
                alergias_list.append(AlergiaBase(
                    sTitulo=alergia.sTitulo,
                    sDescripcion=alergia.sDescripcion
                ))
        
        # Crear enfermedades y enlaces
        if paciente_data.enfermedades:
            for enfermedad_data in paciente_data.enfermedades:
                enfermedad = Enfermedad(
                    sTitulo=enfermedad_data.sTitulo,
                    sDescripcion=enfermedad_data.sDescripcion
                )
                session.add(enfermedad)
                session.flush()
                
                # Crear enlace - verificar que los IDs existan
                if paciente.pacienteID is not None and enfermedad.enfermedadID is not None:
                    link = PacienteEnfermedadLink(
                        pacienteID=paciente.pacienteID,
                        enfermedadID=enfermedad.enfermedadID
                    )
                    session.add(link)
                
                enfermedades_list.append(EnfermedadBase(
                    sTitulo=enfermedad.sTitulo,
                    sDescripcion=enfermedad.sDescripcion
                ))

        session.commit()
        
        return PacienteResponse(
            pacienteID=paciente.pacienteID if paciente.pacienteID is not None else 0,
            sNombre=paciente.sNombre,
            sApellido=paciente.sApellido,
            dFechaNacimiento=paciente.dFechaNacimiento,
            eSexo=paciente.eSexo,
            alergias=alergias_list,
            enfermedades=enfermedades_list
        )
    
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/pacientes", response_model=list[PacienteResponse])
async def get_pacientes(
    session: Session = Depends(get_session),
    usuario_actual: Usuario = Depends(obtener_usuario_activo_actual)  # Protegido por JWT
):
    """Obtiene todos los pacientes con sus alergias y enfermedades (requiere autenticación)"""
    try:
        # Obtener todos los pacientes
        pacientes = session.exec(select(Paciente)).all()
        
        resultado = []
        for paciente in pacientes:
            # Obtener alergias del paciente
            alergia_links = session.exec(
                select(PacienteAlergiaLink).where(
                    PacienteAlergiaLink.pacienteID == paciente.pacienteID
                )
            ).all()
            
            alergias = []
            for link in alergia_links:
                alergia = session.get(Alergia, link.alergiaID)
                if alergia:
                    alergias.append(AlergiaBase(
                        sTitulo=alergia.sTitulo,
                        sDescripcion=alergia.sDescripcion
                    ))
            
            # Obtener enfermedades del paciente
            enfermedad_links = session.exec(
                select(PacienteEnfermedadLink).where(
                    PacienteEnfermedadLink.pacienteID == paciente.pacienteID
                )
            ).all()
            
            enfermedades = []
            for link in enfermedad_links:
                enfermedad = session.get(Enfermedad, link.enfermedadID)
                if enfermedad:
                    enfermedades.append(EnfermedadBase(
                        sTitulo=enfermedad.sTitulo,
                        sDescripcion=enfermedad.sDescripcion
                    ))
            
            resultado.append(PacienteResponse(
                pacienteID=paciente.pacienteID if paciente.pacienteID is not None else 0,
                sNombre=paciente.sNombre,
                sApellido=paciente.sApellido,
                dFechaNacimiento=paciente.dFechaNacimiento,
                eSexo=paciente.eSexo,
                alergias=alergias,
                enfermedades=enfermedades
            ))
        
        return resultado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")