import re
from sys import stdin


def process_line(line):
    line = re.sub('&shy;', u"U+00AD", line)
    return line


for line in stdin:
    print(process_line(line.rstrip()))
