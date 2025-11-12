from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..core.config import settings

templates = Jinja2Templates(directory=str(settings.template_dir.resolve()))
templates.env.globals["static_version"] = settings.static_version
router = APIRouter(include_in_schema=False)
view_router = router


@router.get("/", include_in_schema=False)
async def landing():
    return RedirectResponse(url="/login", status_code=302)


@router.get("/app", response_class=HTMLResponse, name="index")
async def app_home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "amap_api_key": settings.amap_api_key,
            "speech_provider": settings.speech_provider,
            "llm_provider": settings.llm_provider,
        },
    )


@router.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(
    request: Request,
    registered: str | None = Query(default=None),
    email: str | None = Query(default=None),
):
    registered_flag = False
    if registered is not None:
        registered_flag = registered.lower() in {"1", "true", "yes", "on"}
    flash_message = "注册成功，请登录" if registered_flag else None
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "flash_message": flash_message,
            "prefill_email": email or "",
        },
    )


@router.get("/register", response_class=HTMLResponse, name="register_page")
async def register_page(request: Request, email: str | None = Query(default=None)):
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "prefill_email": email or "",
        },
    )


@router.get("/settings", response_class=HTMLResponse, name="settings_page")
async def settings_page(request: Request):
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "speech_provider": settings.speech_provider, "llm_provider": settings.llm_provider},
    )
