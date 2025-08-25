import re
from lxml import etree
from nlp.utils import ns, percent_greek
from nlp.span import Span
from nlp.token import Token
from nlp.bbox import BBox
from nlp.column import Column



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
    def running_head_old(self):
        p = re.compile(r"\D+")
        txt = ''
        for linenum in range(0,4):
            hits = p.findall(str(self.lines[linenum]).strip())
            if hits:
                txt += ' '.join([hit for hit in hits])
        return txt

    @property
    def running_head(self):
        ptop = self.print_region.top
        header_line_height = 35
        return [line for line in self.lines if line.top == ptop and line.height <= header_line_height]


    @property
    def left_column(self):
        left_blocks = self.lines_aligned_left(self.midline / 2)
        # drop the first line; it is the header
        # return left_lines[1:]
        return Column(left_blocks, 'left', self.column_numbers.get('left'))

    # def left_lines(self, left_pad=20):
    #     l1 = self.left + self.margin_left
    #     l2 = l1 + left_pad
    #     return [line for line in self.lines
    #             if line.left >= l1
    #             and line.left < l2]

    def aligned_left(self, line, tolerance=20):
        return line.left - self.print_region.left <= tolerance

    def aligned_right(self, line, tolerance=10):
        return abs(self.print_region.right - line.right) <= tolerance
    
    def left_lines(self, tolerance=30):
        return [line for line in self.lines
                if self.aligned_left(line, tolerance=tolerance)]

    def right_lines(self, tolerance=10):
        return [line for line in self.lines
                if self.aligned_right(line, tolerance=tolerance)]

    def left_column_new(self):
        lines = self.left_lines(tolerance=50)
        return Column(lines, 'left', self.column_numbers.get('left'))

    def right_column_new(self):
        lines = self.right_lines(tolerance=50)
        return Column(lines, 'right', self.column_numbers.get('right'))

    def columns_new(self):
        return self.left_column_new(), self.right_column_new()

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
        try:
            next_line = sorted_lines[idx+2]
            next_idx = next_line.parent.index(next_line)
            next_line.parent.insert(next_idx, righty)

        except IndexError:
            # the fused line is the last line;
            # just insert the right line after the left
            sorted_lines[idx].parent.append(righty)



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
        

    def detect_title_lines(self, start:int=3, end:int=-20):
        centered_lines = [line for line in self.lines[start:end]
                 if line.bbox.is_horizontally_centered_within(self.print_region, 100)
                 and str(line).strip().isupper()]
        return [line for line in centered_lines if line not in self.running_head]

    def cluster_lines(self, lines):
        clusters = []
        cluster = []

        for i in range(0, len(lines) - 1):
            cluster.append(lines[i])
            spacing = lines[i+1].top - lines[i].bottom
            # look for double spacing
            if spacing > (lines[i].height * 2):
                clusters.append(cluster)
                cluster = []
        return clusters


    @property
    def titles(self):
        title_lines = self.detect_title_lines()
        if title_lines:
            return self.cluster_lines(title_lines)


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


