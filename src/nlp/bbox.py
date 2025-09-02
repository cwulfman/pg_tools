from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int
    

@dataclass
class BBox:
    min: Point
    max: Point

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def left(self):
        return self.min.x

    @property
    def right(self):
        return self.max.x

    @property
    def top(self):
        return self.min.y

    @property
    def bottom(self):
        return self.max.y
    

    def __init__(self, x_min:int, y_min:int, x_max:int, y_max:int):
        self.min = Point(x_min, y_min)
        self.max = Point(x_max, y_max)

    def contains(self, inner_bbox):
        condition1 = self.left <= inner_bbox.left
        condition2 = self.right >= inner_bbox.right
        condition3 = self.top <= inner_bbox.top
        condition4 = self.bottom >= inner_bbox.bottom
        return all([condition1, condition2, condition3, condition4])

    def contained_by(self, outer_bbox):
        return outer_bbox.contains(self)

    def intersects_vertically(self, other):
        return (self.max.y > other.min.y) or (other.max.y < self.min.y)

    def intersects_horizontally(self, other):
        return (self.max.y > other.min.x) or (other.max.x < self.min.x)
    
    def intersects(self, other):
        return self.intersects_vertically(other) or self.intersects_horizontally(other)

    def is_horizontally_centered_within(self, outer_bbox, tolerance:int=0):
        left_distance = abs(self.left - outer_bbox.left)
        right_distance = abs(outer_bbox.right - self.right)
        return (self.contained_by(outer_bbox) and
                abs(right_distance - left_distance) <= tolerance)


    def is_vertically_centered_within(self, outer_bbox, tolerance:int=0):
        top_distance = outer_bbox.top - self.top
        bottom_distance = outer_bbox.bottom - self.bottom
        return (self.contained_by(outer_bbox) and
                abs(bottom_distance - top_distance) <= tolerance)



    def is_aligned_left(self, other, tolerance:int=0):
        return abs(self.left - other.left) <= tolerance

    def is_aligned_right(self, other, tolerance:int=0):
        return abs(self.right - other.right) <= tolerance

    def is_aligned_top(self, other, tolerance:int=0):
        return abs(self.top - other.top) <= tolerance

    def is_aligned_bottom(self, other, tolerance:int=0):
        return abs(self.bottom - other.bottom) <= tolerance


    def is_to_the_right_of(self, other, tolerance=0):
        return self.left - other.right <= tolerance

    def is_to_the_left_of(self, other, tolerance=0):
        return other.left - self.right <= tolerance

    def is_above(self, other, tolerance=0):
        return self.bottom - other.top <= tolerance
    
    def is_below(self, other, tolerance=0):
        return other.bottom - self.top <= tolerance
    

    def is_adjacent_right(self, other, side, tolerance:int=0):
        """Other box is next to me on the right."""
        pass
        
        
    def alignment_with(self, other_box, tolerance:int=0):
        alignments = []

        if self.contains(other_box):
            alignments.append('contains')

        if self.contained_by(other_box):
            alignments.append('contained_by')

        if self.is_horizontally_centered_within(other_box, tolerance=tolerance):
            alignments.append('horizontally_centered_within')
            
        if self.is_vertically_centered_within(other_box, tolerance=tolerance):
            alignments.append('vertically_centered_within')

        if self.is_aligned_left(other_box, tolerance=tolerance):
            alignments.append('left')
            
        if self.is_aligned_right(other_box, tolerance=tolerance):
            alignments.append('right')
            
        if self.is_aligned_top(other_box, tolerance=tolerance):
            alignments.append('top')
            
        if self.is_aligned_bottom(other_box, tolerance=tolerance):
            alignments.append('bottom')

        return alignments
        
