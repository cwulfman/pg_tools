# A transformer class
import argparse
import logging
from pathlib import Path
import pg


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

    def transform_volume(self, barcode):
        if self.outdir:
            logging.info(f"transforming volume {barcode}")
            vol_indir = self.indir / barcode
            volume = pg.PgVolume(vol_indir)
            volume.serialize(self.outdir)
            logging.info(f"finished transforming volume {barcode}")
        else:
            logging.error("no output directory to write to")


    def transform_all_volumes(self):
        barcoded_directories = [x for x in self.indir.iterdir() if x.is_dir()]
        barcodes = [d.stem for d in barcoded_directories]
        volume_count = len(barcodes)
        logging.info(f"processing {volume_count} volumes")
        logging.info(f"starting to process {len(barcoded_directories)}")
        for i,barcode in enumerate(barcodes):
            logging.info(f"processing volume {i}: barcode={barcode}")
            self.transform_volume(barcode)
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

