import subprocess
import sys
import json
import os
import traceback
from common.logger import logger
from common.config import get_config
from common.download_file import download_file
from installers.installer import Installer


class Kubectl(Installer):

    def __init__(self):
        self._config = get_config()
        self.enabled = self._config.kubectl_enabled
        self.workdir = self._config.workdir
        self.desired_platform = self._config.platform
        self.desired_ver = self._config.kubectl_ver
        self.download_url = self._config.kubectl_url
        self.bin_path = self.workdir.bin / 'kubectl'
        self.config_path = self.workdir.root / 'kube'

    def install(self):
        logger.info('Install kubectl ...')
        self.config_path.mkdir(exist_ok=True)
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('kubectl already installed')
            return
        self._download()
        logger.info("kubectl installed")

    def make_activate_replaces(self) -> dict:
        return {
            "<KUBE_ENABLED>": str(self.enabled),
            "<KUBE_CONFIG_PATH>": str(self.config_path),
        }

    def _check_current_ver(self):
        if not os.path.exists(self.bin_path):
            return None
        try:
            p = subprocess.run(
                [str(self.bin_path), 'version', '--output=json', '--client=true'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if not p.stdout:
                raise Exception("kubectl stdout -v is empty")
            try:
                version_data = json.loads(p.stdout)
                # [1:] - v1.0.0 -> 1.0.0
                return version_data["clientVersion"]["gitVersion"][1:]
            except json.JSONDecodeError as e:
                logger.error("Error while parsing kubectl json version output")
                logger.error(p.stdout)
                logger.error(p.stderr)
                logger.error(traceback.format_exc())
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            logger.error("Error while check kubectl version")
            logger.error(e.stdout)
            logger.error(e.stderr)
            sys.exit(1)

    def _download(self):
        url = self.download_url.format(
            ver=self.desired_ver,
            os=self.desired_platform,
            arch="amd64",
        )
        logger.debug('Download kubectl {} -> {}'.format(url, self.bin_path))
        if not download_file(url, self.bin_path, self._config.proxies):
            sys.exit(1)
        os.chmod(self.bin_path, 0o550)



