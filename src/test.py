from pathlib import Path
from nlp import Token, Span, Page, Block, Par, Line
from loader import Loader

volpath = Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148')

page1 = volpath / Path("00000697.html")
page2 = volpath / Path('00000102.html')
page3 =   volpath / Path('00000500.html')
page691 = volpath / Path('00000691.html')

loader = Loader(Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148'))

# loader.load()
# p1:Page = loader.pages[697]
# voldir = Path("/tmp/volumes")
#
p1:Page = loader.load_page(page1, 697)
p2:Page = loader.load_page(page2, 102)
p3:Page = loader.load_page(page3, 500)
p4:Page = loader.load_page(page691, 691)
