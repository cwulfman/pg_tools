from __future__ import annotations
from lxml import etree
from typing import Iterable, List


ns = {"xhtml": "http://www.w3.org/1999/xhtml"}

def flatten(a):
    res = []
    for x in a:
        if isinstance(x, list):
            res.extend(flatten(x))
        else:
            res.append(x)
    return res

def genObject(element:etree.Element):
    from nlp.page import Page
    from nlp.block import Block
    from nlp.par import Par
    from nlp.line import Line
    from nlp.token import Token

    cls = (element.get("class") or "").strip()
    if "ocr_line" in cls:
        return Line(element)
    if "ocr_page" in cls:
        return Page(element)
    if "ocrx_block" in cls:
        return Block(element)
    if "ocr_par" in cls:
        return Par(element)
    if "ocr_line" in cls:
        return Line(element)
    if "ocrx_word" in cls:
        return Token(element)
    # Fallback: return generic Span
    from nlp.span import Span
    return Span(element)


def percent_greek(tok_list):
    if len(tok_list) == 0:
        return 0
    else:
        tok_count = 0
        greek_count = 0
        for tok in tok_list:
            tok_count +=1
            if tok.is_greek:
                greek_count += 1
        return greek_count / tok_count
    


def fix_entities(xml_string:str) -> str:
    # Remove XML declaration to avoid ValueError
    xml_string = re.sub(r'<\?xml.*?\?>', '', xml_string, flags=re.DOTALL)
    # Replace bad entities (example: replace &shy; with actual soft hyphen)
    xml_string = xml_string.replace("&shy;", "\u00AD")
    xml_string = xml_string.replace("&quot;", "\u0022")
    return xml_string
        

def load_page_file(page_file:Path):
    with page_file.open('r') as pf:
        raw_data = pf.read()
        clean_data = fix_entities(raw_data)
        tree = etree.fromstring(clean_data)
    return tree


def report(lines):
    print("i\tleft\ttop\twidth\tline")
    for i,l in enumerate(lines):
        print(f"{i}\t{l.left}\t{l.top}\t{l.width}\t{l}")
