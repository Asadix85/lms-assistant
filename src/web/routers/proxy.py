"""پروکسی معکوس کامل برای عبور از احراز هویت LMS."""

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import urljoin, quote

router = APIRouter()

def _assistant_for_request(request: Request):
    """assistant مربوط به کاربر session فعلی."""
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


@router.get("/jaam-proxy")
async def jaam_proxy(request: Request, url: str):
    """دریافت صفحه HTML و تغییر لینک‌ها به دامنه‌ی خودمان."""
    try:
        assistant = _assistant_for_request(request)
    except PermissionError as e:
        return HTMLResponse(f"<h1>خطای احراز هویت</h1><p>{e}</p>", status_code=401)

    if not assistant or not assistant.is_authenticated:
        return HTMLResponse("<h1>ابتدا در برنامه لاگین کنید.</h1>", status_code=401)

    try:
        logger.info(f"🔄 Proxying page: {url}")
        response = assistant.client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        base_url = str(response.url)

        # 👇 تابع کمکی برای تغییر تمام لینک‌ها
        def rewrite_url(original_href, is_static=False):
            if not original_href:
                return original_href
            # ۱. تبدیل لینک نسبی به مطلق
            full_url = urljoin(base_url, original_href)

            # ۲. اگر لینک مربوط به سامانه LMS بود، آن را به پروکسی خودمان تغییر بده
            if any(d in full_url for d in ["lms4.ui.ac.ir", "lms3.ui.ac.ir", "lms5.ui.ac.ir"]):
                # دقت کن که مسیر روت برای استاتیک و صفحات متفاوت است
                endpoint = "jaam-proxy/static" if is_static else "jaam-proxy"
                return f"/api/{endpoint}?url={quote(full_url, safe='')}"
            return full_url

        # ۱. لینک‌های <a> (لینک‌های ناوبری)
        for tag in soup.find_all('a', href=True):
            tag['href'] = rewrite_url(tag['href'], is_static=False)

        # ۲. لینک‌های <form> (فرم‌ها)
        for tag in soup.find_all('form', action=True):
            tag['action'] = rewrite_url(tag['action'], is_static=False)

        # ۳. فایل‌های CSS (<link>)
        for tag in soup.find_all('link', href=True):
            tag['href'] = rewrite_url(tag['href'], is_static=True)

        # ۴. فایل‌های JS (<script>)
        for tag in soup.find_all('script', src=True):
            tag['src'] = rewrite_url(tag['src'], is_static=True)

        # ۵. تصاویر (<img>)
        for tag in soup.find_all('img', src=True):
            tag['src'] = rewrite_url(tag['src'], is_static=True)

        # ۶. CSSهای درون‌خطی (style="background: url(...)")
        # (این بخش برای پروکسی کردن تصاویر پس‌زمینه است)
        for tag in soup.find_all(style=True):
            if "url(" in tag['style']:
                import re
                # پیدا کردن آدرس داخل url()
                def replace_css_url(match):
                    original_url = match.group(1).strip('\'"')
                    new_url = rewrite_url(original_url, is_static=True)
                    return f"url('{new_url}')"
                tag['style'] = re.sub(r'url\(([^)]+)\)', replace_css_url, tag['style'])

        return HTMLResponse(content=str(soup), status_code=200)

    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return HTMLResponse(f"<h1>خطا در ارتباط با سامانه</h1><p>{e}</p>", status_code=500)


@router.get("/jaam-proxy/static")
async def jaam_static(request: Request, url: str):
    """پروکسی فایل‌های استاتیک (CSS, JS, تصاویر)."""
    try:
        assistant = _assistant_for_request(request)
    except PermissionError:
        return Response("Unauthorized", status_code=401)

    try:
        response = assistant.client.get(url)

        # انتقال هدرهای مهم برای فایل‌های استاتیک (مثل Content-Type)
        headers = {}
        if "content-type" in response.headers:
            headers["Content-Type"] = response.headers["content-type"]

        return Response(
            content=response.content,
            headers=headers,
            status_code=response.status_code
        )
    except Exception as e:
        logger.error(f"Static proxy error: {e}")
        return Response("Error", status_code=500)