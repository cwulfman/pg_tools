from pathlib import Path
from pg import PgVolume
from nlp.page import Page
from nlp.column import Column

volpath = Path('/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148')
vol:PgVolume = PgVolume(volpath)

p:Page = vol.page(71)._nlp_page
p.repair_fused_lines()

# compare old columns and new columns
l,r = p.columns()


# assert len(l.lines) == len(lnew.lines)
# assert len(r.lines) == len(rnew.lines)
