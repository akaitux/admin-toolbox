import subprocess
import sys
import os
import re
import shutil
from pathlib import Path
from common.logger import logger
from common.config import get_config
from common.download_file import download_file


class ArgoCD:

    def __init__(self, workdir):
        self.config = get_config()
        self.workdir = workdir
        self.desired_platform = self.config.platform
        self.desired_ver = self.config.argocd_ver
        self.download_url = self.config.argocd_url
        self.bin_path = self.workdir.bin / 'argocd'

    def _check_current_ver(self):
        if not os.path.exists(self.bin_path):
            return None
        try:
            p = subprocess.run(
                [str(self.bin_path), 'version'],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if not p.stdout:
                raise Exception("argocd stdout version is empty")
            l = p.stdout.split('\n')[0].strip()
            l = re.findall('v(\d+\.\d+\.\d+)', l)
            if not l or len(l) != 1:
                raise Exception("Wrong argocd version: {}".format(l))
            return l[0]

        except subprocess.CalledProcessError as exc:
            logger.error("Error while check argocd version")
            logger.error(exc.stdout)
            sys.exit(1)

    def _download(self):
        arch = "amd64"
        url = self.download_url.format(
            ver=self.desired_ver,
            os=self.desired_platform,
            arch=arch,
        )

        logger.debug('Download argocd {} -> {}'.format(url, self.bin_path))
        if not download_file(url, self.bin_path, self.config.proxies):
            sys.exit(1)
        os.chmod(self.bin_path, 0o550)

    def install(self):
        logger.info('Install ArgoCD ...')
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('argocd already installed')
            return
        self._download()
        logger.info("ArgoCD installed")

