# async_runner/hooks.py
from typing import Callable, Dict, Any, Optional

class Hooks:
    def __init__(self):
        self.on_task_start: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_task_success: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_task_fail: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_status_update: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_on_task_start(self, fn: Callable[[Dict[str, Any]], None]):
        self.on_task_start = fn

    def set_on_task_success(self, fn: Callable[[Dict[str, Any]], None]):
        self.on_task_success = fn

    def set_on_task_fail(self, fn: Callable[[Dict[str, Any]], None]):
        self.on_task_fail = fn

    def set_on_status_update(self, fn: Callable[[Dict[str, Any]], None]):
        self.on_status_update = fn
