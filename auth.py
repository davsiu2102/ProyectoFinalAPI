from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from pydantic import BaseModel
from db import get_session
from models import Usuario

# Configuración JWT
SECRET_KEY = "tu_clave_secreta_super_segura_cambiala_en_produccion"  # ¡CAMBIAR EN PRODUCCIÓN!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuración de encriptación de contraseñas
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --------------------------
# ESQUEMAS PYDANTIC
# --------------------------

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UsuarioCreate(BaseModel):
    username: str
    email: str
    password: str

class UsuarioResponse(BaseModel):
    usuarioID: int
    username: str
    email: str
    activo: bool

# --------------------------
# FUNCIONES DE UTILIDAD
# --------------------------

def obtener_password_hash(password: str) -> str:
    """Genera el hash de una contraseña"""
    return pwd_context.hash(password)

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash"""
    return pwd_context.verify(plain_password, hashed_password)

def crear_access_token(data: dict, expires_delta: timedelta | None = None):
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def obtener_usuario_por_username(session: Session, username: str) -> Usuario | None:
    """Obtiene un usuario por su username"""
    from sqlmodel import select
    statement = select(Usuario).where(Usuario.username == username)
    usuario = session.exec(statement).first()
    return usuario

def autenticar_usuario(session: Session, username: str, password: str) -> Usuario | None:
    """Autentica un usuario verificando username y contraseña"""
    usuario = obtener_usuario_por_username(session, username)
    if not usuario:
        return None
    if not verificar_password(password, usuario.hashed_password):
        return None
    return usuario

async def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)  # Reemplazar con get_session
) -> Usuario:
    """Obtiene el usuario actual desde el token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    if token_data.username is None:
        raise credentials_exception
    
    usuario = obtener_usuario_por_username(session, username=token_data.username)
    if usuario is None:
        raise credentials_exception
    return usuario

async def obtener_usuario_activo_actual(
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
) -> Usuario:
    """Verifica que el usuario actual esté activo"""
    if not usuario_actual.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return usuario_actual