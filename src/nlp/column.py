from nlp import flatten
from nlp.line import Line
from nlp.token import Token



class Column:
    def __init__(self, lines, side=None, number=None):
        self.lines = lines
        self.side = side
        self.number = number

    def __len__(self) -> int:
        return len(self.lines)

    def __repr__(self):
        return f"<Column side='{self.side}' n='{self.number}'>"
        
    def __str__(self):
        coltext =''
        if self.number and self.number.isdigit():
            coltext += f"<cb n='{self.number}' />\n"
        else:
            coltext += "<cb/>\n"

        coltext += '\n'.join([str(line) for line in self.lines])
        return coltext

    @property
    def tokens(self) -> list[Token] | None:
        if self.lines is None:
            return None
        else:
            return flatten(line.tokens for line in self.lines)

    @property
    def words(self) -> list[Token] | None:
        if self.lines is None:
            return None
        else:
            return flatten(line.words for line in self.lines)


    @property
    def percent_greek(self) -> int:
        if self.words is None:
            return 0
        else:
            greek_words = [word for word in self.words if word.is_greek]
            return round(100 * (len(greek_words) / len(self.words)))

