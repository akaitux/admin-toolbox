import subprocess
import sys
import os
from common.logger import logger
from common.config import get_config
from common.download_file import download_file


class Terragrunt:

    def __init__(self, workdir):
        self.config = get_config()
        self.workdir = workdir
        self.desired_platform = self.config.platform
        self.desired_ver = self.config.terragrunt_ver
        self.download_url = self.config.terragrunt_url
        self.bin_path = self.workdir.bin / 'terragrunt'

    def _check_current_ver(self):
        if not os.path.exists(self.bin_path):
            return None
        try:
            p = subprocess.run(
                [str(self.bin_path), '-v'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if not p.stdout:
                raise Exception("Terragrunt stdout -v is empty")
            out = p.stdout.strip().split(' ')
            if len(out) != 3 or out[2][0] != 'v':
                raise Exception("Wrong terragrunt -v output: {}".format(out))
            return out[2][1:] # v1.0.0[1:] -> 1.0.0

        except subprocess.CalledProcessError as exc:
            logger.error("Error while check terragrunt version")
            logger.error(exc.stdout)
            sys.exit(1)

    def _download(self):
        url = self.download_url.format(
            ver=self.desired_ver,
            os=self.desired_platform,
            arch="amd64",
        )
        logger.debug('Download terragrunt {} -> {}'.format(url, self.bin_path))
        if not download_file(url, self.bin_path, self.config.proxies):
            sys.exit(1)
        os.chmod(self.bin_path, 0o550)

    def install(self):
        logger.info('Install terragrunt ...')
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('Terragrunt already installed')
            return
        self._download()
        logger.info("Terragrunt installed")



