from fastapi import FastAPI
from routers import web
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="sua-chave-secreta")

app.include_router(web.router, tags=["web"])