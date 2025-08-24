from copy import deepcopy
from nlp.utils import percent_greek
from nlp.span import Span

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


    def preceeds(self, other, padding=5):
        """Returns True if the other line
        is next to me on the right."""
        my_box = self.bbox
        other_box = other.bbox

        return my_box.is_to_the_left_of(other_box, tolerance=padding)
