from lxml import etree
from nlp.span import Span
from nlp.bbox import BBox


span1 = etree.XML("<span class='ocr_line' title='bbox 92 155 1695 196;x_wconf 91'><span class='ocrx_word' title='bbox 92 155 152 196;x_wconf 93'>στὸς</span> <span class='ocrx_word' title='bbox 168 155 221 196;x_wconf 97'>γὰρ</span> <span class='ocrx_word' title='bbox 235 155 310 196;x_wconf 95' >ἡμᾶς</span> <span class='ocrx_word' title='bbox 328 155 494 196;x_wconf 95'>ἐξηγόρασεν</span> <span class='ocrx_word' title='bbox 512 155 546 196;x_wconf 84' style='font-size:10pt;font-family:Times;font-style:bold'>ἐκ</span> <span class='ocrx_word' title='bbox 559 155 613 196;x_wconf 94' style='font-size:10pt;font-family:Times;font-style:bold'>τῆς</span> <span class='ocrx_word' title='bbox 629 155 754 196;x_wconf 100' style='font-size:10pt;font-family:Times;font-style:bold'>κατάρας</span> <span class='ocrx_word' title='bbox 766 155 816 196;x_wconf 100' style='font-size:10pt;font-family:Times;font-style:bold'>του</span> <span class='ocrx_word' title='bbox 827 155 873 196;x_wconf 67'>νό-</span> <span class='ocrx_word' title='bbox 882 155 912 196;x_wconf 67' style='font-size:10pt;font-family:Times;font-style:bold'>A</span> <span class='ocrx_word' title='bbox 919 155 1022 196;x_wconf 90'>nomiæ</span> <span class='ocrx_word' title='bbox 1037 155 1206 196;x_wconf 100'>miraculum</span><span class='ocrx_word' title='bbox 1213 155 1224 196;x_wconf 71'>;</span> <span class='ocrx_word' title='bbox 1241 155 1300 196;x_wconf 99'>non</span> <span class='ocrx_word' title='bbox 1314 155 1417 196;x_wconf 100'>timere</span> <span class='ocrx_word' title='bbox 1428 155 1655 196;x_wconf 100'>maledictionem</span> <span class='ocrx_word' title='bbox 1667 155 1695 196;x_wconf 99'>le</span></span>")

def test_bbox():
    bbox = BBox(92, 155, 1695, 196)
    span = Span(span1)
    assert span.bbox == bbox


def test_length():
    span = Span(span1)
    assert len(span) == 17

def test_tokens():
    span = Span(span1)
    tokens = span.tokens
