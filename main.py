from tile import Model, Shape

BLUE = 0x477984
ORANGE = 0xEEAA4D
RED = 0xC03C44
WHITE = 0xFEF5EB

def render(pattern, dual):
    if pattern == 0: # 3.6.3.6
        model = Model()
        model.append(Shape(6))
        a = model.add(0, range(6), 3)
        b = model.add(a, 1, 6)
        model.repeat(b)
        return model.render(dual)

    if pattern == 1: # 4.6.12
        model = Model()
        model.append(Shape(12))
        a = model.add(0, range(0, 12, 2), 6)
        b = model.add(0, range(1, 12, 2), 4)
        c = model.add(b, 2, 12)
        model.repeat(c)
        return model.render(dual)

    if pattern == 2: # 3.3.4.3.4
        model = Model()
        model.append(Shape(4))
        a = model.add(0, range(4), 3)
        b = model.add(a, 1, 4)
        c = model.add(b, [2, 3], 3)
        d = model.add(c, 2, 4)
        model.repeat(d)
        return model.render(dual)

    if pattern == 3: # 3.3.3.3.6
        model = Model()
        model.append(Shape(6))
        a = model.add(0, range(6), 3)
        b = model.add(a, 1, 3)
        c = model.add(a, 2, 3)
        d = model.add(c, 1, 6)
        model.repeat(d)
        return model.render(dual)

    if pattern == 4: # 4.8.8
        model = Model()
        model.append(Shape(8))
        a = model.add(0, range(1, 8, 2), 4)
        b = model.add(a, 1, 8)
        model.repeat(b)
        return model.render(dual)

    if pattern == 5: # 3.3.4.12 / 3.3.3.3.3.3
        model = Model()
        model.append(Shape(12))
        a = model.add(0, range(0, 12, 2), 3)
        b = model.add(0, range(1, 12, 2), 4)
        c = model.add(b, [1, 3], 3)
        d = model.add(b, 2, 12)
        model.repeat(d)
        return model.render(dual)

    if pattern == 6: # 3.4.6.4
        model = Model()
        model.append(Shape(6))
        a = model.add(0, range(6), 4)
        b = model.add(a, 1, 3)
        c = model.add(a, 2, 6)
        model.repeat(c)
        return model.render(dual)

    if pattern == 7: # 3.3.4.4
        model = Model()
        model.append(Shape(4))
        a = model.add(0, [0, 2], 4) + [0]
        b = model.add(a, [1, 3], 3)
        c = model.add(b, 1, 3)
        d = model.add(c, 2, 4)
        model.repeat(d)
        return model.render(dual)

    if pattern == 8: # 3.3.3.3.3.3
        model = Model()
        model.append(Shape(3))
        a = model.add(0, range(3), 3)
        b = model.add(a, [1, 2], 3)
        model.repeat(b)
        return model.render(dual)

    if pattern == 9:
        model = Model(scale=50)
        model.append(Shape(5))
        a = model.add(0, range(5), 4)
        for i in range(8):
            b = model.add(a, 2, 5)
            a = model.add(b, 2, 4)
        return model.render(dual)

    if pattern == 10:
        model = Model()
        model.append(Shape(6))
        a = model.add(0, range(6), 4)
        b = model.add(a, 2, 3)
        c = model.add(b, 1, 4)
        d = model.add(b, 2, 4)
        e = model.add(d, 2, 6)
        model.add(a, 1, 3)
        model.add(c, 1, 3)
        model.repeat(e)
        return model.render(dual)

    if pattern == 11:
        model = Model()
        model.append(Shape(8))
        a = model.add(0, range(0, 8, 2), 6)
        b = model.add(a, 3, 8)
        model.repeat(b)
        return model.render(dual)

    if pattern == 12: # 3.12.12
        model = Model()
        model.append(Shape(12))
        a = model.add(0, range(0, 12, 2), 3)
        b = model.add(0, range(1, 12, 2), 12)
        model.repeat(b)
        return model.render(dual)

def main():
    for pattern in range(13):
        surface = render(pattern, False)
        surface.write_to_png('output%02da.png' % pattern)
        surface = render(pattern, True)
        surface.write_to_png('output%02db.png' % pattern)

if __name__ == '__main__':
    main()
