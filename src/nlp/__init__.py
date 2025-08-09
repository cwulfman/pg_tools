import unicodedata
from copy import deepcopy
from collections import namedtuple
from lxml import etree


BBox = namedtuple('BBox', ['x', 'y', 'w', 'h'])

class Token:
    def __init__(self, element:etree.Element) -> None:
        self.text = element.text
        self.tail = element.tail
        self.bbox = BBox(*element.get('title').split(';')[0].split(' ')[1:])

    def __repr__(self) -> str:
        return f"Token({self.text!r})"

    def __str__(self) -> str:
        return self.text_with_ws

    @property
    def text_with_ws(self) -> str:
        if self.tail:
            return self.text + self.tail
        else:
            return self.text


    def is_greek(self, threshold: float = 0.5) -> bool:
        greek_count = 0
        alpha_count = 0
        
        for char in self.text:
            alpha_count += 1
            codepoint = ord(char)
                # is it in the Greek and Coptic code block or the Extended Greek code block?
            if (0x0370 <= codepoint <= 0x03FF) or (0x1F00 <= codepoint <= 0x1FFF):
                greek_count += 1
                
        if alpha_count == 0:
                return False  # No letters at all
                
        return (greek_count / alpha_count) >= threshold


    @property
    def is_punct(self) -> bool:
        """
        Returns True if the character is punctuation based on Unicode category.
        """
        if len(self.text) != 1:
            return False
        return unicodedata.category(self.text).startswith('P')



class Span:
    def __init__(self, element:etree.Element):
        self.element = element
        self.type:str = element.get('class')
        self._element:etree.Element = element
        self.bbox = BBox(*element.get('title').split(';')[0].split(' ')[1:])        
        self.objects = []
        self.objects = [genObject(child) for child in element if child.get('class') is not None]

    def __repr__(self):
        return f"<{self.type} len={len(self.objects)}>"

    def __str__(self):
        return ' '.join([tok.text for tok in self.tokens])


    @property
    def tokens(self):
        token_list = []
        for obj in self.objects:
            if obj.__class__ is Token:
                token_list.append(obj)
            else:
                token_list = token_list + obj.tokens
        return token_list

    @property
    def words(self):
        tokens = self.tokens
        return [tok for tok in tokens if not(tok.is_punct)]
    
    @property
    def lines(self):
        line_list = []
        if self.type == 'ocr_line':
            line_list.append(self)
        else:
            for o in self.objects:
                line_list = line_list + o.lines
        return line_list

    @property
    def percent_greek(self) -> float:
        words = self.words
        if len(words) == 0:
            return 0
        else:
            greek_count = 0
            tok_count = len(words)
            greek_count = len([word for word in words if word.is_greek()])
            return (greek_count / tok_count)

    def is_greek(self, threshold: float = 0.7) -> bool:
        words = self.words
        if len(words) == 0:
            return False
        else:
            greek_words = [word for word in words if word.is_greek]
            return (len(greek_words) / len(words)) >= threshold


    def is_greek_old(self, threshold: float = 0.7) -> bool:
        if len(self.objects) == 0:
            return 0
        else:
            greek_count = 0
            obj_count = 0
            for obj in self.objects:
                
                obj_count +=1
                if obj.is_greek(threshold):
                    greek_count += 1
                    
            return (greek_count / obj_count) >= threshold


            

class Page(Span):

    def __str__(self):
        page = ''
        for o in self.objects:
            page += str(o)
        return page

    @property
    def blocks(self):
        return [o for o in self.objects if o.type == 'ocrx_block']


class Block(Span):

    def __str__(self):
        block = '<ab>'
        for o in self.objects:
            block += str(o)
        block += '</ab>\n'
        return block
    

    @property
    def pars(self):
        return [o for o in self.objects if o.type == 'ocr_par']



class Par(Span):
    def __str__(self):
        p = '\n'
        for o in self.objects:
            p = p + str(o)
        return p


class Line(Span):
    def __str__(self):
        p = ''
        for o in self.objects:
            p = p + str(o)
        p += '\n'
        return p


    @property
    def starts_greek(self) -> bool:
        line_length = len(self.words)
        percent = percent_greek(self.words[0:int(line_length / 2)])
        return percent > .5


    @property
    def ends_greek(self) -> bool:
        line_length = len(self.words)
        percent = percent_greek(self.words[int(line_length / 2):])
        return percent > .5

                   

    @property
    def is_merged(self) -> bool:
        condition1 = self.starts_greek and not(self.ends_greek)
        condition2 = not(self.starts_greek) and self.ends_greek
        return any([condition1, condition2])






def genObject(element:etree.Element):
    match element.get('class'):
        case 'ocr_page':
            return Page(element)

        case 'ocrx_block':
            return Block(element)

        case 'ocrx_word':
            return Token(element)

        case 'ocr_line':
            return Line(element)

        case 'ocr_par':
            return Par(element)

        case _:
            return None

def percent_greek(tok_list):
    if len(tok_list) == 0:
        return 0
    else:
        tok_count = 0
        greek_count = 0
        for tok in tok_list:
            tok_count +=1
            if tok.is_greek():
                greek_count += 1
        return greek_count / tok_count
            

def split_line_from_left(line):
    """returns two new line objects."""

    # calculate the middle
    idx = 1
    tokens = line.objects
    v = tokens[0:idx]
    while (percent_greek(v) > 0.9):
        idx += 1
        v = tokens[0:idx]

    mid = idx-1
    
    left_line = deepcopy(line)
    left_line.objects = left_line.objects[0:mid]
    
    right_line = deepcopy(line)
    right_line.objects = right_line.objects[mid:len(right_line.objects)]

    # left_string = tokens[0:idx-1]
    # right_string = tokens[idx-1:len(tokens)]
    # return left_string,right_string
    return left_line,right_line


def split_line_from_right(line):
    """returns two new line objects."""
    # calculate the middle


    for mid,tok in enumerate(line.tokens):
        if tok.is_punct:
            next
        if tok.is_greek():
            break
    
    left_line = deepcopy(line)
    left_line.objects = left_line.objects[0:mid]
    
    right_line = deepcopy(line)
    right_line.objects = right_line.objects[mid:len(right_line.objects)]
    return left_line,right_line

def split_line(line):
    if line.starts_greek:
        greek,latin = split_line_from_left(line)
    else:
        latin,greek = split_line_from_right(line)
    return greek,latin
