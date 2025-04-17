from fastapi import FastAPI, Request, Form, APIRouter
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from fastapi.templating import Jinja2Templates
from core.auth import authenticate_user
from core.logger import Logger
from libraries.cloudflare import Cloudflare

templates = Jinja2Templates(directory="templates")

router = APIRouter()
log = Logger(__name__).get_logger()

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

@router.get("/")
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


@router.get("/login")
async def login(request: Request):
    flash_message, flash_category = get_flash(request)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "flash_message": flash_message,
        "flash_category": flash_category
    })


@router.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if authenticate_user(username, password):
        login_user(request, username)
        return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)
    else:
        set_flash(request, "Credenciais inválidas", "error")
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)


@router.post("/logout")
async def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)


@router.get("/purge_cache")
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


@router.post("/purge_cache")
async def purge_cache_post(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

    form = await request.form()

    user = request.session.get("user")
    
    hosts = form.get("hosts", "").split(",")

    log.info(f"Hosts a serem purgados: {hosts}")

    cloudflare = Cloudflare()

    result = await cloudflare.purge_cache(hosts)

    if(result["success"]):
        log.info(f"Cache purgado com sucesso para os hosts: {hosts}")
        set_flash(request, "Cache purgado com sucesso!", "success")
    else:
        log.error(f"Erro ao purgar cache para os hosts: {hosts}")
        set_flash(request, f"Erro ao purgar cache: {result['error']}", "error")
    return RedirectResponse("/purge_cache", status_code=HTTP_303_SEE_OTHER)
