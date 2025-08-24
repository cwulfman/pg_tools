from lxml import etree
from nlp.token import Token

token1_xml = etree.XML("<span class='ocrx_word' title='bbox 766 155 816 196;x_wconf 100'>του</span>")
token2_xml = etree.XML("<span class='ocrx_word' title='bbox 766 155 816 196;x_wconf 100'>foo</span>")

def test_attributes():
    token = Token(token1_xml)
    assert token.text == 'του'
    assert token.tail is None
    assert token.type == 'token'

def test_token_text():
    greek_token = Token(token1_xml)
    non_greek_token = Token(token2_xml)

    assert greek_token.is_greek
    assert non_greek_token.is_greek is False
