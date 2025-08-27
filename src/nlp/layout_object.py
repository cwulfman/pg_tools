from lxml import etree
from nlp.bbox import BBox
from nlp.style import Style

class LayoutObject:
    def __init__(self, element:etree.Element | None):
        self.bbox = BBox(0,0,0,0)
        if element is not None:
            bbox_string = element.get('title').split(';')[0].split(' ')[1:]
            values = [int(v) for v in bbox_string]
            self.bbox = BBox(*values)
            self._style = {}
            style_string = element.get('style')
            if style_string:
                self._style = Style(style_string)
            self.parent:LayoutObject | None = None
            self.type:str = element.get('class')

    # def reset_bbox(self):
    #     if self.tokens:
    #         x_min = self.tokens[0].left
    #         y_min = self.tokens[0].top
    #         x_max = self.tokens[-1].right
    #         y_max = self.tokens[-1].bottom
    #         self.bbox = BBox(x_min, y_min, x_max, y_max)


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

    @property
    def style(self):
        if self._style:
            return self._style
        elif self.parent:
            return self.parent.style
        else:
            return {}
