from pathlib import Path
import os

def volume_to_xml(dir:Path, outdir:Path):
    fname = f"prnc_{dir.stem}.xml"
    fpath = outdir / Path(fname)
    with fpath.open('w+') as book:
        book.write("<text>\n")

        pages = dir.glob("*.txt")
        
        for page in sorted(pages):
            book.write(f"<pb facs=\'prnc_{dir.stem}.{page.stem}'/>\n")
            with page.open('r') as f:
                content = f.read()
            book.write(content)
        book.write("</text>")

def main():
    pg_dir = Path("/Users/wulfmanc/Desktop/patrologia_graeca")
    out_dir = Path("/Users/wulfmanc/gh/Uncorrected_OCR/patrologia_graeca/volumes_raw")
    vol_folders = [item for item in pg_dir.iterdir() if item.is_dir()]
    for vol in vol_folders:
        volume_to_xml(vol, out_dir)
    
