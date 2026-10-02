"""تست importهای پروژه."""

print("1. تست import EventType...")
from src.models.event import Event, EventType
print(f"   ✅ EventType: {EventType}")
print(f"   ✅ Event: {Event}")
print(f"   ✅ EventType.LIVE_SESSION: {EventType.LIVE_SESSION}")

print("\n2. تست import EventCard...")
from src.ui.widgets.event_card import EventCard
print(f"   ✅ EventCard: {EventCard}")

print("\n3. تست ساخت Event ساده...")
from datetime import datetime
e = Event(
    id="test1",
    course_id="134345",
    title="تست",
    event_type=EventType.LIVE_SESSION,
    url="https://example.com",
    start_at=datetime(2026, 10, 2, 10, 0),
)
print(f"   ✅ Event: {e}")
print(f"   ✅ type(e.event_type): {type(e.event_type)}")

print("\n4. تست ساخت EventCard...")
from PySide6.QtWidgets import QApplication
import sys
app = QApplication(sys.argv)
card = EventCard(e)
print(f"   ✅ EventCard: {card}")