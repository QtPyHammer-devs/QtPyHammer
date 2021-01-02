from __future__ import annotations

__all__ = ["Manager"]
from .manager import Manager


class Span:
    def __init__(self, spans=list()):
        self._spans = spans

    def __add__(self, other: Span):
        ...


class Renderable:
    def __init__(self, editor_object):
        self.uuid = (object.__class__.__name__, editor_object.id)
        self.children = [(*self.uuid, c.id) for c in editor_object]
        self.buffer_map = {c.id: {"vertex": [0, 0], "index": [0, 0]} for c in self.children}

    @staticmethod
    def set_gl_state():
        """Set all GL state required for this renderable type"""
        ...
