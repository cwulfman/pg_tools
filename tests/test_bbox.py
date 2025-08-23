from nlp.bbox import BBox

def test_contains():
    outer_bbox = BBox(5,5,20,20)
    inner_bbox = BBox(6,6,15,15)
    overlapping_bbox = BBox(4,4,15,150)

    assert outer_bbox.contains(inner_bbox)
    assert inner_bbox.contained_by(outer_bbox)

    assert inner_bbox.contains(outer_bbox) is False
    assert outer_bbox.contained_by(inner_bbox) is False
           
    assert outer_bbox.contains(overlapping_bbox) is False
    assert outer_bbox.contained_by(overlapping_bbox) is False


def test_vertical_intersection():
    a = BBox(100,100, 200,200)
    b = BBox(150,150, 250,250)
    c = BBox(500,500, 600,600)

    assert a.intersects_vertically(b)
    assert a.intersects_vertically(c) is False


def test_horizontal_intersection():
    a = BBox(100,100, 200,200)
    b = BBox(150,150, 250,250)
    c = BBox(500,500, 600,600)

    assert a.intersects_horizontally(b)
    assert a.intersects_horizontally(c) is False
    
def test_intersection():
    a = BBox(100,100, 200,200)
    b = BBox(150,150, 250,250)
    c = BBox(500,500, 600,600)

    assert a.intersects(b)


def test_horizontally_centered_within():
   outer_bbox = BBox(0,0, 20,20)
   centered_bbox = BBox(5,5, 15, 20)
   uncentered_bbox = BBox(7,0, 11,10)
   not_within_bbox = BBox(5,5, 30,30)

   assert centered_bbox.is_horizontally_centered_within(outer_bbox)
   assert uncentered_bbox.is_horizontally_centered_within(outer_bbox) is False
   assert uncentered_bbox.is_horizontally_centered_within(outer_bbox, tolerance=3) is True
   assert not_within_bbox.is_horizontally_centered_within(outer_bbox, tolerance=3) is False

# def test_vertically_centered_within():
#     outer_bbox = BBox(0,0, 20,20)
#     centered_bbox = BBox(5,5, 15, 15)
#     uncentered_bbox = BBox(0,5, 11, 16)
#     not_within_bbox = BBox(5,5, 30,30)

#     assert centered_bbox.is_vertically_centered_within(outer_bbox)
#     assert uncentered_bbox.is_vertically_centered_within(outer_bbox) is False
#     assert uncentered_bbox.is_vertically_centered_within(outer_bbox, tolerance=2) is True
#     assert not_within_bbox.is_vertically_centered_within(outer_bbox, tolerance=3) is False

def test_alignment():
    main_box = BBox(30,30,50,50)
    left_box = BBox(33,35,90,90)
    right_box = BBox(0,0, 50,60)
    top_box = BBox(16,31, 80,85)
    bottom_box = BBox(10,10, 31,53)
    unaligned_box = BBox(100,100,200,200)

    assert main_box.is_aligned_left(left_box) is False # not exactly aligned
    assert main_box.is_aligned_left(left_box, tolerance=5) is True # within tolerance
    assert main_box.is_aligned_right(right_box)
    assert main_box.is_aligned_top(top_box, tolerance=5) is True # within tolerance
    assert main_box.is_aligned_bottom(bottom_box, tolerance=5) is True # within tolerance

    assert main_box.is_aligned_left(unaligned_box) is False
    assert main_box.is_aligned_left(unaligned_box, tolerance=5) is False
    assert main_box.is_aligned_right(unaligned_box) is False
    assert main_box.is_aligned_right(unaligned_box, tolerance=5) is False
    assert main_box.is_aligned_top(unaligned_box) is False
    assert main_box.is_aligned_top(unaligned_box, tolerance=5) is False
    assert main_box.is_aligned_bottom(unaligned_box) is False
    assert main_box.is_aligned_bottom(unaligned_box, tolerance=5) is False
