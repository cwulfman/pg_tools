from pathlib import Path
from nlp import Line
from nlp.bbox import BBox
from pg import Volume, Page


volpath = Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148')
vol:Volume = Volume(volpath)


def test_alignment():
    p = vol.page(71)._nlp_page
    p.repair_fused_lines()
    right_line = p.lines[39]
    left_line = p.lines[40]

    assert p.aligned_left(left_line) is True
    assert p.aligned_left(right_line) is False

    assert p.aligned_right(right_line) is True
    assert p.aligned_right(left_line) is False
    
    left_lines = p.left_lines()
    right_lines = p.right_lines()

    assert left_line in left_lines
    assert right_line not in left_lines

    assert right_line in right_lines
    assert left_line not in right_lines


def test_indented():
    p = vol.page(71)._nlp_page
    p.repair_fused_lines()
    indented_line = p.lines[8]

    assert p.aligned_left(indented_line, tolerance=20) is False
    assert p.aligned_left(indented_line, tolerance=50) is True

def test_columns():
    p = vol.page(71)._nlp_page
    p.repair_fused_lines()

    left_column = p.left_column_new()
    breakpoint()
