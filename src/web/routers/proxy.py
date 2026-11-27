"""پروکسی معکوس LMS — فقط میزبان‌های مجاز (ضد SSRF)."""
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import urljoin, quote, urlparse
import re

router = APIRouter()

ALLOWED_HOSTS = {"lms3.ui.ac.ir", "lms4.ui.ac.ir", "lms5.ui.ac.ir"}
MAX_STATIC_BYTES = 20 * 1024 * 1024
SAFE_STATIC_PREFIXES = (
    "text/css", "application/javascript", "text/javascript",
    "image/", "font/", "application/font", "application/octet-stream",
)


def _check_url(url: str) -> None:
    """فقط http(s) و فقط میزبان‌های LMS دانشگاه."""
    p = urlparse(url or "")
    if p.scheme not in ("http", "https"):
        raise HTTPException(400, "پروتکل لینک مجاز نیست")
    if (p.hostname or "").lower() not in ALLOWED_HOSTS:
        raise HTTPException(403, "این میزبان در فهرست مجاز نیست")


def _assistant_for_request(request: Request):
    from src.storage.repositories.user_repo import UserRepository
    from src.web.security import SESSION_COOKIE_NAME

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise PermissionError("وارد نشده‌اید")
    user = UserRepository(request.app.state.db).get_user_by_token(token)
    if not user:
        raise PermissionError("نشست منقضی شده است")
    sm = request.app.state.session
    sm.set_active_user(user["id"])
    return sm.get_assistant(user["id"])


def _err_page(msg: str, code: int) -> HTMLResponse:
    return HTMLResponse(
        f"<h1>درخواست مجاز نیست</h1><p>{msg}</p>",
        status_code=code,
        headers={"X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer"},
    )


@router.get("/jaam-proxy")
async def jaam_proxy(request: Request, url: str):
    """دریافت صفحهٔ HTML از LMS و بازنویسی لینک‌ها به دامنهٔ خودمان."""
    try:
        assistant = _assistant_for_request(request)
    except PermissionError as e:
        return _err_page(str(e), 401)
    if not assistant or not assistant.is_authenticated:
        return _err_page("ابتدا در برنامه لاگین کنید.", 401)

    try:
        _check_url(url)
    except HTTPException as e:
        logger.warning("proxy blocked url host: {}", urlparse(url).hostname)
        return _err_page(e.detail, e.status_code)

    try:
        response = assistant.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        base_url = str(response.url)

        def rewrite_url(original_href, is_static=False):
            if not original_href:
                return original_href
            full_url = urljoin(base_url, original_href)
            # مقایسهٔ دقیق hostname (نه substring) تا هاست جعلی رد شود
            if (urlparse(full_url).hostname or "").lower() in ALLOWED_HOSTS:
                endpoint = "jaam-proxy/static" if is_static else "jaam-proxy"
                return f"/api/{endpoint}?url={quote(full_url, safe='')}"
            return full_url

        for tag in soup.find_all("a", href=True):
            tag["href"] = rewrite_url(tag["href"], is_static=False)
        for tag in soup.find_all("form", action=True):
            tag["action"] = rewrite_url(tag["action"], is_static=False)
        for tag in soup.find_all("link", href=True):
            tag["href"] = rewrite_url(tag["href"], is_static=True)
        for tag in soup.find_all("script", src=True):
            tag["src"] = rewrite_url(tag["src"], is_static=True)
        for tag in soup.find_all("img", src=True):
            tag["src"] = rewrite_url(tag["src"], is_static=True)

        def replace_css_url(match):
            original_url = match.group(1).strip("'\"")
            return f"url('{rewrite_url(original_url, is_static=True)}')"

        for tag in soup.find_all(style=True):
            if "url(" in tag["style"]:
                tag["style"] = re.sub(r"url\(([^)]+)\)", replace_css_url, tag["style"])

        return HTMLResponse(
            content=str(soup),
            status_code=200,
            headers={
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
            },
        )
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return _err_page("خطا در ارتباط با سامانه", 500)


@router.get("/jaam-proxy/static")
async def jaam_static(request: Request, url: str):
    """پروکسی CSS/JS/تصویر/فونت — هرگز HTML سرو نمی‌کند."""
    try:
        assistant = _assistant_for_request(request)
    except PermissionError:
        return Response("Unauthorized", status_code=401)

    try:
        _check_url(url)
    except HTTPException as e:
        return Response(e.detail, status_code=e.status_code)

    try:
        response = assistant.client.get(url)
        ct = (response.headers.get("content-type") or "").split(";")[0].strip().lower()

        if "html" in ct:
            logger.warning("static proxy refused HTML from {}", urlparse(url).hostname)
            return Response("HTML از این مسیر مجاز نیست", status_code=403)
        if ct and not ct.startswith(SAFE_STATIC_PREFIXES):
            return Response("نوع فایل مجاز نیست", status_code=415)
        if len(response.content) > MAX_STATIC_BYTES:
            return Response("فایل بیش از حد بزرگ است", status_code=413)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers={
                "Content-Type": ct or "application/octet-stream",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "private, max-age=3600",
            },
        )
    except Exception as e:
        logger.error(f"Static proxy error: {e}")
        return Response("Error", status_code=500)