# from_mets.py
#
# Script to derive a minimal XML document from a digital object
# defined by a METS file.

from pathlib import Path

from models.mets import Volume, Page

vol_dir = [Path("/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148")]
top_dir = Path("/Users/wulfmanc/Desktop/patrologia_graeca")
target_dir = Path("/Users/wulfmanc/gh/Uncorrected_OCR/patrologia_graeca/volumes_raw")
vol_dirs = [d for d in top_dir.iterdir() if d.is_dir()]

for vol in vol_dirs:
    fname = f"njp_{vol.stem}.xml"
    fpath = target_dir / fname
    volume = Volume(vol)
    with fpath.open('w+') as f:
        f.write(volume.xml)


# v:Volume = Volume(vol_dir)
# p:Page = v.pages[55]
