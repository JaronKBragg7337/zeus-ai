"""Runtime automation controls for Zeus AI."""
from typing import Dict

from audit_log import append_action


_STOP_REQUESTED = False


def request_stop(reason: str = "manual") -> Dict[str, object]:
    global _STOP_REQUESTED
    _STOP_REQUESTED = True
    append_action({"type": "control", "action": "kill", "reason": reason})
    return {"stopped": True, "reason": reason}


def clear_stop() -> Dict[str, object]:
    global _STOP_REQUESTED
    _STOP_REQUESTED = False
    append_action({"type": "control", "action": "resume"})
    return {"stopped": False}


def stop_requested() -> bool:
    return _STOP_REQUESTED


def status() -> Dict[str, object]:
    return {"stop_requested": _STOP_REQUESTED}
