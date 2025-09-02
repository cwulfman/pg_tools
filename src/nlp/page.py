import io
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
        self.type = "page"


    def __str__(self):
        page = ''
        for o in self.objects:
            page += str(o)
        return page


    @property
    def midline(self):
        if self.print_region is not None:
            return self.print_region.width / 2
        else:
           return self.width / 2

    def group_lines_by_baseline(self, tolerance = 10):
        if not self.lines:
            return []
        groups = []
        sorted_lines = sorted(self.lines, key=lambda x: x.bottom)
        current_group = [sorted_lines[0]]
        current_baseline = sorted_lines[0].bottom
        for line in sorted_lines[1:]:
            if abs(line.bottom - current_baseline) < tolerance:
                current_group.append(line)
            else:
                groups.append(current_group)
                current_group = [line]
                current_baseline = line.bottom
        return groups
                
    def group_lines_into_columns(self):
        groups = self.group_lines_by_baseline(tolerance=35)
        left_column = []
        right_column = []
        for g in groups:
            for line in g:
                if line.left < self.midline:
                    left_column.append(line)
                else:
                    right_column.append(line)
        return [left_column, right_column]
        


    @property
    def margin_left(self):
        if self.lines:
            return self.left + min([line.left for line in self.lines])
        else:
            return self.left

    @property
    def margin_right(self):
        if self.lines:
            return self.right - max([line.right for line in self.lines])
        else:
            return self.right

    @property
    def margin_top(self):
        if self.lines:
            return self.top + min([line.top for line in self.lines])
        else:
            return self.top

    @property
    def margin_bottom(self):
        if self.lines:
            return self.bottom - max([line.bottom for line in self.lines])
        else:
            return self.bottom

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
        if self.lines and len(self.lines) > 1:
            nums_left = re.findall(r"\d+", str(self.lines[0]).strip())
            nums_right = re.findall(r"\d+", str(self.lines[1]).strip())
            if nums_left:
                col_nums['left'] = nums_left[0]
                if nums_right:
                    col_nums['right'] = nums_right[0]
        return col_nums


    @property
    def running_head(self):
        ptop = self.print_region.top
        header_line_height = 35
        return [line for line in self.lines if line.top == ptop and line.height <= header_line_height]


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

    @property
    def left_column(self):
        lines = self.left_lines(tolerance=50)
        return Column(lines, 'left', self.column_numbers.get('left'))

    @property
    def right_column(self):
        lines = self.right_lines(tolerance=50)
        return Column(lines, 'right', self.column_numbers.get('right'))

    @property
    def columns(self):
        return self.left_column, self.right_column

    
    @property
    def greek_column(self):
        left_column = self.left_column
        if left_column and percent_greek(left_column.tokens) > .5:
            return left_column
        else:
            right_column = self.right_column
            if right_column and percent_greek(right_column.tokens) > .5:
                return right_column
            
    # some pages have two columns in Greek
    @property
    def greek_columns(self):
        columns = []
        left_column = self.left_column
        if left_column and percent_greek(left_column.tokens) > .5:
            columns.append(left_column)

        right_column = self.right_column
        if right_column and percent_greek(right_column.tokens) > .5:
            columns.append(right_column)

        return columns
            

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
            if next_line and next_line.parent:
                next_idx = next_line.parent.index(next_line)
                next_line.parent.insert(next_idx, righty)

        except IndexError:
            # the fused line is the last line;
            # just insert the right line after the left
            if sorted_lines[idx].parent:
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
        # centered_lines = [line for line in self.lines[start:end]
        centered_lines = [line for line in self.lines
                 if line.bbox.is_horizontally_centered_within(self.print_region, 100)
                 and str(line).strip().isupper()]
        return [line for line in centered_lines if line not in self.running_head]

    def cluster_lines(self, lines) -> list:
        clusters = []
        cluster = []
        prev_line = []
        
        for _,line in enumerate(lines):
            if len(cluster) == 0:
                cluster.append(line)
            else:
                current_line = line
                prev_line = cluster[-1]
                spacing = current_line.top - prev_line.bottom
                if spacing < current_line.height * 2:
                    cluster.append(current_line)
                else:
                    cluster.append(current_line)
                    clusters.append(cluster)
                    cluster = []
        return clusters

            
    @property
    def titles(self):
        detected_lines = self.detect_title_lines()
        if detected_lines:
            names = self.names_in_titles
            return [line for line in detected_lines if not line in names]
        else:
            return None

    @property
    def title_strings(self):
        title_strings = []
        detected_lines = self.detect_title_lines()
        if detected_lines:
            names = self.names_in_titles
            title_lines = [line for line in detected_lines if not line in names]
            title_clusters = self.cluster_lines(title_lines)
            if len(title_clusters) > 0:
                for cluster in title_clusters:
                        title_strings.append(' '.join([str(line).strip() for line in cluster]))
        return title_strings

    @property
    def names_in_titles(self):
        title_lines = self.detect_title_lines()
        return [line for line in title_lines if line.style.size > 10 and 'bold' in line.style.weight and str(line).isupper()]
        


    @property
    def has_columns(self):
        pass

    def analyze(self):
        pass


    def display(self):
        groups = self.group_lines_by_baseline(tolerance=35)
        for g in groups:
            for line in g:
                if line.left < self.midline:
                    print(line)
                else:
                    print(f"\t\t\t\t\t\t\t{line}")


    def xml(self, greek_only=True):
        self.repair_fused_lines()
        with io.StringIO() as buffer:
            buffer.write(f"<page n='{self.number}' ")
            if self.running_head:
                head_txt = ' '.join(str(line) for line in self.running_head)
                buffer.write(f"running_head='{head_txt.strip()}'")
            buffer.write(">\n")
            if greek_only is True:
                columns = self.greek_columns
            else:
                columns = self.columns

            if columns:
                for column in columns:
                    buffer.write(f"<column n='{column.number}' side='{column.side}'>")
                    buffer.write(str(column))
                    buffer.write("\n</column>\n")

            buffer.write("</page>\n")
            content = buffer.getvalue()
        return content
            

        


class BlankPage(Page):
    def __init__(self, tree:etree.Element| None, number:int=0):
        if tree is not None:
            super().__init__(tree, number)
        self.type = "blank"

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
    def lines(self):
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
    def greek_columns(self):
        return []

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
