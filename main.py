from math import sin, cos, tan, pi, atan2
import cairo
import random

COLORS = [
    0x477984,
    0xEEAA4D,
    0xC03C44,
    0xFEF5EB,
]

def color(value):
    r = ((value >> 16) & 0xff) / 255.0
    g = ((value >> 8) & 0xff) / 255.0
    b = ((value >> 0) & 0xff) / 255.0
    return (r, g, b)

class Shape(object):
    def __init__(self, sides, x=0, y=0, rotation=0, **kwargs):
        self.sides = sides
        self.x = x
        self.y = y
        self.rotation = rotation
        self.color = COLORS[(self.sides - 3) % len(COLORS)]
        for key, value in kwargs.items():
            setattr(self, key, value)
    def points(self, scale=1, margin=0):
        angle = 2 * pi / self.sides
        rotation = self.rotation - pi / 2
        if self.sides % 2 == 0:
            rotation += angle / 2
        angles = [angle * i + rotation for i in range(self.sides)]
        angles.append(angles[0])
        d = 0.5 / sin(angle / 2) * scale - margin * sin(angle / 2)
        return [(self.x + cos(a) * d, self.y + sin(a) * d) for a in angles]
    def adjacent(self, sides, edge, **kwargs):
        (x1, y1), (x2, y2) = self.points()[edge:edge + 2]
        angle = 2 * pi / sides
        a = atan2(y2 - y1, x2 - x1)
        b = a - pi / 2
        d = 0.5 / tan(angle / 2)
        x = x1 + (x2 - x1) / 2.0 + cos(b) * d
        y = y1 + (y2 - y1) / 2.0 + sin(b) * d
        a += angle * ((sides - 1) / 2)
        return Shape(sides, x, y, a, **kwargs)
    def render(self, dc):
        points = self.points(margin=0.2)
        dc.move_to(*points[0])
        for point in points[1:]:
            dc.line_to(*point)
        dc.set_source_rgb(*color(self.color))
        dc.fill_preserve()
        dc.set_source_rgb(*color(0x313E4A))
        dc.stroke()
    def render_edge_labels(self, dc):
        points = self.points(margin=0.15)
        for edge in range(self.sides):
            (x1, y1), (x2, y2) = points[edge:edge + 2]
            text = str(edge)
            tw, th = dc.text_extents(text)[2:4]
            x = x1 + (x2 - x1) / 2.0 - tw / 2.0
            y = y1 + (y2 - y1) / 2.0 + th / 2.0
            dc.set_source_rgb(1, 1, 1)
            dc.move_to(x, y)
            dc.show_text(text)
    def render_label(self, dc, text):
        text = str(text)
        tw, th = dc.text_extents(text)[2:4]
        x = self.x - tw / 2.0
        y = self.y + th / 2.0
        dc.set_source_rgb(1, 1, 1)
        dc.move_to(x, y)
        dc.show_text(text)

class Model(object):
    def __init__(self):
        self.shapes = []
    def append(self, shape):
        self.shapes.append(shape)
    def add(self, index, edge, sides, **kwargs):
        parent = self.shapes[index]
        shape = parent.adjacent(sides, edge, **kwargs)
        self.append(shape)
    def render(self, dc, dx=0, dy=0):
        dc.save()
        dc.translate(dx, dy)
        for index, shape in enumerate(self.shapes):
            shape.render(dc)
            # shape.render_edge_labels(dc)
            # shape.render_label(dc, index)
        dc.restore()
    def recursive_render(self, dc, indexes, depth, x=0, y=0, memo=None):
        if depth < 0:
            return
        memo = memo or {}
        key = (round(x, 3), round(y, 3))
        previous_depth = memo.get(key, -1)
        if previous_depth >= depth:
            return
        memo[key] = max(depth, previous_depth)
        if previous_depth < 0:
            self.render(dc, x, y)
        for index in indexes:
            shape = self.shapes[index]
            self.recursive_render(
                dc, indexes, depth - 1, x + shape.x, y + shape.y, memo)

def main():
    width = height = 1024
    scale = 48
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    dc = cairo.Context(surface)
    dc.set_line_cap(cairo.LINE_CAP_ROUND)
    dc.set_line_join(cairo.LINE_JOIN_ROUND)
    dc.set_line_width(3.0 / scale)
    dc.set_font_size(10.0 / scale)
    dc.translate(width / 2, height / 2)
    dc.scale(scale, scale)
    dc.set_source_rgb(0, 0, 0)
    dc.paint()

    # model = Model()
    # model.append(Shape(8, color=COLORS[2]))
    # for i in range(4):
    #     model.add(0, i * 2 + 1, 4)
    # for i in range(4):
    #     model.add(i + 1, 1, 8, color=COLORS[2])
    # model.recursive_render(dc, range(5, 9), 5)

    model = Model()
    model.append(Shape(6, color=COLORS[0]))
    for i in range(6):
        model.add(0, i, 4)
    for i in range(6):
        model.add(i + 1, 1, 3, color=COLORS[2])
    for i in range(6):
        model.add(i + 7, 2, 4)
    for i in range(6):
        model.add(i + 13, 3, 6, color=COLORS[0])
    model.recursive_render(dc, range(19, 25), 6)

    # model = Model()
    # model.append(Shape(6, color=COLORS[0]))
    # for i in range(6):
    #     model.add(0, i, 3, color=COLORS[2])
    # for i in range(6):
    #     model.add(i + 1, 1, 3, color=COLORS[2])
    #     model.add(i + 1, 2, 3, color=COLORS[2])
    # for i in range(6):
    #     model.add(i * 2 + 7, 2, 6, color=COLORS[0])
    # model.recursive_render(dc, range(19, 25), 6)

    surface.write_to_png('output.png')

if __name__ == '__main__':
    main()
