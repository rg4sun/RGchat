import json
a = ('127.0.0.1',1090)
aj = json.dumps(a)
print(aj)
print(type(aj))

p = '127.0.0.1:1090'
pp = p.split(':')
pp[1] = int(pp[1])
pt = tuple(pp)
print(pt)