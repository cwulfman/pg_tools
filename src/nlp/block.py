from lxml import etree
from nlp.span import Span
from nlp.utils import flatten

class Block(Span):
    def __init__(self, tree:etree.Element):
        super().__init__(tree)


    def __str__(self):
        block = ''
        for o in self.objects:
            block += str(o)
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

