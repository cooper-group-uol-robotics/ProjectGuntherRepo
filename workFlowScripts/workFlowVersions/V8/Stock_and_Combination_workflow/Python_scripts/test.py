import os
raw_cwd = os.getcwd()
str_cwd = ''.join([letter if letter != '\\' else '/' for letter in raw_cwd])
print(str_cwd)