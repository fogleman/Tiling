from math import sin, cos, tan, pi, atan2
import cairo

# Model() defaults
WIDTH = 1024
HEIGHT = 1024
SCALE = 64

# Model.render() defaults
BACKGROUND_COLOR = 0x000000
LINE_WIDTH = 0.1
MARGIN = 0.1
SHOW_LABELS = False

# Shape() defaults
FILL_COLOR = 0x477984
STROKE_COLOR = 0x313E4A

def color(value):
    r = ((value >> (8 * 2)) & 255) / 255.0
    g = ((value >> (8 * 1)) & 255) / 255.0
    b = ((value >> (8 * 0)) & 255) / 255.0
    return (r, g, b)

def normalize(x, y):
    return (round(x, 6), round(y, 6))

def inset_corner(p1, p2, p3, margin):
    (x1, y1), (x2, y2), (x3, y3) = (p1, p2, p3)
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
        point = inset_corner(p1, p2, p3, margin)
        result.append(point)
    result.append(result[0])
    return result

class Shape(object):
    def __init__(self, sides, x=0, y=0, rotation=0, **kwargs):
        self.sides = sides
        self.x = x
        self.y = y
        self.rotation = rotation
        self.fill = FILL_COLOR
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
    def render(self, dc, margin):
        points = self.points(margin)
        dc.move_to(*points[0])
        for point in points[1:]:
            dc.line_to(*point)
        dc.set_source_rgb(*color(self.fill))
        dc.fill_preserve()
        dc.set_source_rgb(*color(self.stroke))
        dc.stroke()
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
    def __init__(self, width=WIDTH, height=HEIGHT, scale=SCALE):
        self.width = width
        self.height = height
        self.scale = scale
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
            w = self.width / 2.0 / self.scale
            h = self.height / 2.0 / self.scale
            tl = any(x < -w and y < -h for x, y in memo)
            tr = any(x > w and y < -h for x, y in memo)
            bl = any(x < -w and y > h for x, y in memo)
            br = any(x > w and y > h for x, y in memo)
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
            shapes.sort(key=angle, reverse=True)
            points = [(shape.x, shape.y) for shape in shapes]
            points.append(points[0])
            result.append(DualShape(points))
        return result
    def render(
            self, dual=False, background_color=BACKGROUND_COLOR, margin=MARGIN,
            show_labels=SHOW_LABELS, line_width=LINE_WIDTH):
        surface = cairo.ImageSurface(
            cairo.FORMAT_RGB24, self.width, self.height)
        dc = cairo.Context(surface)
        dc.set_line_cap(cairo.LINE_CAP_ROUND)
        dc.set_line_join(cairo.LINE_JOIN_ROUND)
        dc.set_line_width(line_width)
        dc.set_font_size(18.0 / self.scale)
        dc.translate(self.width / 2, self.height / 2)
        dc.scale(self.scale, self.scale)
        dc.set_source_rgb(*color(background_color))
        dc.paint()
        shapes = self.dual() if dual else self.lookup.values()
        if show_labels:
            for shape in shapes:
                shape.render_edge_labels(dc)
        for shape in shapes:
            shape.render(dc, margin)
        if show_labels:
            for index, shape in enumerate(self.shapes):
                if shape in shapes:
                    shape.render_label(dc, index)
        return surface
