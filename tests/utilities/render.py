import itertools
import sys
import unittest

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from PyQt5 import QtCore, QtWidgets

sys.path.append("../../")
from QtPyHammer.utilities import render, solid


brush_source = """"id" "1"
side
{
        "id" "1"
        "plane" "(64 64 -64) (64 -64 64) (64 64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "2"
        "plane" "(-64 -64 -64) (-64 64 64) (-64 -64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "3"
        "plane" "(-64 64 -64) (64 64 64) (-64 64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "4"
        "plane" "(64 -64 -64) (-64 -64 64) (64 -64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "5"
        "plane" "(64 -64 64) (-64 64 64) (64 64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "6"
        "plane" "(-64 -64 -64) (64 64 -64) (-64 64 -64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
editor
{
        "color" "255 0 255"
        "visgroupshown" "1"
        "visgroupautoshown" "1"
}"""
brush_namespace = solid.vmf.parse_lines(brush_source.split("\n"))
brush = solid.solid(brush_namespace)


class testing_viewport(QtWidgets.QOpenGLWidget):
    def __init__(self):
        super(testing_viewport, self).__init__(parent=None)
        self.render_manager = render.manager()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(15)
        self.timer.timeout.connect(self.update_or_close)
        self.called = {"initializeGL": 0, "update": 0, "paintGL": 0}
        self.close_after = {"initializeGL": 1, "update": 1, "paintGL": 1}

    def update_or_close(self):
        for function, times in self.called.items():
            if times < close_after[function]:
                self.update()
                break
        else:
            self.close()

    def initializeGL(self):
        self.render_manager.init_GL()
        self.render_manager.init_buffers()
        self.timer.start()

    def update(self):
        self.render_manager.update()
        super(testing_viewport, self).update() # call self.paintGL

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.render_manager.draw()
        self.called["paintGL"] += 1


class TestRenderManagerMethods(unittest.TestCase):
    def setUp(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.viewport = testing_viewport()

    def test_initilisation(self):
        self.viewport.show()

    def test_buffer_update(self):
        vertices = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        vertices = itertools.chain(*vertices)
        update = (GL_ARRAY_BUFFER, 0, 36, np.array(vertices, dtype=np.float32))
        self.viewport.render_manager.buffer_update_queue.append(update)
        indices = (0, 1, 2)
        update = (GL_ELEMENT_ARRAY_BUFFER, 0, 12, np.array(indices, dtype=np.uint32))
        self.viewport.render_manager.buffer_update_queue.append(update)
        self.viewport.close_after["update"] = 2
        self.viewport.show()
        # glGetBufferSubData to check data reached buffers
        # must be performed before self.viewport.close() is called

    def test_add_brush(self):
        ...
        # use "brush" defined above

    def test_add_brush_and_displacement(self):
        ...
        # ensure displacement data does not override brushes


class TestSpanOperations(unittest.TestCase):
    def test_add_to_empty_list(self):
        assert render.add_span([], (0, 1)) == [(0, 1)]

    def test_add_exact_tail_overlap(self):
        assert render.add_span([(0, 1)], (1, 2)) == [(0, 3)]

    def test_add_no_overlap_tail(self):
        assert render.add_span([(0, 1)], (2, 2)) == [(0, 1), (2, 2)]

    def test_add_no_overlap_head(self):
        assert render.add_span([(2, 2)], (0, 1)) == [(0, 1), (2, 2)]

    def test_remove_span(self):
        assert render.remove_span([(0, 1)], (0, 1)) == []
        assert render.remove_span([(0, 3)], (1, 2)) == [(2, 1)]
        assert render.remove_span([(0, 1), (2, 2)], (2, 2)) == [(0, 1)]
        assert render.remove_span([(0, 4)], (2, 2)) == [(0, 2)]
        assert render.remove_span([(0, 1), (2, 2)], (0, 1)) == [(2, 2)]


if __name__ == "__main__":
    unittest.main() # not very verbose, need to know which tests fail

##    span_list = [(0, 4)]
##    span = (0, 1)
##    print(f"{span_list} - {span} --> {render.remove_span(span_list, span)}")
##    span_list = [(5, 1)]
##    print(f"{span_list} - {span} --> {render.remove_span(span_list, span)}")
        
