# A transformer class
import argparse
import logging
from pathlib import Path
from nlp.volume import EPubVolume


# Configure basic logging to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Transformer():
    """A class to transform one or all of the
    volumes. It assumes its input direcory
    contains subdirectories named by barcode
    or other id."""
    def __init__(self, indir, outdir) -> None:
        self.indir = Path(indir)
        self.outdir = Path(outdir)

    def transform_volume(self, epub):
        barcode = Path(epub).stem
        file_path = (self.outdir / barcode).with_suffix(".xml")

        if file_path.is_file():
            logging.info(f"{file_path} already exists")
        else:
            logging.info(f"transforming volume {barcode}")
            volume = EPubVolume(epub)
            volume.serialize(self.outdir, greek_only=True)
            logging.info(f"finished transforming volume {barcode}")


    def transform_all_volumes(self):
        epubs = [x for x in Path(self.indir).iterdir() if x.is_file()]
        if epubs:
            volume_count = len(epubs)
            logging.info(f"processing {volume_count} volumes")
            logging.info(f"starting to process {len(epubs)}")
            for i,epub in enumerate(epubs):
                logging.info(f"processing volume {i}: id={Path(epub).stem}")
                self.transform_volume(epub)
                logging.info(f"done processing volume {i}")


def main():
    parser = argparse.ArgumentParser(description="Transform barcoded volume directories into XML.")
    parser.add_argument("input_dir", help="Path to the input directory containing barcoded folders")
    parser.add_argument("output_dir", help="Path to the output directory where XML files will be written")
    parser.add_argument("--barcode", help="Optional specific barcode to transform")

    args = parser.parse_args()

    transformer = Transformer(args.input_dir, args.output_dir)

    if args.barcode:
        transformer.transform_volume(args.barcode)
    else:
        transformer.transform_all_volumes()

if __name__ == "__main__":
    main()
