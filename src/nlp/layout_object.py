from lxml import etree
from nlp.bbox import BBox

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
    
