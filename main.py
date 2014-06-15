from math import sin, cos, tan, pi, atan2
import cairo

BACKGROUND_COLOR = 0x000000
DUAL = False
MARGIN = 0.1
SCALE = 64
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

def normalize(x, y):
    return (round(x, 6), round(y, 6))

def inset_corner(p1, p2, p3, margin):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    a1 = atan2(y2 - y1, x2 - x1) - pi / 2
    a2 = atan2(y3 - y2, x3 - x2) - pi / 2
    ax1, ay1 = x1 + cos(a1) * margin, y1 + sin(a1) * margin
    ax2, ay2 = x2 + cos(a1) * margin, y2 + sin(a1) * margin
    bx1, by1 = x2 + cos(a2) * margin, y2 + sin(a2) * margin
    bx2, by2 = x3 + cos(a2) * margin, y3 + sin(a2) * margin
    ady, adx = ay2 - ay1, ax1 - ax2
    bdy, bdx = by2 - by1, bx1 - bx2
    c1 = ady * ax1 + adx * ay1
    c2 = bdy * bx1 + bdx * by1
    d = ady * bdx - bdy * adx
    x = (bdx * c1 - adx * c2) / d
    y = (ady * c2 - bdy * c1) / d
    return (x, y)

def inset_polygon(points, margin):
    result = []
    points = list(points)
    points.insert(0, points[-2])
    for p1, p2, p3 in zip(points, points[1:], points[2:]):
        point = inset_corner(p3, p2, p1, margin)
        result.append(point)
    result.append(result[0])
    return result

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
    def copy(self, x, y):
        return Shape(
            self.sides, x, y, self.rotation,
            fill=self.fill, stroke=self.stroke
        )
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
        points = self.points(MARGIN - 0.25)
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

class DualShape(Shape):
    def __init__(self, points):
        super(DualShape, self).__init__(len(points) - 1)
        self.data = points
    def points(self, margin=0):
        if margin == 0:
            return self.data
        else:
            return inset_polygon(self.data, margin)

class Model(object):
    def __init__(self):
        self.shapes = []
        self.lookup = {}
    def append(self, shape):
        self.shapes.append(shape)
        key = normalize(shape.x, shape.y)
        self.lookup[key] = shape
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
    def add_repeats(self, x, y):
        for shape in self.shapes:
            key = normalize(x + shape.x, y + shape.y)
            if key in self.lookup:
                continue
            self.lookup[key] = shape.copy(x + shape.x, y + shape.y)
    def _repeat(self, indexes, x, y, depth, memo):
        if depth < 0:
            return
        key = normalize(x, y)
        previous_depth = memo.get(key, -1)
        if previous_depth >= depth:
            return
        memo[key] = depth
        if previous_depth == -1:
            self.add_repeats(x, y)
        for index in indexes:
            shape = self.shapes[index]
            self._repeat(
                indexes, x + shape.x, y + shape.y, depth - 1, memo)
    def repeat(self, indexes):
        memo = {}
        depth = 0
        while True:
            self._repeat(indexes, 0, 0, depth, memo)
            d = SIZE / 2.0 / SCALE
            tl = any(x < -d and y < -d for x, y in memo)
            tr = any(x > d and y < -d for x, y in memo)
            bl = any(x < -d and y > d for x, y in memo)
            br = any(x > d and y > d for x, y in memo)
            if tl and tr and bl and br:
                break
            depth += 1
    def dual(self):
        vertexes = {}
        for shape in self.lookup.values():
            for (x, y) in shape.points()[:-1]:
                key = normalize(x, y)
                vertexes.setdefault(key, []).append(shape)
        result = []
        for (x, y), shapes in vertexes.items():
            if len(shapes) < 3:
                continue
            def angle(shape):
                return atan2(shape.y - y, shape.x - x)
            shapes.sort(key=angle)
            points = [(shape.x, shape.y) for shape in shapes]
            points.append(points[0])
            result.append(DualShape(points))
        return result
    def render(self, dc):
        shapes = self.dual() if DUAL else self.lookup.values()
        if SHOW_LABELS:
            for shape in shapes:
                shape.render_edge_labels(dc)
        for index, shape in enumerate(shapes):
            shape.render(dc)
            if SHOW_LABELS:
                shape.render_label(dc, index)

def main(pattern):
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, SIZE, SIZE)
    dc = cairo.Context(surface)
    dc.set_line_cap(cairo.LINE_CAP_ROUND)
    dc.set_line_join(cairo.LINE_JOIN_ROUND)
    dc.set_line_width(STROKE_WIDTH)
    dc.set_font_size(18.0 / SCALE)
    dc.translate(SIZE / 2, SIZE / 2)
    dc.scale(SCALE, SCALE)
    dc.set_source_rgb(*color(BACKGROUND_COLOR))
    dc.paint()

    if pattern == 0: # 3.6.3.6
        model = Model()
        model.append(Shape(6))
        a = model.add_all([0], range(6), 3)
        b = model.add_all(a, [1], 6)
        model.repeat(b)
        model.render(dc)

    if pattern == 1: # 4.6.12
        model = Model()
        model.append(Shape(12, fill=RED))
        a = model.add_all([0], range(0, 12, 2), 6, fill=ORANGE)
        b = model.add_all([0], range(1, 12, 2), 4, fill=WHITE)
        c = model.add_all(b, [2], 12, fill=RED)
        model.repeat(c)
        model.render(dc)

    if pattern == 2: # 3.3.4.3.4
        model = Model()
        model.append(Shape(4))
        a = model.add_all([0], range(4), 3)
        b = model.add_all(a, [1], 4)
        c = model.add_all(b, [2, 3], 3)
        d = model.add_all(c, [2], 4)
        model.repeat(d)
        model.render(dc)

    if pattern == 3: # 3.3.3.3.6
        model = Model()
        model.append(Shape(6, fill=RED))
        a = model.add_all([0], range(6), 3)
        b = model.add_all(a, [1], 3)
        c = model.add_all(a, [2], 3)
        d = model.add_all(c, [1], 6, fill=RED)
        model.repeat(d)
        model.render(dc)

    if pattern == 4: # 4.8.8
        model = Model()
        model.append(Shape(8, fill=RED))
        a = model.add_all([0], range(1, 8, 2), 4)
        b = model.add_all(a, [1], 8, fill=RED)
        model.repeat(b)
        model.render(dc)

    if pattern == 5: # 3.3.4.12 / 3.3.3.3.3.3
        model = Model()
        model.append(Shape(12, fill=RED))
        a = model.add_all([0], range(0, 12, 2), 3)
        b = model.add_all([0], range(1, 12, 2), 4)
        c = model.add_all(b, [1, 3], 3)
        d = model.add_all(b, [2], 12, fill=RED)
        model.repeat(d)
        model.render(dc)

    if pattern == 6: # 3.4.6.4
        model = Model()
        model.append(Shape(6, fill=RED))
        a = model.add_all([0], range(6), 4)
        b = model.add_all(a, [1], 3)
        c = model.add_all(a, [2], 6, fill=RED)
        model.repeat(c)
        model.render(dc)

    if pattern == 7: # 3.3.4.4
        model = Model()
        model.append(Shape(4))
        a = model.add_all([0], [0, 2], 4) + [0]
        b = model.add_all(a, [1, 3], 3)
        c = model.add_all(b, [1], 3)
        d = model.add_all(c, [2], 4)
        model.repeat(d)
        model.render(dc)

    if pattern == 8: # 3.3.3.3.3.3
        model = Model()
        model.append(Shape(3))
        a = model.add_all([0], range(3), 3)
        b = model.add_all(a, [1, 2], 3)
        model.repeat(b)
        model.render(dc)

    if pattern == 9:
        model = Model()
        model.append(Shape(5))
        a = model.add_all([0], range(5), 4)
        for i in range(8):
            b = model.add_all(a, [2], 5)
            a = model.add_all(b, [2], 4)
        model.render(dc)

    if pattern == 10:
        model = Model()
        model.append(Shape(6, fill=RED))
        a = model.add_all([0], range(6), 4)
        b = model.add_all(a, [2], 3)
        c = model.add_all(b, [1], 4)
        d = model.add_all(b, [2], 4)
        e = model.add_all(d, [2], 6, fill=RED)
        model.add_all(a, [1], 3)
        model.add_all(c, [1], 3)
        model.repeat(e)
        model.render(dc)

    if pattern == 11:
        model = Model()
        model.append(Shape(8))
        a = model.add_all([0], range(0, 8, 2), 6)
        b = model.add_all(a, [3], 8)
        model.repeat(b)
        model.render(dc)

    surface.write_to_png('output.png')

if __name__ == '__main__':
    main(6)
