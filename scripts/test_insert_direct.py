"""تست درج مستقیم یک Assignment با متن طولانی."""

from src.models.assignment import Assignment
from src.storage.database import Database
from src.storage.repositories import AssignmentRepository


# متن طولانی (کپی از LMS)
LONG_TITLE = "تکلیف 1- کاربردهای  سیستم های  مرتبه صفر -انتگرالگیر-مشتق گیر-مرتبه اول -مرتبه دوم در صنعت و جامعه را بنویسید"
print(f"طول ورودی: {len(LONG_TITLE)}")


with Database("data/test_long.db") as db:
    db.init_schema()

    # درس رو بساز (چون FK داریم)
    from src.models.course import Course, CourseStatus
    from src.storage.repositories import CourseRepository

    course = Course(
        id="139710",
        name="مدارهای الکتریکی و الکترونیکی",
        url="https://lms4.ui.ac.ir/group/139710",
        group_id="139710",
        domain="lms4",
        status=CourseStatus.ACTIVE,
    )
    CourseRepository(db).save(course)

    # Assignment بساز
    a = Assignment(
        id="test_long_title",
        course_id="139710",
        title=LONG_TITLE,
        description="تست",
    )

    print(f"طول بعد از ساخت Assignment: {len(a.title)}")

    # ذخیره کن
    repo = AssignmentRepository(db)
    repo.save(a)

    # بخون
    loaded = repo.get_by_id("test_long_title")
    print(f"طول بعد از خوندن از DB: {len(loaded.title)}")
    print(f"\nمتن خوندن‌شده:")
    print(f"  {loaded.title!r}")

    # مقایسه
    if loaded.title == LONG_TITLE:
        print("\n✅ متن کامل ذخیره و بازیابی شد")
    else:
        print("\n❌ متن ناقص شد")
        print(f"  انتظار: {len(LONG_TITLE)} کاراکتر")
        print(f"  دریافت: {len(loaded.title)} کاراکتر")
        # پیدا کردن تفاوت
        for i, (c1, c2) in enumerate(zip(LONG_TITLE, loaded.title)):
            if c1 != c2:
                print(f"  اولین تفاوت در ایندکس {i}:")
                print(f"    انتظار: {c1!r}")
                print(f"    دریافت: {c2!r}")
                break


# پاکسازی
from pathlib import Path
Path("data/test_long.db").unlink(missing_ok=True)