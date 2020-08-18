def test(x):
    if x > 10: print('haha'); return x/2
    else:      print('hehe'); return x*2

x = int(input())
print(test(x))