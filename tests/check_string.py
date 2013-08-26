from citeproc.string import String, NoCase


a = String('a ')
b = String(' b ')
nocase = NoCase('NoCase')
nocase2 = NoCase('NoCaseTwo')

c = a + nocase + b + nocase2

print(c)
print(c.upper())
print(c.lower())

print('test' + b)
print('test ' + nocase)
print(a + 'test')
print(nocase + ' test')

print('test ' + c)
print(c + ' test')
