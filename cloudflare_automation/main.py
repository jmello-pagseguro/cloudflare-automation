from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_303_SEE_OTHER

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="sua-chave-secreta")

# ---------- Utilitários ----------

def login_user(request: Request, username: str):
    request.session["user"] = username

def logout_user(request: Request):
    request.session.pop("user", None)

def set_flash(request: Request, message: str, category: str):
    request.session["flash_message"] = message
    request.session["flash_category"] = category

def get_flash(request: Request):
    message = request.session.pop("flash_message", None)
    category = request.session.pop("flash_category", None)
    return message, category

def is_authenticated(request: Request):
    return "user" in request.session

# ---------- Rotas ----------

@app.get("/")
async def index(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

    flash_message, flash_category = get_flash(request)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": request.session.get("user"),
        "flash_message": flash_message,
        "flash_category": flash_category
    })


@app.get("/login")
async def login(request: Request):
    flash_message, flash_category = get_flash(request)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "flash_message": flash_message,
        "flash_category": flash_category
    })


@app.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin":
        login_user(request, username)
        return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)
    else:
        set_flash(request, "Credenciais inválidas", "error")
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)


@app.post("/logout")
async def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)


@app.get("/purge_cache")
async def purge_cache(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

    flash_message, flash_category = get_flash(request)
    return templates.TemplateResponse("purge_cache.html", {
        "request": request,
        "user": request.session.get("user"),
        "flash_message": flash_message,
        "flash_category": flash_category
    })


@app.post("/purge_cache")
async def purge_cache_post(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

    form = await request.form()
    hosts = form.get("hosts", "").split(",")

    print(f"Hosts a serem purgados: {hosts}")

    set_flash(request, "Cache purgado com sucesso!", "success")
    return RedirectResponse("/purge_cache", status_code=HTTP_303_SEE_OTHER)
