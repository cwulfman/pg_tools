from collections import deque
import statistics
from pathlib import Path
import re
import unicodedata
from copy import deepcopy, copy
from lxml import etree
from typing import Iterator
from nlp.bbox import BBox

ns = {"xhtml": "http://www.w3.org/1999/xhtml"}

def flatten(a):
    res = []
    for x in a:
        if isinstance(x, list):
            res.extend(flatten(x))
        else:
            res.append(x)
    return res


class LayoutObject:
    def __init__(self, element:etree.Element):
        bbox_string = element.get('title').split(';')[0].split(' ')[1:]
        values = [int(v) for v in bbox_string]
        self.bbox = BBox(*values)
        self.parent:LayoutObject | None = None
        self.type:str = element.get('class')

    def reset_bbox(self):
        if self.tokens:
            x_min = self.tokens[0].left
            y_min = self.tokens[0].top
            x_max = self.tokens[-1].right
            y_max = self.tokens[-1].bottom
            self.bbox = BBox(x_min, y_min, x_max, y_max)


    @property
    def top(self):
        return self.bbox.top

    @property
    def bottom(self):
        return self.bbox.bottom

    @property
    def width(self):
        return self.bbox.width

    @property
    def height(self):
        return self.bbox.height

    @property
    def left(self):
        return self.bbox.left

    @property
    def right(self):
        return self.bbox.right

    @property
    def parent_block(self):
        if self.parent is None:
            return None
        elif self.parent.type == 'ocrx_block':
            return self.parent
        else:
            return self.parent.parent_block
    


class Token(LayoutObject):
    def __init__(self, element:etree.Element):
        super().__init__(element)
        self.text = self.clean_text(element.text)
        self.tail = element.tail
        self.type = "token"


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
    def is_greek(self) -> bool:
        greek_count = 0
        alpha_count = 0
        threshold:float = 0.5
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

        
    def clean_text(self,text):
        # Replace bad entities (example: replace &shy; with actual soft hyphen)
        text = text.replace("&shy;", "\u00AD")
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text



class Span(LayoutObject):
    def __init__(self, element:etree.Element):
        super().__init__(element)
        self.objects:deque = deque()
        children = [child for child in element if child.get('class') is not None]
        for child in children:
            object = genObject(child)
            object.parent = self
            self.objects.append(object)

    def __repr__(self):
        return f"<{self.type} len={len(self.objects)}>"


    def __str__(self):
        txt = ''
        for object in self.objects:
            txt += str(object)
        return txt


    def reset_bbox(self):
        if len(self.objects) == 0:
            self.bbox = BBox(0,0,0,0)
        elif len(self.objects) == 1:
            obj = self.objects[0]
            self.bbox = copy(obj.bbox)
        else:
            first = self.objects[0]
            last = self.objects[-1]
            self.bbox = BBox(first.left, first.top, last.right, last.bottom)
            
    

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
    def blocks(self):
        block_list = []
        if self.type == 'ocrx_block':
            block_list.append(self)
        else:
            for o in self.objects:
                block_list = block_list + o.blocks
        return block_list
        
    

    def append(self, object:LayoutObject):
        object.parent = self
        self.objects.append(object)
        self.reset_bbox()
            

    def prepend(self, object:LayoutObject):
        object.parent = self
        self.objects.appendleft(object)
        self.reset_bbox()

    def pop(self):
        object = self.objects.pop()
        self.reset_bbox()
        object.parent = None
        return object
            
    def popleft(self):
        object = self.objects.popleft()
        self.reset_bbox()
        object.parent = None
        return object

    def peek(self):
        return self.objects[-1]

    def peekleft(self):
        return self.objects[0]

    def clear(self):
        self.objects.clear()
        self.reset_bbox()

    def index(self, x):
        return self.objects.index(x)

    def insert(self, i, x):
        self.objects.insert(i, x)
        self.reset_bbox()

    def remove(self, x):
        self.objects.remove(x)
        self.reset_bbox()

    def replace(self, a, b):
        idx = self.objects.index(a)
        self.objects.remove(a)
        self.objects.insert(idx, b)
        self.reset_bbox()
    

    

        
    @property
    def percent_greek(self):
        if len(self.words) == 0:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek]
            return round(100 * (len(greek_words) / len(self.words)))

    

class Line(Span):
    def __str__(self):
        p = ''
        for o in self.objects:
            p = p + str(o)
        p += '\n'
        return p

    def __repr__(self):
        txt = ''
        for token in self.tokens:
            txt += token.text_with_ws
        return f"|{txt}|"


    @property
    def length(self) -> int:
        return len(self.tokens)

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
    def is_fused(self) -> bool:
        condition1 = self.starts_greek and not(self.ends_greek)
        condition2 = not(self.starts_greek) and self.ends_greek
        return any([condition1, condition2])


    def split(self):
        line_left = deepcopy(self)
        line_right = deepcopy(self)

        mid = round(self.length / 2)

        line_right.objects.clear()
        while line_left.length > mid:
            line_right.prepend(line_left.pop())

        line_left.reset_bbox()
        line_right.reset_bbox()

        return line_left, line_right

    def unfuse(self):
        left,right = self.split()
        if self.starts_greek:
            while right.percent_greek > 0:
                left.append(right.popleft())
                while right.peekleft().is_punct:
                    left.append(right.popleft())
        elif self.ends_greek:
            while left.percent_greek > 0:
                right.prepend(left.pop())
                while left.peek().is_punct:
                    right.prepend(left.pop())
        else:
            pass

        return left, right
                    



        


class Page(Span):
    def __init__(self, tree:etree.Element, number:int=0):
        self.root = tree.xpath("//xhtml:div[@class='ocr_page']", namespaces=ns)[0]        
        super().__init__(self.root)
        self.number = number


    def __str__(self):
        page = ''
        for o in self.objects:
            page += str(o)
        return page


    @property
    def midline(self):
        return self.width / 2

    @property
    def margin_left(self):
        return self.left + min([line.left for line in self.lines])

    @property
    def margin_right(self):
        return self.right - max([line.right for line in self.lines])

    @property
    def margin_top(self):
        return self.top + min([line.top for line in self.lines])

    @property
    def margin_bottom(self):
        return self.bottom - max([line.bottom for line in self.lines])

    @property
    def print_region(self):
        return BBox(self.left + self.margin_left,
                    self.top + self.margin_top,
                    self.right - self.margin_right,
                    self.bottom - self.margin_bottom)

    def lines_adjacent(self, a_line):
        return [line for line in self.lines if abs(a_line.bottom - line.bottom) <= 10]

    
    @property
    def header_lines(self):
        return self.lines_adjacent(self.lines[0])

    def lines_aligned_left(self, x, padding=30):
        # return [line for line in self.lines if abs(line.left - x) <= padding]
        return [line for line in self.lines if line.left <= x]

    def blocks_aligned_left(self, x, padding=30):
        # return [line for line in self.lines if abs(line.left - x) <= padding]
        return [block for block in self.blocks if block.left <= x]


    @property
    def column_numbers(self):
        # p = re.compile(r'.*?(\d+).*^')
        col_nums = {}
        nums_left = re.findall(r"\d+", str(self.lines[0]).strip())
        nums_right = re.findall(r"\d+", str(self.lines[1]).strip())
        if nums_left:
            col_nums['left'] = nums_left[0]
        if nums_right:
            col_nums['right'] = nums_right[0]
        return col_nums


    @property
    def running_head(self):
        p = re.compile(r"\D+")
        txt = ''
        for linenum in range(0,4):
            hits = p.findall(str(self.lines[linenum]).strip())
            if hits:
                txt += ' '.join([hit for hit in hits])
        return txt


    @property
    def left_column(self):
        left_blocks = self.lines_aligned_left(self.midline / 2)
        # drop the first line; it is the header
        # return left_lines[1:]
        return Column(left_blocks, 'left', self.column_numbers.get('left'))

    def left_lines(self, left_pad=20):
        l1 = self.left + self.margin_left
        l2 = l1 + left_pad
        return [line for line in self.lines
                if line.left >= l1
                and line.left < l2]

    def columns(self):
        left_column = []
        right_column = []
        left_lines = self.left_lines()
        left_column = sorted(left_lines, key=lambda x: x.top)
        for left_line in left_column:
            adjacents = self.lines_adjacent(left_line)
            if len(adjacents) == 2:
                right_line = [line for line in adjacents
                              if line != left_line][0]
                right_column.append(right_line)
                
        return Column(left_column, 'left'), Column(right_column, 'right')
        
    
    @property
    def right_column(self):
        return Column([block for block in self.blocks if abs(block.left - self.midline) <= 300], 'right', self.column_numbers.get('right'))

    
    @property
    def greek_column(self):
        left_column = self.left_column
        if left_column and percent_greek(left_column.tokens) > .5:
            return left_column
        else:
            right_column = self.right_column
            if right_column and percent_greek(right_column.tokens) > .5:
                return right_column
            

    @property
    def fused_lines(self):
        fused = []
        for line in self.left_column.lines:
            condition1 = line.width > self.midline
            condition2 = len(line.tokens) > 4
            condition3 = line.is_fused
            if all([condition1, condition2, condition3]):
                fused.append(line)

        return fused

    def repair_fused_line(self, fused_line):
        lefty, righty = fused_line.unfuse()
        # Get an sorted list of the page lines,
        # ordered by line top. Replace the fused
        # line with the new left line, and insert
        # the right line above the line two lines later.
        sorted_lines = sorted(self.lines, key=lambda line: line.top)
        idx = sorted_lines.index(fused_line)
        sorted_lines[idx].parent.replace(fused_line, lefty)
        next_line = sorted_lines[idx+2]
        next_idx = next_line.parent.index(next_line)
        next_line.parent.insert(next_idx, righty)

    def repair_fused_lines(self):
        for line in self.fused_lines:
            self.repair_fused_line(line)

    @property
    def gutters(self):
        guts = []
        for line in self.lines:
            adjacents = self.lines_adjacent(line)
            if len(adjacents) == 2:
                adjacents.sort(key=lambda x: x.left)
                guts.append(adjacents[1].left - adjacents[0].right)
        return guts
        

    @property
    def has_columns(self):
        pass

    

    def analyze(self):
        pass
    


class BlankPage(Page):
    def __init__(self, tree:etree.Element, number:int=0):
        super().__init__(tree)

    # stunt all relevant properties and methods

    @property
    def midline(self):
        return 0

    @property
    def margin_left(self):
        return 0

    @property
    def margin_right(self):
        return 0

    @property
    def margin_top(self):
        return 0

    @property
    def margin_bottom(self):
        return 0

    @property
    def print_region(self):
        return BBox(0,0,0,0)

    def lines_adjacent(self, a_line):
        return None

    @property
    def header_lines(self):
        return None

    def lines_aligned_left(self, x, padding=30):
        return None

    def blocks_aligned_left(self, x, padding=30):
        return None

    @property
    def column_numbers(self):
        return None
    
    @property
    def running_head(self):
        return None

    @property
    def left_column(self):
        return None

    def left_lines(self, left_pad=20):    
        return None

    def columns(self):
        return None, None

    @property
    def right_column(self):
        return None

    @property
    def greek_column(self):
        return None

    @property
    def fused_lines(self):
        return None

    def repair_fused_line(self, fused_line):
        pass
    
    def repair_fused_lines(self):
        pass

    @property
    def gutters(self):
        return None

    @property
    def has_columns(self):
        return False

    
class Column:
    def __init__(self, blocks, side=None, number=None):
        self.blocks = blocks
        self.side = side
        self.number = number

    def __repr__(self):
        return f"<Column side='{self.side}' n='{self.number}'>"
        
    def __str__(self):
        coltext =''
        if self.number and self.number.isdigit():
            coltext += f"<cb n='{self.number}' />\n"
        else:
            coltext += "<cb/>\n"

        coltext += '\n'.join([str(b) for b in self.blocks])
        return coltext

    @property
    def tokens(self):
        return flatten(block.tokens for block in self.blocks)

    @property
    def words(self):
        return flatten(block.words for block in self.blocks)

    @property
    def lines(self):
        return flatten([block.lines for block in self.blocks])

    @property
    def percent_greek(self):
        if len(self.words) == 0:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek]
            return round(100 * (len(greek_words) / len(self.words)))


    def remove_header(self):
        if self.blocks:
            header = self.blocks.pop(0)
            self._lines = None
            return header
        else:
            return None

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
    

    


class Block(Span):
    def __init__(self, tree:etree.Element):
        super().__init__(tree)


    def __str__(self):
        # block = '<ab>'
        block = ''
        for o in self.objects:
            block += str(o)
        # block += '</ab>\n'
        return block
    

    @property
    def paras(self):
        return [o for o in self.objects if o.type == 'ocr_par']

    @property
    def lines(self):
        return flatten([para.lines for para in self.paras])
        
    @property
    def words(self):
        return flatten([para.words for para in self.paras])

    @property
    def tokens(self):
        return flatten([para.tokens for para in self.paras])

    


class Par(Block):
    def __str__(self):
        p = '\n'
        for o in self.objects:
            p = p + str(o)
        return p



        

def genObject(element:etree.Element):
    match element.get('class'):
        case 'ocr_page':
            page:Page = Page(element)
            return page

        case 'ocrx_block':
            block:Block = Block(element)
            return block

        case 'ocrx_word':
            token = Token(element)
            return token

        case 'ocr_line':
            line = Line(element)
            return line

        case 'ocr_par':
            par = Par(element)
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
            if tok.is_greek:
                greek_count += 1
        return greek_count / tok_count
    


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


def report(lines):
    print("i\tleft\ttop\twidth\tline")
    for i,l in enumerate(lines):
        print(f"{i}\t{l.left}\t{l.top}\t{l.width}\t{l}")
