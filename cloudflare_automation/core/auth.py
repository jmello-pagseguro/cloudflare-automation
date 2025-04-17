import os,re
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request
from ldap3 import ALL, NTLM, Connection, Server
from .logger import Logger

# JWT config
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
LDAP_SERVER = os.getenv("LDAP_HOST")
LDAP_PORT = 389
BASE_DN = os.getenv("LDAP_BASE_DN")
USER_DOMAIN = os.getenv("LDAP_DOMAIN")
GROUPS_PERMITED = os.getenv("LDAP_GROUPS_PERMITED").split(",")
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
log = Logger(__name__).get_logger()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate_user(username: str, password: str) -> bool:
    try:

        server_uri = f"{LDAP_SERVER}:{LDAP_PORT}"
        server = Server(server_uri, get_info=ALL)
        connection = Connection(
            server,
            user=f'{USER_DOMAIN}\\{username}',
            password=password,
            authentication=NTLM
        )
        if connection.bind():

            user_data = {
                "name": "",
                "username": username,
                "member_of": []
            }

            connection.search(search_base=BASE_DN,
            search_filter=f"(sAMAccountName={username})",
            attributes=["*"])

            for member_of in connection.response[0]['attributes']['memberOf']:
                group_name = re.search("CN=([A-Z|a-z|_|-]{1,})", member_of)
                if group_name:
                    user_data["member_of"].append(group_name.group(1))
                else:
                    log.info("Nao tem grupo")

            user_data["name"] = connection.response[0]['attributes']['displayName']
            for group_p in GROUPS_PERMITED:
                if group_p in user_data["member_of"]:
                    return True

            log.error(f"Usuario: {username} nao esta nos grupos do AD que permitem o acesso ao sistema.")
            return False
        else:
            log.error("Nao foi possivel autenticar no AD, verifique se o usuario e senha foram digitados corretamente.")
            return False

    except Exception as error:
        log.error(f"Ocorreu um erro com a conexao do AD: {LDAP_SERVER}:{LDAP_PORT}")
        log.error(error)
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
