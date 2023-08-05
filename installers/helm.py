import subprocess
import sys
import os
import re
import shutil
from pathlib import Path
from common.logger import logger
from common.config import get_config
from common.download_file import download_file
from installers.installer import Installer


class Helm(Installer):

    def __init__(self):
        self._config = get_config()
        self.enabled = self._config.helm_enabled
        self.workdir = self._config.workdir
        self.desired_platform = self._config.platform
        self.desired_ver = self._config.helm_ver
        self.download_url = self._config.helm_url
        self.bin_path = self.workdir.bin / 'helm'

    def install(self):
        logger.info('Install Helm ...')
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('helm already installed')
            return
        self._download()
        logger.info("Helm installed")

    def make_activate_replaces(self) -> dict:
        return  {}


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
                raise Exception("helm stdout version is empty")
            for l in p.stdout.split('\n'):
                l = l.strip()
                if not 'Version:' in l:
                    continue
                l = re.findall('v(\d+\.\d+\.\d+)', l)
                if not l or len(l) != 1:
                    raise Exception("Wrong helm version: {}".format(l))
                return l[0]
            raise Exception("Something wrong with helmversion")

        except subprocess.CalledProcessError as exc:
            logger.error("Error while check helm version")
            logger.error(exc.stdout)
            sys.exit(1)

    def _download(self):
        arch = "amd64"
        url = self.download_url.format(
            ver=self.desired_ver,
            os=self.desired_platform,
            arch=arch,
        )
        zip_arch = self.workdir.tmp / 'helm.tar.gz'

        logger.debug('Download helm {} -> {}'.format(url, zip_arch))
        if not download_file(url, zip_arch, self._config.proxies):
            sys.exit(1)

        # Unzip
        logger.debug('Unzip helm {}'.format(zip_arch))
        try:
            Path(self.workdir.tmp / 'helm').mkdir(exist_ok=True)
            subprocess.run(
                ['tar', '-x', '-f', zip_arch, '-C', self.workdir.tmp/ 'helm'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("Error while unpack helm")
            logger.error(exc.stdout)
            sys.exit(1)

        logger.debug('Move helm bin to {}'.format(self.bin_path))
        os.remove(zip_arch)
        shutil.move(self.workdir.tmp / f'helm/{self.desired_platform}-{arch}/helm', self.bin_path)
