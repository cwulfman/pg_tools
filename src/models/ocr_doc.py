# ocr_doc.py
#
# Models hocr elements

from lxml import etree

ocr_namespaces = {'html' : 'http://www.w3.org/1999/xhtml'}

pages = etree.XPath(".//html:div[@class='ocr_page']", namespaces=ocr_namespaces)
blocks = etree.XPath(".//html:div[@class='ocrx_block']", namespaces=ocr_namespaces)
paragraphs = etree.XPath(".//html:span[@class='ocr_par']", namespaces=ocr_namespaces)
lines = etree.XPath(".//html:span[@class='ocr_line']", namespaces=ocr_namespaces)
words = etree.XPath(".//html:span[@class='ocrx_word']", namespaces=ocr_namespaces)



def prettyprint(element, **kwargs):
    xml = etree.tostring(element, pretty_print=True, **kwargs)
    print(xml.decode(), end='')



class OCRDoc:

    def __init__(self, root):
        self.root = root

    @property
    def pages(self):
        return [OCRPage(obj) for obj in
                self.root.xpath(".//html:div[@class='ocr_page']",
                                namespaces=ocr_namespaces)]


    @property
    def blocks(self):
        result = []
        if self.root is not None:
            result = [OCRBlock(obj) for obj in
                      self.root.xpath(".//html:div[@class='ocrx_block']",
                                      namespaces=ocr_namespaces)]
        return result
   

    @property
    def paragraphs(self):
        return [OCRParagraph(obj) for obj in
                self.root.xpath(".//html:p[@class='ocr_par']",
                                namespaces=ocr_namespaces)]

        

    @property
    def lines(self):
        return [OCRLine(obj) for obj in 
                self.root.xpath(".//html:span[@class='ocr_line']",
                                namespaces=ocr_namespaces)]
        

    @property
    def words(self):
        return [OCRWord(obj) for obj in
                self.root.xpath(".//html:span[@class='ocrx_word']",
                                namespaces=ocr_namespaces)]
        



class OCRPage(OCRDoc):
    def __init__(self, root):
        super().__init__(root)


    @property
    def text(self) -> str:
        blocks = '\n\n'.join(b.text for b in self.blocks)
        return f"<div>\n{blocks}\n</div>"


class OCRBlock(OCRDoc):
    def __init__(self, root):
        super().__init__(root)

    @property
    def text(self) -> str:
        paragraphs = '\n'.join(p.text for p in self.paragraphs)
        return f"<div>{paragraphs}</div>"


class OCRParagraph(OCRDoc):
    def __init__(self, root):
        super().__init__(root)

    @property
    def text(self) -> str:
        lines = '\n'.join(line.text for line in self.lines)
        return f"<p>{lines}</p>"


class OCRLine(OCRDoc):
    def __init__(self, root):
        super().__init__(root)

    @property
    def text(self) -> str:
        return ''.join(w.text for w in self.words)



class OCRWord(OCRDoc):
    def __init__(self, root):
        super().__init__(root)


    @property
    def text(self) -> str:
        text = self.root.text
        text = text.replace("<", "&lt;")        
        text = text.replace(">", "&gt;")        
        if self.root.tail:
            text += self.root.tail
        return text

