from math import sin, cos, tan, pi, atan2
import cairo

BACKGROUND_COLOR = 0x000000
MARGIN = 0.1
SCALE = 48
SHOW_LABELS = False
SIZE = 1024
STROKE_COLOR = 0x313E4A
STROKE_WIDTH = 0.1

BLUE = 0x477984
ORANGE = 0xEEAA4D
RED = 0xC03C44
WHITE = 0xFEF5EB

COLORS = [BLUE, ORANGE, RED, WHITE]

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
        self.fill = COLORS[(self.sides - 3) % len(COLORS)]
        self.stroke = STROKE_COLOR
        for key, value in kwargs.items():
            setattr(self, key, value)
    def points(self, margin=0):
        angle = 2 * pi / self.sides
        rotation = self.rotation - pi / 2
        if self.sides % 2 == 0:
            rotation += angle / 2
        angles = [angle * i + rotation for i in range(self.sides)]
        angles.append(angles[0])
        d = 0.5 / sin(angle / 2) - margin / cos(angle / 2)
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
        points = self.points(MARGIN)
        dc.move_to(*points[0])
        for point in points[1:]:
            dc.line_to(*point)
        dc.set_source_rgb(*color(self.fill))
        dc.fill_preserve()
        if STROKE_WIDTH:
            dc.set_source_rgb(*color(self.stroke))
            dc.stroke_preserve()
        dc.new_path()
    def render_edge_labels(self, dc):
        points = self.points(MARGIN + 0.1)
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
    def add_all(self, indexes, edges, sides, **kwargs):
        start = len(self.shapes)
        for index in indexes:
            for edge in edges:
                self.add(index, edge, sides, **kwargs)
        end = len(self.shapes)
        return range(start, end)
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
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, SIZE, SIZE)
    dc = cairo.Context(surface)
    dc.set_line_cap(cairo.LINE_CAP_ROUND)
    dc.set_line_join(cairo.LINE_JOIN_ROUND)
    dc.set_line_width(STROKE_WIDTH)
    dc.set_font_size(12.0 / SCALE)
    dc.translate(SIZE / 2, SIZE / 2)
    dc.scale(SCALE, SCALE)
    dc.set_source_rgb(*color(BACKGROUND_COLOR))
    dc.paint()

    pattern = 6

    if pattern == 0: # 3.6.3.6
        model = Model()
        model.append(Shape(6))
        a = model.add_all([0], range(6), 3)
        b = model.add_all(a, [1], 6)
        model.recursive_render(dc, b)

    if pattern == 1: # 4.6.12
        model = Model()
        model.append(Shape(12, fill=RED))
        a = model.add_all([0], range(0, 12, 2), 6, fill=ORANGE)
        b = model.add_all([0], range(1, 12, 2), 4, fill=WHITE)
        c = model.add_all(b, [2], 12, fill=RED)
        model.recursive_render(dc, c)

    if pattern == 2: # 3.3.4.3.4
        model = Model()
        model.append(Shape(4))
        a = model.add_all([0], range(4), 3)
        b = model.add_all(a, [1], 4)
        c = model.add_all(b, [2, 3], 3)
        d = model.add_all(c, [2], 4)
        model.recursive_render(dc, d)

    if pattern == 3: # 3.3.3.3.6
        model = Model()
        model.append(Shape(6, fill=RED))
        a = model.add_all([0], range(6), 3)
        b = model.add_all(a, [1], 3)
        c = model.add_all(a, [2], 3)
        d = model.add_all(c, [1], 6, fill=RED)
        model.recursive_render(dc, d)

    if pattern == 4: # 4.8.8
        model = Model()
        model.append(Shape(8, fill=RED))
        a = model.add_all([0], range(1, 8, 2), 4)
        b = model.add_all(a, [1], 8, fill=RED)
        model.recursive_render(dc, b)

    if pattern == 5: # 3.3.4.12 / 3.3.3.3.3.3
        model = Model()
        model.append(Shape(12, fill=RED))
        a = model.add_all([0], range(0, 12, 2), 3)
        b = model.add_all([0], range(1, 12, 2), 4)
        c = model.add_all(b, [1, 3], 3)
        d = model.add_all(b, [2], 12, fill=RED)
        model.recursive_render(dc, d)

    if pattern == 6: # 3.4.6.4
        model = Model()
        model.append(Shape(6, fill=RED))
        a = model.add_all([0], range(6), 4)
        b = model.add_all(a, [1], 3)
        c = model.add_all(a, [2], 6, fill=RED)
        model.recursive_render(dc, c)

    if pattern == 7: # 3.3.4.4
        model = Model()
        model.append(Shape(4))
        a = model.add_all([0], [0, 2], 4) + [0]
        b = model.add_all(a, [1, 3], 3)
        c = model.add_all(b, [1], 3)
        d = model.add_all(c, [2], 4)
        model.recursive_render(dc, d)

    surface.write_to_png('output.png')

if __name__ == '__main__':
    main()
