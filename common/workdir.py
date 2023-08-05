from pathlib import Path
import os
import shutil
from common.logger import logger

class Workdir:

    def __init__(self, root_dir=""):
        self.root = Path(root_dir).expanduser().resolve()
        if not root_dir:
            self.root = Path('~/.admin-toolbox').expanduser().resolve()
        if not self.root:
            raise Exception('Workdir root not defined')
        self.tmp = Path("{}/tmp".format(self.root))
        self.bin = Path("{}/bin".format(self.root))
        self.storage = Path("{}/storage".format(self.root))
        logger.info("Root dir is: {}".format(self.root))
        logger.info("Bin dir is: {}".format(self.bin))

    def prepare(self):
        self.root.mkdir(exist_ok=True)
        self.bin.mkdir(exist_ok=True)
        if self.tmp.exists():
            shutil.rmtree(self.tmp)
        self.tmp.mkdir()

    def cleanup(self):
        if self.tmp.exists():
            shutil.rmtree(self.tmp)


