"""Windows desktop observation and control primitives for Zeus."""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyautogui
import pytesseract
from PIL import ImageGrab

from config import get_data_dir


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


if os.name == "nt":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32


def _require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("Desktop control is currently implemented for Windows only.")


def _rect_to_dict(rect: Any) -> dict[str, int]:
    return {
        "left": int(rect.left),
        "top": int(rect.top),
        "right": int(rect.right),
        "bottom": int(rect.bottom),
        "width": int(rect.right - rect.left),
        "height": int(rect.bottom - rect.top),
    }


def get_screen_info() -> dict[str, Any]:
    """Return virtual and primary screen dimensions in desktop coordinates."""
    _require_windows()
    return {
        "primary": {
            "width": int(user32.GetSystemMetrics(0)),
            "height": int(user32.GetSystemMetrics(1)),
        },
        "virtual": {
            "left": int(user32.GetSystemMetrics(76)),
            "top": int(user32.GetSystemMetrics(77)),
            "width": int(user32.GetSystemMetrics(78)),
            "height": int(user32.GetSystemMetrics(79)),
        },
        "cursor": {"x": int(pyautogui.position().x), "y": int(pyautogui.position().y)},
    }


def list_windows() -> dict[str, Any]:
    """List visible top-level Windows windows with handles and bounds."""
    _require_windows()
    windows: list[dict[str, Any]] = []
    enum_proc_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum_proc_type
    def enum_window(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        title_buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, length + 1)
        title = title_buffer.value.strip()
        if not title:
            return True
        rect = ctypes.wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        windows.append({
            "handle": int(hwnd),
            "title": title,
            "pid": int(pid.value),
            "bounds": _rect_to_dict(rect),
        })
        return True

    user32.EnumWindows(enum_window, 0)
    return {"windows": windows, "count": len(windows)}


def focus_window(handle: int) -> dict[str, Any]:
    """Restore and focus the top-level window identified by ``list_windows``."""
    _require_windows()
    hwnd = ctypes.c_void_p(int(handle))
    if not user32.IsWindow(hwnd):
        return {"error": f"Window handle is not valid: {handle}"}
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    focused = bool(user32.SetForegroundWindow(hwnd))
    return {"handle": int(handle), "focused": focused}


def capture_screen(
    path: str | None = None,
    left: int | None = None,
    top: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> dict[str, Any]:
    """Capture the full virtual desktop or a region, returning the saved PNG path."""
    _require_windows()
    if any(value is not None for value in (left, top, width, height)):
        if None in (left, top, width, height) or width <= 0 or height <= 0:
            return {"error": "A screen region requires left, top, width, and height."}
        bbox = (left, top, left + width, top + height)
    else:
        bbox = None

    image = ImageGrab.grab(bbox=bbox, all_screens=bbox is None)
    if path:
        output = Path(path).expanduser().resolve()
    else:
        output = get_data_dir() / "screenshots" / (
            f"screen-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}-{uuid.uuid4().hex[:8]}.png"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG")
    return {
        "path": str(output),
        "width": image.width,
        "height": image.height,
        "region": {"left": left, "top": top, "width": width, "height": height} if bbox else None,
    }


def read_screen_text(
    left: int | None = None,
    top: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> dict[str, Any]:
    """Read visible text from the desktop or a screen region using local Tesseract OCR."""
    _require_windows()
    if any(value is not None for value in (left, top, width, height)):
        if None in (left, top, width, height) or width <= 0 or height <= 0:
            return {"error": "An OCR region requires left, top, width, and height."}
        bbox = (left, top, left + width, top + height)
    else:
        bbox = None
    image = ImageGrab.grab(bbox=bbox, all_screens=bbox is None)
    text = pytesseract.image_to_string(image)
    return {"text": text[:20000], "characters": len(text), "region": bbox}


def move_mouse(x: int, y: int, duration_ms: int = 0) -> dict[str, Any]:
    _require_windows()
    pyautogui.moveTo(x, y, duration=max(duration_ms, 0) / 1000)
    return {"x": int(x), "y": int(y)}


def click_mouse(
    x: int,
    y: int,
    button: str = "left",
    clicks: int = 1,
    interval_ms: int = 0,
) -> dict[str, Any]:
    _require_windows()
    if button not in {"left", "middle", "right"}:
        return {"error": "button must be left, middle, or right."}
    pyautogui.click(x=x, y=y, button=button, clicks=max(1, clicks), interval=max(interval_ms, 0) / 1000)
    return {"x": int(x), "y": int(y), "button": button, "clicks": max(1, clicks)}


def type_text(text: str, interval_ms: int = 0) -> dict[str, Any]:
    _require_windows()
    pyautogui.write(text, interval=max(interval_ms, 0) / 1000)
    return {"characters": len(text)}


def press_keys(keys: list[str], interval_ms: int = 0) -> dict[str, Any]:
    _require_windows()
    if not keys:
        return {"error": "At least one key is required."}
    pyautogui.hotkey(*keys, interval=max(interval_ms, 0) / 1000)
    return {"keys": keys}


def wait_for(milliseconds: int) -> dict[str, Any]:
    duration = min(max(milliseconds, 0), 120000) / 1000
    time.sleep(duration)
    return {"waited_ms": int(duration * 1000)}
