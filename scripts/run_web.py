#!/usr/bin/env python
"""LMS Assistant Web — اجرای سرور FastAPI (جایگزین GUI کیوتی)."""

import sys
from pathlib import Path

# اطمینان از بودن root پروژه در sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    import uvicorn

    print("🌐 LMS Assistant Web")
    print("   آدرس: http://127.0.0.1:8000")
    print("   مستندات API: http://127.0.0.1:8000/docs")
    uvicorn.run(
        "src.web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
