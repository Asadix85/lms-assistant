"""مدل و داده‌های مکان‌های دانشگاه اصفهان."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class CampusLocation:
    name: str           # نام دانشکده / سالن
    building: str       # نام ساختمان (نمایش به کاربر)
    lat: float          # عرض جغرافیایی
    lng: float          # طول جغرافیایی


# ⚠️ ترتیب کلیدواژه‌ها بسیار مهم است:
# کلمات خاص‌تر باید بالاتر باشند تا با کلمات عمومی‌تر تداخل نکنند.
UI_LOCATIONS: dict[str, CampusLocation] = {
    # --- دانشکده فنی و مهندسی ---
    "انصاری": CampusLocation(
        name="دانشکده فنی و مهندسی (انصاری)",
        building="ساختمان فنی مهندسی انصاری",
        lat=32.603250,
        lng=51.657516,
    ),
    "فني قديم": CampusLocation(
        name="دانشکده فنی و مهندسی",
        building="ساختمان فنی قدیم",
        lat=32.601595,
        lng=51.658739,
    ),
    "مجتمع کلاس": CampusLocation(
        name="دانشکده فنی و مهندسی",
        building="مجتمع کلاس‌ها",
        lat=32.601595,
        lng=51.658739,
    ),
    "فني": CampusLocation(
        name="دانشکده فنی و مهندسی",
        building="ساختمان فنی",
        lat=32.601704,
        lng=51.658592,
    ),

    # --- دانشکده علوم اداری و اقتصاد ---
    "اقتصاد جدید": CampusLocation(
        name="دانشکده علوم اداری و اقتصاد",
        building="ساختمان علوم اداری و اقتصاد",
        lat=32.598350,
        lng=51.657270,
    ),
    "اقتصاد قدیم": CampusLocation(
        name="ساختمان قديم اقتصاد",
        building="ساختمان قديم اقتصاد",
        lat=32.600555,
        lng=51.658691,
    ),

    # --- سایر دانشکده‌ها ---
    "فیزیک": CampusLocation(
        name="دانشکده فیزیک",
        building="ساختمان فیزیک",
        lat=32.604334,
        lng=51.660526,
    ),
    "شیمی": CampusLocation(
        name="دانشکده شیمی",
        building="ساختمان شیمی",
        lat=32.604546,
        lng=51.659560,
    ),
    "ریاضی": CampusLocation(
        name="دانشکده ریاضی و آمار",
        building="ساختمان ریاضی و آمار",
        lat=32.605536,
        lng=51.660958,
    ),
    "الهیات": CampusLocation(
        name="دانشکده الهیات و معارف اهل البیت",
        building="ساختمان معارف و الهیات",
        lat=32.612474,
        lng=51.659174,
    ),
    "علوم پایه": CampusLocation(
        name="دانشکده علوم پایه",
        building="مجتمع علوم پایه",
        lat=32.606512,
        lng=51.657890,
    ),

    # --- سالن‌ها ---
    "حجاب": CampusLocation(
        name="سالن حجاب",
        building="سالن حجاب",
        lat=32.618984,
        lng=51.662382,
    ),
    "بهرامیان": CampusLocation( # 👈 کلیدواژه را کوتاه کردیم تا "شهید بهرامیان" هم پیدا شود
        name="سالن شهید بهرامیان",
        building="سالن شهید بهرامیان",
        lat=32.621082,
        lng=51.663825,
    ),
    "نیلفروش": CampusLocation( # 👈 کلیدواژه را کوتاه کردیم
        name="سالن نیلفروش زاده",
        building="سالن نیلفروش زاده",
        lat=32.620113,
        lng=51.663310,
    ),
}


def get_location(text: str) -> CampusLocation | None:
    """جستجوی هوشمند مکان بر اساس تطبیق کلیدواژه."""
    if not text:
        return None

    # ۱. نرمال‌سازی: تبدیل حروف عربی به فارسی و حذف نیم‌فاصله
    norm_text = text.replace("ي", "ی").replace("ك", "ک").replace("\u200c", " ").strip()

    # ۲. جستجو در دیکشنری (از بالا به پایین)
    for key, loc in UI_LOCATIONS.items():
        norm_key = key.replace("ي", "ی").replace("ك", "ک")
        norm_name = loc.name.replace("ي", "ی").replace("ك", "ک")
        norm_building = loc.building.replace("ي", "ی").replace("ك", "ک")

        # اگر کلیدواژه یا نام یا ساختمان در متن کلاس پیدا شد
        if norm_key in norm_text or norm_name in norm_text or norm_building in norm_text:
            return loc

    return None