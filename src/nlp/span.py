from copy import deepcopy, copy
from collections import deque
from lxml import etree
from nlp.utils import genObject
from nlp.layout_object import LayoutObject
from nlp.bbox import BBox
from nlp.token import Token


class Span(LayoutObject):
    def __init__(self, element: etree.Element | None):
        super().__init__(element)
        self.objects:deque = deque()
        if element is not None:
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

    def __len__(self) -> int:
        return len(self.objects)
    


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
            if isinstance(obj, Token):
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
        if len(self.objects) > 0:
            object = self.objects.pop()
            self.reset_bbox()
            object.parent = None
            return object
            
    def popleft(self):
        if len(self.objects) > 0:
            object = self.objects.popleft()
            self.reset_bbox()
            object.parent = None
            return object

    def peek(self):
        if len(self.objects) > 0:
            return self.objects[-1]

    def peekleft(self):
        if len(self.objects) > 0:
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
