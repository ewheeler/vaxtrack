#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

# until i upgrade to python 2.7 on this machine...
# http://docs.python.org/dev/whatsnew/2.7.html#pep-378-format-specifier-for-thousands-separator
def add_sep_to_int(num, sep=','):
    if isinstance(num, int):
    	num = str(num)
    result = []
    digits = map(str, num)
    build, next = result.append, digits.pop
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    return ''.join(reversed(result))
