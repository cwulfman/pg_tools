from lxml import etree
from nlp.layout_object import LayoutObject
from nlp.span import Span
from nlp.line import Line
from nlp.bbox import BBox



hocr_line = etree.XML("<span class='ocr_line' title='bbox 92 155 1695 196;x_wconf 91'><span class='ocrx_word' title='bbox 92 155 152 196;x_wconf 93'>στὸς</span> <span class='ocrx_word' title='bbox 168 155 221 196;x_wconf 97'>γὰρ</span> <span class='ocrx_word' title='bbox 235 155 310 196;x_wconf 95' >ἡμᾶς</span> <span class='ocrx_word' title='bbox 328 155 494 196;x_wconf 95'>ἐξηγόρασεν</span> <span class='ocrx_word' title='bbox 512 155 546 196;x_wconf 84' style='font-size:10pt;font-family:Times;font-style:bold'>ἐκ</span> <span class='ocrx_word' title='bbox 559 155 613 196;x_wconf 94' style='font-size:10pt;font-family:Times;font-style:bold'>τῆς</span> <span class='ocrx_word' title='bbox 629 155 754 196;x_wconf 100' style='font-size:10pt;font-family:Times;font-style:bold'>κατάρας</span> <span class='ocrx_word' title='bbox 766 155 816 196;x_wconf 100' style='font-size:10pt;font-family:Times;font-style:bold'>του</span> <span class='ocrx_word' title='bbox 827 155 873 196;x_wconf 67'>νό-</span> <span class='ocrx_word' title='bbox 882 155 912 196;x_wconf 67' style='font-size:10pt;font-family:Times;font-style:bold'>A</span> <span class='ocrx_word' title='bbox 919 155 1022 196;x_wconf 90'>nomiæ</span> <span class='ocrx_word' title='bbox 1037 155 1206 196;x_wconf 100'>miraculum</span><span class='ocrx_word' title='bbox 1213 155 1224 196;x_wconf 71'>;</span> <span class='ocrx_word' title='bbox 1241 155 1300 196;x_wconf 99'>non</span> <span class='ocrx_word' title='bbox 1314 155 1417 196;x_wconf 100'>timere</span> <span class='ocrx_word' title='bbox 1428 155 1655 196;x_wconf 100'>maledictionem</span> <span class='ocrx_word' title='bbox 1667 155 1695 196;x_wconf 99'>le</span></span>")

non_hocr_word = etree.XML("<span data-coords='199 920 337 962' class='ocrx_word'>secundum</span>")

non_hocr_line = etree.XML("<span class='ocr_line' data-width='0.512422360248447' data-line-break='true' data-px=''><span data-coords='199 920 337 962' class='ocrx_word'>secundum</span> <span data-coords='350 920 481 961' class='ocrx_word'>proprium</span> <span data-coords='495 920 606 961' class='ocrx_word'>laborem</span> <span data-coords='617 920 626 961' class='ocrx_word'>(</span> <span data-coords='629 919 656 961' class='ocrx_word'>1.</span> <span data-coords='674 919 729 960' class='ocrx_word'>Cor</span> <span data-coords='729 919 736 960' class='ocrx_word'>.</span> <span data-coords='747 919 808 960' class='ocrx_word'>3.8</span> <span data-coords='808 919 821 960' class='ocrx_word'>)</span> <span data-coords='822 919 830 960' class='ocrx_word'>.</span> <span data-coords='851 919 895 960' class='ocrx_word'>Ne</span> <span data-coords='912 919 990 960' class='ocrx_word'>igitur</span> </span>")


def test_hocr_line():
    object = LayoutObject(hocr_line)
    expected_bbox = BBox(92, 155, 1695, 196)
    assert object.bbox == expected_bbox


def test_non_hocr_word():
    object = LayoutObject(non_hocr_word)
    expected_bbox = BBox(199, 920, 337, 962)
    assert object.bbox == expected_bbox


def test_non_hocr_line():
    object = Line(non_hocr_line)
    expected_bbox = BBox(199, 920, 990, 960)
    assert object.bbox == expected_bbox
