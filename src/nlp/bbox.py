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

    def is_horizontally_centered_within(self, outer_bbox, tolerance:int=0):
        left_distance = self.left - outer_bbox.left
        right_distance = outer_bbox.right - self.right
        return abs(right_distance - left_distance) <= tolerance


    def is_vertically_centered_within(self, outer_bbox, tolerance:int=0):
        top_distance = self.top - outer_bbox.top
        bottom_distance = outer_bbox.bottom - self.bottom
        return abs(bottom_distance - top_distance) <= tolerance


    def is_aligned_left(self, other, tolerance:int=0):
        return abs(self.left - other.left) <= tolerance

    def is_aligned_right(self, other, tolerance:int=0):
        return abs(self.right - other.right) <= tolerance

    def is_aligned_top(self, other, tolerance:int=0):
        return abs(self.top - other.top) <= tolerance

    def is_aligned_bottom(self, other, tolerance:int=0):
        return abs(self.bottom - other.bottom) <= tolerance


    def is_adjacent_right(self, other, side):
        """Other box is next to me on the right."""
        pass
        
        
