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
        return self.root.xpath("//html:span[@class='ocr_page']", namespaces=ocr_namespaces)


    @property
    def blocks(self):
        return self.root.xpath("//html:span[@class='ocrx_block']", namespaces=ocr_namespaces)

        

    @property
    def paragraphs(self):
        return self.root.xpath("//html:span[@class='ocr_par']", namespaces=ocr_namespaces)

        

    @property
    def lines(self):
        return self.root.xpath("//html:span[@class='ocr_line']", namespaces=ocr_namespaces)
        

    @property
    def words(self):
        return self.root.xpath("//html:span[@class='ocrx_word']", namespaces=ocr_namespaces)
        


class OCRPage(OCRDoc):
    def __init__(self, root):
        super().__init__(root)


class OCRBlock(OCRDoc):
    def __init__(self, root):
        super().__init__(root)


class OCRParagraph(OCRDoc):
    def __init__(self, root):
        super().__init__(root)




class OCRLine(OCRDoc):
    def __init__(self, root):
        super().__init__(root)



class OCRWord(OCRDoc):
    def __init__(self, root):
        super().__init__(root)

