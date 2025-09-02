from nlp.utils import percent_greek
from nlp.span import Span
from nlp.bbox import BBox
from lxml import etree

class Line(Span):
    def __init__(self, element: etree.Element | None):
        super().__init__(element)
        if element is None:
            self.parent = None
        self.type = 'ocr_line'

    def __str__(self):
        p = ''
        for o in self.objects:
            p = p + str(o)
        # p += '\n'
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
        line_left = Line(None)
        line_right = Line(None)

        line_left.objects = self.objects.copy()
        line_left.reset_bbox()

        mid = round(self.length / 2)


        while line_left.length > mid:
            tok = line_left.pop()
            if tok:
                line_right.prepend(tok)

        line_left.reset_bbox()
        line_right.reset_bbox()

        return line_left, line_right

    def unfuse(self):
        left,right = self.split()
        if self.starts_greek:
            while right.percent_greek > 0:
                tok = right.popleft()
                if tok:
                    left.append(tok)
                while right.peekleft() and right.peekleft().is_punct:
                    tok = right.popleft()
                    if tok:
                        left.append(tok)
                        
        elif self.ends_greek:
            while left.percent_greek > 0:
                tok = left.pop()
                if tok:
                    right.prepend(tok)
                    while left.peek() and left.peek().is_punct:
                        tok = left.pop()
                        if tok:
                            right.prepend(tok)
        else:
            pass

        return left, right


    def preceeds(self, other, padding=5):
        """Returns True if the other line
        is next to me on the right."""
        my_box = self.bbox
        other_box = other.bbox

        return my_box.is_to_the_left_of(other_box, tolerance=padding)
