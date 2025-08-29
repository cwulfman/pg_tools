import logging
from pathlib import Path
from pg import Loader, PgVolume
indir = Path('/Users/wulfmanc/Desktop/patrologia_graeca')
volumes_dir = Path("/tmp/volumes")


# Configure basic logging to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run():
    for dir in indir.iterdir():
        if dir.stem != '.DS_Store':
            logging.info(f"Starting to process volume {dir.stem}")
            dpath = Path(dir)
            if len(list(dpath.glob("*.xml"))) > 0:
                volume = PgVolume(dir)
                outdir = volumes_dir / dir.stem
                outdir.mkdir(parents=True, exist_ok=True)
                volume.serialize(outdir)
                logging.info(f"Finished processing volume {dir.stem}")
            else:
                logging.error(f"ERROR: no METS file for {dir.stem}")
            



if __name__ == "__main__":
    logging.info("Starting run")
    run()
    logging.info("Finished run")
