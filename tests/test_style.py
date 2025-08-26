from nlp.style import Style


s = Style('font-size:11pt;font-family:"Times";font-style:"bold italic";')

assert s.size == 11
assert s.family == "Times"
assert s.weight == ("bold", "italic")

assert "bold" in s
assert "italic" in s
assert "underline" not in s
