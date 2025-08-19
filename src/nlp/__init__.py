from collections import deque
import statistics
from pathlib import Path
import re
import unicodedata
from copy import deepcopy
from lxml import etree
from dataclasses import dataclass
from typing import Iterator

ns = {"xhtml": "http://www.w3.org/1999/xhtml"}

def flatten(a):
    res = []
    for x in a:
        if isinstance(x, list):
            res.extend(flatten(x))
        else:
            res.append(x)
    return res

@dataclass(frozen=True)
class Point:
    x: int
    y: int
    

@dataclass
class BBox:
    min: Point
    max: Point

    @property
    def width(self) -> int:
        return self.max.x - self.min.x

    @property
    def height(self) -> int:
        return self.max.y - self.min.y

    @property
    def left(self):
        return self.min.x

    @property
    def right(self):
        return self.max.x - self.height

    @property
    def top(self):
        return self.min.x

    @property
    def bottom(self):
        return self.max.y
    

    def __init__(self, x_min:int, y_min:int, x_max:int, y_max:int):
        self.min = Point(x_min, y_min)
        self.max = Point(x_max, y_max)
    

# @dataclass(frozen=True)
# class BBox:
#     x_min: int
#     y_min: int
#     x_max: int
#     y_max: int

#     @property
#     def width(self) -> int:
#         return self.x_max - self.x_min

#     @property
#     def height(self) -> int:
#         return self.y_max - self.y_min

#     def to_xywh(self) -> tuple[int, int, int, int]:
#         """Return (x, y, width, height) tuple."""
#         return (self.x_min, self.y_min, self.width, self.height)

#     # --- Drop-in tuple-like behavior ---
#     def __iter__(self) -> Iterator[int]:
#         yield self.x_min
#         yield self.y_min
#         yield self.x_max
#         yield self.y_max

#     def __getitem__(self, index: int) -> int:
#         return (self.x_min, self.y_min, self.x_max, self.y_max)[index]

#     def __len__(self) -> int:
#         return 4

class Token:
    def __init__(self, element:etree.Element) -> None:
        self.type = 'token'
        self.element = element
        self.text = self.clean_text(element.text)
        self.tail = element.tail
        bbox_string = element.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
        # self.bbox = BBox(Point(values[0], values[1]), Point(values[3], values[4]));
        self.bbox = BBox(*values)
        self.index = None
        self.parent = None

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

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.min.x

    @property
    def right(self):
        return self.bbox.max.x - self.bbox.height

    @property
    def top(self):
        return self.bbox.min.x

    @property
    def bottom(self):
        return self.bbox.max.y
        


    def clean_text(self,text):
        # Replace bad entities (example: replace &shy; with actual soft hyphen)
        text = text.replace("&shy;", "\u00AD")
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text
        


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



# def calculated_bbox(token_list:list[Token]):
#     first_token = token_list[0]
#     last_token = token_list[-1]

    
    


# class Span:
#     def __init__(self, element:etree.Element):
#         self.element = element
#         self.parent = None
#         self.index = 0
#         self.type:str = element.get('class')
#         self._element:etree.Element = element
#         bbox_string = element.get('title').split(';')[0].split(' ')[1:]
#         values = [int(v) for v in bbox_string]
#         self.bbox = BBox(*values)
#         children = [child for child in element if child.get('class') is not None]
#         self.objects = []
#         for i,child in enumerate(children):
#             object = genObject(child, i)
#             object.parent = self
#             self.objects.append(object)
        
#         # self.objects = [genObject(child) for child in element if child.get('class') is not None]


#     def __repr__(self):
#         return f"<{self.type} len={len(self.objects)}>"

#     def __str__(self):
#         return ' '.join([tok.text for tok in self.tokens])


#     @property
#     def top(self):
#         return self.bbox.y_min

#     @property
#     def bottom(self):
#         return self.bbox.y_max

#     @property
#     def width(self):
#         return self.bbox.width

#     @property
#     def height(self):
#         return self.bbox.height

#     @property
#     def left(self):
#         return self.bbox.x_min

#     @property
#     def right(self):
#         return self.bbox.x_max

#     @property
#     def tokens(self):
#         token_list = []
#         for obj in self.objects:
#             if obj.__class__ is Token:
#                 token_list.append(obj)
#             else:
#                 token_list = token_list + obj.tokens
#         return token_list

#     @property
#     def words(self):
#         tokens = self.tokens
#         return [tok for tok in tokens if not(tok.is_punct)]
    
#     @property
#     def lines(self):
#         line_list = []
#         if self.type == 'ocr_line':
#             line_list.append(self)
#         else:
#             for o in self.objects:
#                 line_list = line_list + o.lines
#         return line_list

#     @property
#     def percent_greek(self) -> float:
#         words = self.words
#         if len(words) == 0:
#             return 0
#         else:
#             greek_count = 0
#             tok_count = len(words)
#             greek_count = len([word for word in words if word.is_greek()])
#             return (greek_count / tok_count)

#     def is_greek(self, threshold: float = 0.7) -> bool:
#         words = self.words
#         if len(words) == 0:
#             return False
#         else:
#             greek_words = [word for word in words if word.is_greek(threshold)]
#             return (len(greek_words) / len(words)) >= threshold




            

# class Page(Span):
#     def __init__(self, element:etree.Element, page_number=None):
#         super().__init__(element)
#         self.number = page_number
#         self._columns = None

#     def __str__(self):
#         page = ''
#         # if self.columns:
#         if self.greek_columns:
#             for column in self.greek_columns:
#                 page += str(column)
#             # page += str(self.columns['left'])
#             # page += str(self.columns['right'])
#         # else:
#         #     for o in self.objects:
#         #         page += str(o)
#         return page

#     @property
#     def columns(self):
#         if self._columns is None:
#             self._columns = {}
#             left,right = split_columns(self)
#             self._columns['left'] = left
#             self._columns['right'] = right
#         return self._columns

#     @property
#     def greek_columns(self):
#         hits = []
#         for side in ['left', 'right']:
#             if self.columns[side].is_greek():
#                 hits.append(self.columns[side])
#         return hits
                

#     @property
#     def blocks(self):
#         return [o for o in self.objects if o.type == 'ocrx_block']

#     @property
#     def header(self):
#         p_elements = self.element.xpath("xhtml:div[@class='ocrx_block']/xhtml:p",
#                            namespaces=ns)
#         if p_elements:
#             return genObject(p_elements[0],0)
#         else:
#             return None

#     @property
#     def header_old(self):
#         header = None
#         if self.lines and self.header:
#             header = self.columns['left'].remove_header()
#         return header


#     def serialize(self, file_handle):
        
#         if self.lines:
#             header = self.columns['left'].remove_header()
#             greek_columns = self.greek_columns
#         else:
#             header = None
#             greek_columns = []

#         if header:
#             running_title_toks = header.tokens[2:]
#             if running_title_toks:
#                 running_title = ''.join([tok.text_with_ws for tok in running_title_toks])
#                 running_title 
#                 pbstring = f"<pb n=\"{self.number}\" ed=\"{running_title}\"/>"
#             else:
#                 pbstring = f"<pb n=\"{self.number}\" />"
#         else:
#             pbstring = f"<pb n=\"{self.number}\" />"

#             file_handle.write(f"{pbstring}\n")
            
#             for column in greek_columns:
#                 if header:
#                     if column == self.columns['left']:
#                         cb_number = header.tokens[0].text
#                     elif column == self.columns['right']:
#                         cb_number = header.tokens[1].text
#                     cb = f"<cb n='{cb_number}' />\n"
#                 if cb_number.isdigit():
#                     cb = f"<cb n='{cb_number}' />\n"
#                 else:
#                     cb = "<cb />"
#                 file_handle.write(f"{cb}\n")
#                 file_handle.write(str(column))


#     def repair_fused_line(self, fused_line):
#         left_line, right_line = split_line(fused_line)
#         left_column, right_column = split_columns(self)
#         left_block,left_idx = left_column.line_index(fused_line)

#         target = left_block.objects[left_idx]
#         move_line(left_line, target)
#         if left_idx > len(left_block.objects):
#             left_block.objects.append(left_line)
#         else:
#             left_block.objects[left_idx] = left_line

#         # breakpoint()
#         pass

#         right_block,right_idx = right_column.line_after_index(right_line)
#         target = right_block.objects[right_idx]
#         move_line(right_line,target)
#         right_block.objects.insert(right_idx, right_line)

#         return left_line, right_line


#     def repair_fused_lines(self):
#         fused_lines = merged_lines(self)
#         for fused_line in fused_lines:
#             self.repair_fused_line(fused_line)
        

# class Block(Span):

#     def __str__(self):
#         # block = '<ab>'
#         block = ''
#         for o in self.objects:
#             block += str(o)
#         # block += '</ab>\n'
#         return block
    

#     @property
#     def pars(self):
#         return [o for o in self.objects if o.type == 'ocr_par']



# class Par(Span):
#     def __str__(self):
#         p = '\n'
#         for o in self.objects:
#             p = p + str(o)
#         return p


# class Line(Span):
#     def __str__(self):
#         p = ''
#         for o in self.objects:
#             p = p + str(o)
#         p += '\n'
#         return p


#     @property
#     def starts_greek(self) -> bool:
#         line_length = len(self.words)
#         percent = percent_greek(self.words[0:int(line_length / 2)])
#         return percent > .5


#     @property
#     def ends_greek(self) -> bool:
#         line_length = len(self.words)
#         percent = percent_greek(self.words[int(line_length / 2):])
#         return percent > .5

                   

#     @property
#     def is_merged(self) -> bool:
#         condition1 = self.starts_greek and not(self.ends_greek)
#         condition2 = not(self.starts_greek) and self.ends_greek
#         return any([condition1, condition2])

    



# class Column:
#     def __init__(self, blocks, number=None):
#         self.blocks = blocks
#         self._lines = None
#         self.number = number

#     def __repr__(self):
#         return f"<column n='{self.number}'>"
        
#     def __str__(self):
#         coltext =''
#         if self.number and self.number.isdigit():
#             coltext += f"<cb n='{self.number}' />\n"
#         else:
#             coltext += "<cb/>\n"

#         coltext += '\n'.join([str(b) for b in self.blocks])
#         return coltext

#     @property
#     def lines(self):
#         if self._lines is None:
#             self._lines = []
#             for o in self.blocks:
#                 self._lines = self._lines + o.lines
#         return self._lines


#     def remove_header(self):
#         if self.blocks:
#             header = self.blocks.pop(0)
#             self._lines = None
#             return header
#         else:
#             return None

#     def line_index(self, line):
#         # search the lines in the column
#         # get the index of the line in its parent block
#         idx = line.parent.objects.index(line)
#         return line.parent, idx
#         # for block in self.blocks:
#         #     if contains_line(block, line):
#         #         index_in_block = block.lines.index(line)
#         #         return block,index_in_block

#     def line_after_index(self,from_line, spacing=10):
#         # the top of the next line
#         # should be roughly the same
#         # as the bottom of the line.
#         hits = [line for line in self.lines
#                 if line.top >= from_line.bottom
#                 and line.top <= from_line.bottom + spacing]

#         # breakpoint()

#         if hits:
#             next_line = hits[0]
#         else:
#             next_line = self.lines[-1]

#         next_line_parent = next_line.parent
#         idx = next_line_parent.objects.index(next_line)
#         return next_line_parent, idx
    


#     # def is_greek(self, threshold = .5):
#     #     if len(self.blocks) == 0:
#     #         return False
#     #     else:
#     #         greek_blocks = [b for b in self.blocks if b.is_greek()]
#     #         return (len(greek_blocks) / len(self.blocks)) >= threshold


#     def is_greek(self, threshold = .5):
#         if len(self.lines) == 0:
#             return False
#         else:
#             greek_lines = [line for line in self.lines if line.is_greek()]
#             return (len(greek_lines) / len(self.lines)) >= threshold




# def genObject(element:etree.Element, index):
#     match element.get('class'):
#         case 'ocr_page':
#             page:Page = Page(element)
#             page.index = index
#             return page

#         case 'ocrx_block':
#             block:Block = Block(element)
#             block.index = index
#             return block

#         case 'ocrx_word':
#             token = Token(element)
#             return token

#         case 'ocr_line':
#             line = Line(element)
#             line.index = index
#             return line

#         case 'ocr_par':
#             par = Par(element)
#             par.index = index
#             return par

#         case _:
#             return None


        

# def percent_greek(tok_list):
#     if len(tok_list) == 0:
#         return 0
#     else:
#         tok_count = 0
#         greek_count = 0
#         for tok in tok_list:
#             tok_count +=1
#             if tok.is_greek():
#                 greek_count += 1
#         return greek_count / tok_count


# # def split_line_from_left(line):
# #     """returns two new line objects."""

# #     # calculate the middle
# #     idx = 1
# #     tokens = line.objects
# #     v = tokens[0:idx]
# #     while (percent_greek(v) > 0.9):
# #         idx += 1
# #         v = tokens[0:idx]

# #     mid = idx-1

# #     left_line = deepcopy(line)
# #     left_line.objects = left_line.objects[0:mid]

# #     right_line = deepcopy(line)
# #     right_line.objects = right_line.objects[mid:len(right_line.objects)]

# #     # left_string = tokens[0:idx-1]
# #     # right_string = tokens[idx-1:len(tokens)]
# #     # return left_string,right_string
# #     return left_line,right_line


# # def split_linefrom_right(line):
# #     """returns two new line objects."""
# #     # calculate the middle


# #     for mid,tok in enumerate(line.tokens):
# #         if tok.is_punct:
# #             next
# #         if tok.is_greek():
# #             break

# #     left_line = deepcopy(line)
# #     left_line.objects = left_line.objects[0:mid]

# #     right_line = deepcopy(line)
# #     right_line.objects = right_line.objects[mid:len(right_line.objects)]
# #     return left_line,right_line


# def split_line(line):
#     left_line = deepcopy(line)
#     right_line = deepcopy(line)

#     if line.starts_greek:
#         indexes = [line.objects.index(word) for word in line.words if word.is_greek()]
#         greek_span = left_line.objects[indexes[0]:indexes[-1]+1]
#         latin_span = right_line.objects[indexes[-1] + 1:len(left_line.objects)]
#         left_line.objects = greek_span
#         right_line.objects = latin_span

#     else:
#         indexes = [line.objects.index(word) for word in line.words if not(word.is_greek())]
#         if indexes:
#             latin_span = right_line.objects[indexes[0]:indexes[-1]+1]
#             greek_span = left_line.objects[indexes[-1] + 1:len(left_line.objects)]
#             left_line.objects = latin_span
#             right_line.objecs = greek_span
#         else:
#             # breakpoint()
#             pass

#     return left_line,right_line
        

# def right_column(page, padding=40):
#     cb_number = None
#     if page.header:
#         try:
#             cb_number = page.header.tokens[1].text
#         except IndexError:
#             cb_number = 0
#     mid = page.width / 2
#     return Column([b for b in page.blocks if b.left > mid - padding], cb_number)

# def left_column(page, padding=40):
#     cb_number = None
#     if page.header:
#         cb_number = page.header.tokens[0].text

#     mid = page.width / 2
#     col = Column([b for b in page.blocks if b.left <  mid - padding], cb_number)
#     _ = col.remove_header()
#     return col

# def split_columns(page, padding=40):
#     left = left_column(page, padding)
#     right = right_column(page, padding)
#     return left,right


# def merged_lines(block):
#     return [line for line in block.lines if line.is_merged]


# # def next_line_down(from_line, column, spacing=10):
# #     # always in the right column
# #     # the top of the next line should
# #     # be near the bottom of the line
    
# #     # hits = [line for line in column.lines
# #     #         if from_line.bottom == line.top]
# #     hits = [line for line in column.lines
# #             if line.top >= from_line.bottom
# #             and line.top <= from_line.bottom + spacing]
    
# #     if hits:
# #         return hits[0]



# def contains_line(span, line):
#     if line in span.objects:
#         return span
#     else:
#         for child in span.objects:
#             if (not(child.type) == 'token'):
#                 if contains_line(child, line):
#                     return child


# def move_line(new_line, target_line, position="above"):
#     target_bbox = target_line.bbox
#     new_line_bbox = new_line.bbox

#     # Construct a new bbox for the new line
#     if position == "above":
#         new_x_min = target_line.bbox.x_min
#         new_x_max = new_line.bbox.x_min + new_line.bbox.width
#         new_y_min = target_line.bbox.y_min - (2 * new_line.bbox.height)
#         new_y_max = new_y_min + new_line_bbox.height

#         new_bbox =  BBox(new_x_min, new_y_min, new_x_max, new_y_max)
#         new_line.bbox = new_bbox
#         return new_bbox
    

class Volume:
    pass

class Span2:
    def __init__(self, tree:etree.Element):
        self.root = tree
        bbox_string = self.root.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
        self.bbox = BBox(*values)
        word_spans = self.root.xpath(".//xhtml:span[@class='ocrx_word']", namespaces=ns)
        self.tokens = deque([Token(word) for word in word_spans])
        # self.words = deque([tok for tok in self.tokens if not(tok.is_punct)])


    @property
    def words(self):
        return deque([tok for tok in self.tokens if not(tok.is_punct)])

    def __repr__(self):
        string =  ' '.join([tok.text for tok in self.tokens])
        if len(string) > 20:
            string = f"{string[0:19]}..."
        return f"|{string}|"

    def __str__(self):
        return ' '.join([tok.text for tok in self.tokens])

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.min.x

    @property
    def right(self):
        return self.bbox.max.x - self.bbox.height

    @property
    def top(self):
        return self.bbox.min.x

    @property
    def bottom(self):
        return self.bbox.max.y

    @property
    def percent_greek(self):
        if len(self.words) == 0:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek()]
            return round(100 * (len(greek_words) / len(self.words)))

    @property
    def is_greek(self) -> bool:
        return self.percent_greek > 60

    def adjacent(self, span) -> bool:
        return abs(self.top - span.top) <= 10
            

class Line2(Span2):
    def __init__(self, tree:etree.Element):
        super().__init__(tree)
        # word_spans = self.root.xpath(".//xhtml:span[@class='ocrx_word']", namespaces=ns)
        # self.tokens = [Token(word) for word in word_spans]
        # self.words = [tok for tok in self.tokens if not(tok.is_punct)]

    def split(self, x):
        my_tokens = deepcopy(self.tokens)
        l_toks = deque(my_tokens)
        r_toks = deque()
        while len(r_toks) < x:
            r_toks.appendleft(l_toks.pop())

        return Line3(l_toks), Line3(r_toks)

    def split_old(self, x):
        line_left = Line3(self.tokens[:x])
        line_right = Line3(self.tokens[x:])
        return line_left, line_right

class Line3(Line2):
    def __init__(self, token_list):
        self.tokens = token_list
        # self.words = [tok for tok in self.tokens if not(tok.is_punct)]
        # calculate the BBox from the tokens
        self.bbox = BBox(self.tokens[0].bbox.min.x,
                         self.tokens[0].bbox.min.y,
                         self.tokens[-1].bbox.max.x,
                         self.tokens[-1].bbox.max.y)

        
class Line:
    def __init__(self, token_list):
        self.tokens = token_list
        # self.words = [tok for tok in self.tokens if not(tok.is_punct)]
        # calculate the BBox from the tokens
        self.bbox = BBox(self.tokens[0].bbox.min.x,
                         self.tokens[0].bbox.min.y,
                         self.tokens[-1].bbox.max.x,
                         self.tokens[-1].bbox.max.y)



    def __str__(self):
        txt = ''
        for token in self.tokens:
            txt += token.text_with_ws
        return txt

    def __repr__(self):
        txt = ''
        for token in self.tokens:
            txt += token.text_with_ws
        return f"|{txt}|"

    @property
    def words(self):
        return [tok for tok in self.tokens if not(tok.is_punct)]

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.min.x

    @property
    def right(self):
        return self.bbox.max.x - self.bbox.height

    @property
    def top(self):
        return self.bbox.min.x

    @property
    def bottom(self):
        return self.bbox.max.y

    @property
    def percent_greek(self):
        if len(self.words) == 0:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek()]
            return round(100 * (len(greek_words) / len(self.words)))

    @property
    def is_greek(self) -> bool:
        return self.percent_greek > 60

    def adjacent(self, span) -> bool:
        return abs(self.top - span.top) <= 10
    


    def split(self, x):
        left_line = Line(self.tokens[:x])
        right_line = Line(self.tokens[x:])
        return left_line, right_line
        

class Block2(Span2):
    def __init__(self, tree:etree.Element):
        super().__init__(tree)
        # self.root = tree
        self.lines =  [Line2(line) for line in self.root.xpath(".//xhtml:span[@class='ocr_line']",  namespaces=ns)]


    def __repr__(self):
        return f"|Block: {self.bbox}|"

    def display(self):
        txt = ''
        for i,l in enumerate(self.lines):
            # print(f"{i}\t{l}\n")
            txt += f"{i}\t{l}\n"
        print(txt)

    def mean_bottom(self):
        return statistics.mean([line.bottom for line in self.lines])
    

class Page:
    def __init__(self, tree:etree.Element):
        self.root = tree.xpath("//xhtml:div[@class='ocr_page']", namespaces=ns)[0]
        bbox_string = self.root.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
        self.bbox = BBox(*values)

        self.lines = []
        source_lines = self.root.xpath(".//xhtml:span[@class='ocr_line']",  namespaces=ns)
        for source_line in source_lines:
            source_tokens = source_line.xpath(".//xhtml:span[@class='ocrx_word']", namespaces=ns)
            self.lines.append(Line([Token(x) for x in source_tokens]))
        self.column_numbers = self.extract_column_numbers()

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.min.x

    @property
    def right(self):
        return self.bbox.max.x

    @property
    def percent_greek(self):
        if len(self.words) == 0:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek()]
            return round(100 * (len(greek_words) / len(self.words)))

    @property
    def midline(self):
        return self.width / 2

    @property
    def header_lines(self):
        return self.lines_adjacent(self.lines[0])

    def lines_adjacent(self, a_line):
        return [line for line in self.lines if abs(a_line.bottom - line.bottom) <= 10]

    def lines_aligned_left(self, x, padding=30):
        # return [line for line in self.lines if abs(line.left - x) <= padding]
        return [line for line in self.lines if line.left <= x]

    @property
    def left_column(self):
        left_lines = self.lines_aligned_left(self.midline / 2)
        # drop the first line; it is the header
        # return left_lines[1:]
        return left_lines

    @property
    def right_column(self):
        return [line for line in self.lines if abs(line.left - self.midline) <= 300]

    def extract_column_numbers(self):
        header_string = ' '.join([str(l) for l in self.header_lines])
        p = re.compile(r'^(\d+)\D+(\d+).*$')
        m = p.match(header_string)
        if m:
            left_column_num = m.group(1)
            right_column_num = m.group(2)
            return left_column_num, right_column_num

    def remove_header(self):
        for line in self.header_lines:
            self.lines.remove(line)
        return self.lines


    def display(self):
        for i,line in enumerate(self.lines):
            print(f"{i}\t{line}")


    @property
    def fused_lines(self):
        return [line for line in self.left_column if line.right > self.midline]


    def fix_fused_line(self, fused_line):
        split_point = round(len(fused_line.tokens) / 2)
        left_line, right_line = fused_line.split(split_point)
        if right_line.is_greek:
            while left_line.words[-1].is_greek():
                self.shift_word_right(left_line, right_line)
        else:
            while right_line.words[0].is_greek():
                self.shift_word_left(left_line, right_line)

        idx =self.lines.index(fused_line)
        del(self.lines[idx])
        self.lines.insert(idx, right_line)
        self.lines.insert(idx, left_line)
        
        
    def fix_fused_lines(self):
        fused_lines = self.fused_lines
        for fl in fused_lines:
            self.fix_fused_line(fl)

    def shift_word_right(self, line1, line2):
        word = line1.words[-1]
        index = line1.tokens.index(word)
        while len(line1.tokens) != index:
            tok = line1.tokens.pop()
            # line2.tokens.appendleft(tok)
            line2.tokens.insert(0, tok)

        
    def shift_word_left(self, line1, line2):
        word = line1.words[0]
        index = line1.tokens.index(word)
        while len(line1.tokens) != index:
            tok = line1.tokens.popleft()
            line2.tokens.append(tok)

        
            
    

class Page2:
    def __init__(self, tree:etree.Element):
        self.root = tree.xpath("//xhtml:div[@class='ocr_page']", namespaces=ns)[0]
        bbox_string = self.root.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
        self.bbox = BBox(*values)
        self.blocks = [Block2(b) for b in self.root.xpath("./xhtml:div[@class='ocrx_block']", namespaces=ns)]
        self.lines = flatten([block.lines for block in self.blocks])
        self.words = flatten([block.words for block in self.blocks])
        self.tokens = flatten([block.tokens for block in self.blocks])

    def __repr__(self):
        return f"|Page: {len(self.lines)} lines|"

    def display(self):
        txt = ''
        for i,line in enumerate(self.lines):
            txt += f"{i}\t{line}\n"
        print(txt)

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.min.x

    @property
    def right(self):
        return self.bbox.max.x

    @property
    def percent_greek(self):
        if len(self.words) == 0:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek()]
            return round(100 * (len(greek_words) / len(self.words)))

    @property
    def midline(self):
        return self.width / 2

    @property
    def header_lines(self):
        first_block = self.blocks[0]
        if 2 <= len(first_block.lines) <= 4:
            return first_block

    def lines_adjacent(self, a_line):
        return [line for line in self.lines if abs(a_line.bottom - line.bottom) <= 10]

    def lines_aligned_left(self, x, padding=30):
        # return [line for line in self.lines if abs(line.left - x) <= padding]
        return [line for line in self.lines if line.left <= x]

    @property
    def left_column(self):
        left_lines = self.lines_aligned_left(self.midline / 2)
        # drop the first line; it is the header
        return left_lines[1:]

    @property
    def right_column(self):
        return [line for line in self.lines if abs(line.left - self.midline) <= 300]

    @property
    def fused_lines(self):
        return [line for line in self.left_column if line.right > self.midline]


    def fix_fused_line(self, fused_line):
        split_point = round(len(fused_line.tokens) / 2)
        left_line, right_line = fused_line.split(split_point)
        if right_line.is_greek:
            while left_line.words[-1].is_greek():
                self.shift_word_right(left_line, right_line)
        else:
            while right_line.words[0].is_greek():
                self.shift_word_left(left_line, right_line)

        idx =self.lines.index(fused_line)
        del(self.lines[idx])
        self.lines.insert(idx, right_line)
        self.lines.insert(idx, left_line)
        
        
    def fix_fused_lines(self):
        fused_lines = self.fused_lines
        for fl in fused_lines:
            self.fix_fused_line(fl)

    def shift_word_right(self, line1, line2):
        word = line1.words[-1]
        index = line1.tokens.index(word)
        while len(line1.tokens) != index:
            tok = line1.tokens.pop()
            line2.tokens.appendleft(tok)

        
    def shift_word_left(self, line1, line2):
        word = line1.words[0]
        index = line1.tokens.index(word)
        while len(line1.tokens) != index:
            tok = line1.tokens.popleft()
            line2.tokens.append(tok)

        

        
    


def fix_entities(xml_string:str) -> str:
    # Remove XML declaration to avoid ValueError
    xml_string = re.sub(r'<\?xml.*?\?>', '', xml_string, flags=re.DOTALL)
    # Replace bad entities (example: replace &shy; with actual soft hyphen)
    xml_string = xml_string.replace("&shy;", "\u00AD")
    xml_string = xml_string.replace("&quot;", "\u0022")
    return xml_string
        

def load_page_file(page_file:Path):
    with page_file.open('r') as pf:
        raw_data = pf.read()
        clean_data = fix_entities(raw_data)
        tree = etree.fromstring(clean_data)
    return tree





pfile = Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148/00000102.html')
page_root = load_page_file(pfile)
p1 = Page2(page_root)
p2 = Page(page_root)
