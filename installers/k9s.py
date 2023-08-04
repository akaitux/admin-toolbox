import subprocess
import sys
import os
import re
import shutil
from pathlib import Path
from common.logger import logger
from common.config import get_config
from common.download_file import download_file


class K9S:

    def __init__(self, workdir):
        self.config = get_config()
        self.workdir = workdir
        self.desired_platform = self.config.platform
        self.desired_ver = self.config.k9s_ver
        self.download_url = self.config.k9s_url
        self.bin_path = self.workdir.bin / 'k9s'

    def _check_current_ver(self):
        if not os.path.exists(self.bin_path):
            return None
        try:
            p = subprocess.run(
                [str(self.bin_path), 'version'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if not p.stdout:
                raise Exception("k9s stdout -v is empty")
            for l in p.stdout.split('\n'):
                l = l.strip()
                if not 'Version:' in l:
                    continue
                l = re.findall('v(\d+\.\d+\.\d+)', l)
                if not l or len(l) != 1:
                    raise Exception("Wrong k9s version: {}".format(l))
                return l[0]
            raise Exception("Something wrong with k9s version")

        except subprocess.CalledProcessError as exc:
            logger.error("Error while check k9s version")
            logger.error(exc.stdout)
            sys.exit(1)

    def _download(self):
        url = self.download_url.format(
            ver=self.desired_ver,
            os=self.desired_platform,
            arch="x86_64",
        )
        zip_arch = self.workdir.tmp / 'k9s.tar.gz'

        logger.debug('Download k9s {} -> {}'.format(url, zip_arch))
        if not download_file(url, zip_arch, self.config.proxies):
            sys.exit(1)

        # Unzip
        logger.debug('Unzip k9s {}'.format(zip_arch))
        try:
            Path(self.workdir.tmp / 'k9s').mkdir(exist_ok=True)
            subprocess.run(
                ['tar', '-x', '-f', zip_arch, '-C', self.workdir.tmp/ 'k9s'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("Error while unpack k9s")
            logger.error(exc.stdout)
            sys.exit(1)

        logger.debug('Move k9s bin to {}'.format(self.bin_path))
        os.remove(zip_arch)
        shutil.move(self.workdir.tmp / 'k9s/k9s', self.bin_path)

    def install(self):
        logger.info('Install k9s ...')
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('k9s already installed')
            return
        self._download()
        logger.info("k9s installed")

