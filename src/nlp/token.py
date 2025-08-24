import unicodedata
from lxml import etree
from nlp.layout_object import LayoutObject

class Token(LayoutObject):
    def __init__(self, element:etree.Element):
        super().__init__(element)
        self.text = self.clean_text(element.text)
        self.tail = element.tail
        self.type = "token"


    def __repr__(self) -> str:
        return f"Token({self.text!r})"

    def __str__(self) -> str:
        return self.text_with_ws

    @property
    def text_with_ws(self) -> str:
        if self.tail:
            return self.text + self.tail
        else:
            return self.text

    @property
    def is_greek(self) -> bool:
        greek_count = 0
        alpha_count = 0
        threshold:float = 0.5
        for char in self.text:
            alpha_count += 1
            codepoint = ord(char)
                # is it in the Greek and Coptic code block or the Extended Greek code block?
            if (0x0370 <= codepoint <= 0x03FF) or (0x1F00 <= codepoint <= 0x1FFF):
                greek_count += 1
                
        if alpha_count == 0:
                return False  # No letters at all
                
        return (greek_count / alpha_count) >= threshold


    @property
    def is_punct(self) -> bool:
        """
        Returns True if the character is punctuation based on Unicode category.
        """
        if len(self.text) != 1:
            return False
        return unicodedata.category(self.text).startswith('P')

        
    def clean_text(self,text):
        # Replace bad entities (example: replace &shy; with actual soft hyphen)
        text = text.replace("&shy;", "\u00AD")
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text
