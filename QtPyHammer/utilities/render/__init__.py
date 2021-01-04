from __future__ import annotations

__all__ = ["Manager", "Span", "Renderable", "RenderableId", "RenderableChildId"]
import collections

from .manager import Manager


class Span:
    def __init__(self, spans=list()):
        self.start, self.end

    def __add__(self, other: Span):
        ...


RenderableId = collections.namedtuple("RenderableId", ["type", "id"])
RenderableChildId = collections.namedtuple("RenderableChildId", ["type", "id", "child_id"])


class Renderable:
    def __init__(self, editor_object):
        self.uuid = RenderableId(object.__class__.__name__, editor_object.id)
        self.children = [RenderableChildId(*self.uuid, c.id) for c in editor_object]
        # ^ editor_object.__iter__() must return children with .id attrs, or None
        self.buffer_map = {c.child_id: {"vertex": Span(), "index": Span()} for c in self.children}

    @staticmethod
    def set_gl_state():
        """Set all GL state required for this renderable type"""
        ...
