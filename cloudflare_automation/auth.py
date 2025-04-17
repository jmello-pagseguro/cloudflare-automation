import os
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request

# JWT config
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Simulação de banco de usuários
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "password": "admin",  # Em produção, use hashes!
        "full_name": "Administrador Fictício",
    },
    "joao": {
        "username": "joao",
        "password": "teste123",
        "full_name": "João Vitor Teste",
    },
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate_user(username: str, password: str) -> bool:
    user = FAKE_USERS_DB.get(username)
    if user and user["password"] == password:
        return True
    return False

def create_jwt_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(token: str = Depends(oauth2_scheme)):
    username = verify_jwt_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Usuário não autenticado")
    return username
