class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, r):
        print('__add__')
        return Vec(self.x + r.x, self.y + r.y)
    def __radd__(self, l): # sum start from 0 + Vec() ...
        print('__radd__')
        return Vec(self.x, self.y)

x = Vec(10.0, 20.0)
y = Vec(1.0, 2.0)
z = x + y
print(z.x, z.y)

a = [Vec(1.0, 2.0)] * 10
# sa = sum(a, Vec(0, 0))
sa = sum(a)
print(sa.x, sa.y)

# def test(x):
#     if x > 10: print('haha'); return x/2
#     else:      print('hehe'); return x*2

# x = int(input())
# print(test(x))


pp = [i for i in range(10)]
qq = [10] * len(pp)
print(qq)