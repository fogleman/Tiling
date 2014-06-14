from math import sin, cos, tan, pi, atan2
import cairo

MARGIN = 0.1
SCALE = 48
SHOW_LABELS = False
SIZE = 1024
STROKE_COLOR = 0x313E4A
STROKE_WIDTH = 0.1

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
        d = 0.5 / sin(angle / 2) * scale - margin / cos(angle / 2)
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
        points = self.points(margin=MARGIN)
        dc.move_to(*points[0])
        for point in points[1:]:
            dc.line_to(*point)
        dc.set_source_rgb(*color(self.color))
        dc.fill_preserve()
        if STROKE_WIDTH:
            dc.set_source_rgb(*color(STROKE_COLOR))
            dc.stroke_preserve()
        dc.new_path()
    def render_edge_labels(self, dc):
        points = self.points(margin=MARGIN + 0.1)
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
    def render(self, dc, x=0, y=0):
        dc.save()
        dc.translate(x, y)
        for index, shape in enumerate(self.shapes):
            shape.render(dc)
            if SHOW_LABELS:
                shape.render_edge_labels(dc)
                shape.render_label(dc, index)
        dc.restore()
    def _recursive_render(self, dc, indexes, x, y, depth, memo):
        if depth < 0:
            return
        key = (round(x, 6), round(y, 6))
        previous_depth = memo.get(key, -1)
        if previous_depth >= depth:
            return
        memo[key] = depth
        if previous_depth == -1:
            self.render(dc, x, y)
        for index in indexes:
            shape = self.shapes[index]
            self._recursive_render(
                dc, indexes, x + shape.x, y + shape.y, depth - 1, memo)
    def recursive_render(self, dc, indexes):
        memo = {}
        depth = 0
        while True:
            self._recursive_render(dc, indexes, 0, 0, depth, memo)
            d = SIZE / 2.0 / SCALE
            tl = any(x < -d and y < -d for x, y in memo)
            tr = any(x > d and y < -d for x, y in memo)
            bl = any(x < -d and y > d for x, y in memo)
            br = any(x > d and y > d for x, y in memo)
            if tl and tr and bl and br:
                break
            depth += 1

def main():
    width = height = SIZE
    scale = SCALE
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    dc = cairo.Context(surface)
    dc.set_line_cap(cairo.LINE_CAP_ROUND)
    dc.set_line_join(cairo.LINE_JOIN_ROUND)
    dc.set_line_width(STROKE_WIDTH)
    dc.set_font_size(12.0 / scale)
    dc.translate(width / 2, height / 2)
    dc.scale(scale, scale)
    dc.set_source_rgb(0, 0, 0)
    dc.paint()

    pattern = 3

    if pattern == 1:
        model = Model()
        model.append(Shape(12, color=COLORS[2]))
        for i in range(12):
            model.add(0, i, 3 + i % 2)
        for i in range(6):
            model.add(2 + i * 2, 2, 12, color=COLORS[2])
            model.add(2 + i * 2, 1, 3)
            model.add(2 + i * 2, 3, 3)
        model.recursive_render(dc, range(13, 29, 3))

    elif pattern == 2:
        model = Model()
        model.append(Shape(8, color=COLORS[2]))
        for i in range(4):
            model.add(0, i * 2 + 1, 4)
        for i in range(4):
            model.add(i + 1, 1, 8, color=COLORS[2])
        model.recursive_render(dc, range(5, 9))

    elif pattern == 3:
        model = Model()
        model.append(Shape(6, color=COLORS[2]))
        for i in range(6):
            model.add(0, i, 4)
        for i in range(6):
            model.add(i + 1, 1, 3, color=COLORS[3])
        for i in range(6):
            model.add(i + 7, 2, 4)
        for i in range(6):
            model.add(i + 13, 3, 6, color=COLORS[2])
        model.recursive_render(dc, range(19, 25))

    elif pattern == 4:
        model = Model()
        model.append(Shape(6, color=COLORS[0]))
        for i in range(6):
            model.add(0, i, 3, color=COLORS[2])
        for i in range(6):
            model.add(i + 1, 1, 3, color=COLORS[2])
            model.add(i + 1, 2, 3, color=COLORS[2])
        for i in range(6):
            model.add(i * 2 + 7, 2, 6, color=COLORS[0])
        model.recursive_render(dc, range(19, 25))

    surface.write_to_png('output.png')

if __name__ == '__main__':
    main()
