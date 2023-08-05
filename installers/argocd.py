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


class ArgoCD(Installer):

    def __init__(self):
        self._config = get_config()
        self.enabled = self._config.argocd_enabled
        self.workdir = self._config.workdir
        self.desired_platform = self._config.platform
        self.desired_ver = self._config.argocd_ver
        self.download_url = self._config.argocd_url
        self.bin_path = self.workdir.bin / 'argocd'
        self.cfg_path = self.workdir.root / "argocd.cfg"

    def install(self):
        logger.info('Install ArgoCD ...')
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('argocd already installed')
            return
        self._download()
        logger.info("ArgoCD installed")

    def make_activate_replaces(self) -> dict:
        return {
            "<ALIAS_ARGOCD>": f"argocd='argocd --config {self.cfg_path}'",
        }

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
            l = re.findall(r'v(\d+\.\d+\.\d+)', l)
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
        if not download_file(url, self.bin_path, self._config.proxies):
            sys.exit(1)
        os.chmod(self.bin_path, 0o550)

