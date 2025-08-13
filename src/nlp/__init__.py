from pathlib import Path
import unicodedata
from copy import deepcopy
from lxml import etree
from dataclasses import dataclass
from typing import Iterator

@dataclass(frozen=True)
class BBox:
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    @property
    def width(self) -> int:
        return self.x_max - self.x_min

    @property
    def height(self) -> int:
        return self.y_max - self.y_min

    def to_xywh(self) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) tuple."""
        return (self.x_min, self.y_min, self.width, self.height)

    # --- Drop-in tuple-like behavior ---
    def __iter__(self) -> Iterator[int]:
        yield self.x_min
        yield self.y_min
        yield self.x_max
        yield self.y_max

    def __getitem__(self, index: int) -> int:
        return (self.x_min, self.y_min, self.x_max, self.y_max)[index]

    def __len__(self) -> int:
        return 4



class Token:
    def __init__(self, element:etree.Element) -> None:
        self.type = 'token'
        self.element = element
        self.text = element.text
        self.tail = element.tail
        bbox_string = element.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
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
        self.parent = None
        self.index = 0
        self.type:str = element.get('class')
        self._element:etree.Element = element
        bbox_string = element.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
        self.bbox = BBox(*values)
        children = [child for child in element if child.get('class') is not None]
        self.objects = []
        for i,child in enumerate(children):
            object = genObject(child, i)
            object.parent = self
            self.objects.append(object)
        
        # self.objects = [genObject(child) for child in element if child.get('class') is not None]


    def __repr__(self):
        return f"<{self.type} len={len(self.objects)}>"

    def __str__(self):
        return ' '.join([tok.text for tok in self.tokens])


    @property
    def top(self):
        return self.bbox.y_min

    @property
    def bottom(self):
        return self.bbox.y_max

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.x_min

    @property
    def right(self):
        return self.bbox.x_max

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
            greek_words = [word for word in words if word.is_greek(threshold)]
            return (len(greek_words) / len(words)) >= threshold




            

class Page(Span):
    def __init__(self, element:etree.Element, page_number=None):
        super().__init__(element)
        self.number = page_number
        self._columns = None

    def __str__(self):
        page = ''
        for o in self.objects:
            page += str(o)
        return page

    @property
    def columns(self):
        if self._columns is None:
            self._columns = {}
            left,right = split_columns(self)
            self._columns['left'] = left
            self._columns['right'] = right
        return self._columns

    @property
    def greek_columns(self):
        hits = []
        for side in ['left', 'right']:
            if self.columns[side].is_greek():
                hits.append(self.columns[side])
        return hits
                

    @property
    def blocks(self):
        return [o for o in self.objects if o.type == 'ocrx_block']


    def serialize(self, dir:Path, **kwargs):
        
        if self.lines:
            header = self.columns['left'].remove_header()
            greek_columns = self.greek_columns
        else:
            header = None
            greek_columns = []

        fname = Path(str(self.number))
        file_path = dir / fname.with_suffix('.xml')
        with file_path.open('w+', encoding='utf-8') as f:
            f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            f.write("<text>\n")
            f.write(f"<pb n='{self.number}'/>\n")
            if header:
                f.write(header)
            for column in greek_columns:
                f.write('<cb/>\n')
                f.write(str(column))
            f.write("</text>")

    def repair_fused_line(self, fused_line):
        left_line, right_line = split_line(fused_line)
        left_column, right_column = split_columns(self)
        left_block,left_idx = left_column.line_index(fused_line)

        target = left_block.objects[left_idx]
        move_line(left_line, target)
        if left_idx > len(left_block.objects):
            left_block.objects.append(left_line)
        else:
            left_block.objects[left_idx] = left_line

        # breakpoint()
        pass

        right_block,right_idx = right_column.line_after_index(right_line)
        target = right_block.objects[right_idx]
        move_line(right_line,target)
        right_block.objects.insert(right_idx, right_line)

        return left_line, right_line


    def repair_fused_lines(self):
        fused_lines = merged_lines(self)
        for fused_line in fused_lines:
            self.repair_fused_line(fused_line)
        

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

    



class Column:
    def __init__(self, blocks):
        self.blocks = blocks
        self._lines = None

    def __repr__(self):
        return f"<column len={len(self.blocks)}>"
        
    def __str__(self):
        return '\n'.join([str(b) for b in self.blocks])

    @property
    def lines(self):
        if self._lines is None:
            self._lines = []
            for o in self.blocks:
                self._lines = self._lines + o.lines
        return self._lines


    def remove_header(self):
        self.blocks.pop(0)
        self._lines = None

    def line_index(self, line):
        # search the lines in the column
        # get the index of the line in its parent block
        idx = line.parent.objects.index(line)
        return line.parent, idx
        # for block in self.blocks:
        #     if contains_line(block, line):
        #         index_in_block = block.lines.index(line)
        #         return block,index_in_block

    def line_after_index(self,from_line, spacing=10):
        # the top of the next line
        # should be roughly the same
        # as the bottom of the line.
        hits = [line for line in self.lines
                if line.top >= from_line.bottom
                and line.top <= from_line.bottom + spacing]

        # breakpoint()

        if hits:
            next_line = hits[0]
        else:
            next_line = self.lines[-1]

        next_line_parent = next_line.parent
        idx = next_line_parent.objects.index(next_line)
        return next_line_parent, idx
    


    # def is_greek(self, threshold = .5):
    #     if len(self.blocks) == 0:
    #         return False
    #     else:
    #         greek_blocks = [b for b in self.blocks if b.is_greek()]
    #         return (len(greek_blocks) / len(self.blocks)) >= threshold


    def is_greek(self, threshold = .5):
        if len(self.lines) == 0:
            return False
        else:
            greek_lines = [line for line in self.lines if line.is_greek()]
            return (len(greek_lines) / len(self.lines)) >= threshold




def genObject(element:etree.Element, index):
    match element.get('class'):
        case 'ocr_page':
            page:Page = Page(element)
            page.index = index
            return page

        case 'ocrx_block':
            block:Block = Block(element)
            block.index = index
            return block

        case 'ocrx_word':
            token = Token(element)
            return token

        case 'ocr_line':
            line = Line(element)
            line.index = index
            return line

        case 'ocr_par':
            par = Par(element)
            par.index = index
            return par

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


# def split_line_from_left(line):
#     """returns two new line objects."""

#     # calculate the middle
#     idx = 1
#     tokens = line.objects
#     v = tokens[0:idx]
#     while (percent_greek(v) > 0.9):
#         idx += 1
#         v = tokens[0:idx]

#     mid = idx-1

#     left_line = deepcopy(line)
#     left_line.objects = left_line.objects[0:mid]

#     right_line = deepcopy(line)
#     right_line.objects = right_line.objects[mid:len(right_line.objects)]

#     # left_string = tokens[0:idx-1]
#     # right_string = tokens[idx-1:len(tokens)]
#     # return left_string,right_string
#     return left_line,right_line


# def split_line_from_right(line):
#     """returns two new line objects."""
#     # calculate the middle


#     for mid,tok in enumerate(line.tokens):
#         if tok.is_punct:
#             next
#         if tok.is_greek():
#             break

#     left_line = deepcopy(line)
#     left_line.objects = left_line.objects[0:mid]

#     right_line = deepcopy(line)
#     right_line.objects = right_line.objects[mid:len(right_line.objects)]
#     return left_line,right_line


def split_line(line):
    left_line = deepcopy(line)
    right_line = deepcopy(line)

    if line.starts_greek:
        indexes = [line.objects.index(word) for word in line.words if word.is_greek()]
        greek_span = left_line.objects[indexes[0]:indexes[-1]+1]
        latin_span = right_line.objects[indexes[-1] + 1:len(left_line.objects)]
        left_line.objects = greek_span
        right_line.objects = latin_span

    else:
        indexes = [line.objects.index(word) for word in line.words if not(word.is_greek())]
        if indexes:
            latin_span = right_line.objects[indexes[0]:indexes[-1]+1]
            greek_span = left_line.objects[indexes[-1] + 1:len(left_line.objects)]
            left_line.objects = latin_span
            right_line.objecs = greek_span
        else:
            # breakpoint()
            pass

    return left_line,right_line
        

def right_column(page, padding=40):
    mid = page.width / 2
    return Column([b for b in page.blocks if b.left > mid - padding])

def left_column(page, padding=40):
    mid = page.width / 2
    return Column([b for b in page.blocks if b.left <  mid - padding])

def split_columns(page, padding=40):
    left = left_column(page, padding)
    right = right_column(page, padding)
    return left,right


def merged_lines(block):
    return [line for line in block.lines if line.is_merged]


# def next_line_down(from_line, column, spacing=10):
#     # always in the right column
#     # the top of the next line should
#     # be near the bottom of the line
    
#     # hits = [line for line in column.lines
#     #         if from_line.bottom == line.top]
#     hits = [line for line in column.lines
#             if line.top >= from_line.bottom
#             and line.top <= from_line.bottom + spacing]
    
#     if hits:
#         return hits[0]



def contains_line(span, line):
    if line in span.objects:
        return span
    else:
        for child in span.objects:
            if (not(child.type) == 'token'):
                if contains_line(child, line):
                    return child


def move_line(new_line, target_line, position="above"):
    target_bbox = target_line.bbox
    new_line_bbox = new_line.bbox

    # Construct a new bbox for the new line
    if position == "above":
        new_x_min = target_line.bbox.x_min
        new_x_max = new_line.bbox.x_min + new_line.bbox.width
        new_y_min = target_line.bbox.y_min - (2 * new_line.bbox.height)
        new_y_max = new_y_min + new_line_bbox.height

        new_bbox =  BBox(new_x_min, new_y_min, new_x_max, new_y_max)
        new_line.bbox = new_bbox
        return new_bbox
    
