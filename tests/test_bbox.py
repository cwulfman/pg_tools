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


def test_horizontally_centered():
    outer_bbox = BBox(0,0, 20,20)
    centered_bbox = BBox(5,5, 15, 20)
    uncentered_bbox = BBox(7,0, 11,10)

    assert centered_bbox.is_horizontally_centered_within(outer_bbox)
    assert uncentered_bbox.is_horizontally_centered_within(outer_bbox) is False
    assert uncentered_bbox.is_horizontally_centered_within(outer_bbox, tolerance=3) is True

def test_vertically_centered():
    outer_bbox = BBox(0,0, 20,20)
    centered_bbox = BBox(5,5, 15, 15)
    uncentered_bbox = BBox(0,5, 11, 16)

    assert centered_bbox.is_vertically_centered_within(outer_bbox)
    assert uncentered_bbox.is_vertically_centered_within(outer_bbox) is False
    assert uncentered_bbox.is_vertically_centered_within(outer_bbox, tolerance=2) is True
