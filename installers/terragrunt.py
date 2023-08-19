import subprocess
import sys
import os
from common.logger import logger
from common.config import get_config
from common.download_file import download_file
from installers.installer import Installer


class Terragrunt(Installer):

    def __init__(self):
        self._config = get_config()
        self.enabled = self._config.terragrunt_enabled
        self.workdir = self._config.workdir
        self.desired_platform = self._config.platform
        self.desired_ver = self._config.terragrunt_ver
        self.download_url = self._config.terragrunt_url
        self.bin_path = self.workdir.bin / 'terragrunt'
        self.use_proxy = self._config.terragrunt_use_proxy

    def install(self):
        logger.info('Install terragrunt ...')
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('Terragrunt already installed')
            return
        self._download()
        logger.info("Terragrunt installed")

    def make_activate_replaces(self) -> dict:
        replaces = {
            "<ALIAS_TERRAGRUNT>": "terragrunt='terragrunt'",
        }
        if self.enabled:
            replaces['<TERRAGRUNT_ENABLED>'] = "true"
        else:
            replaces['<TERRAGRUNT_ENABLED>'] = ""
        if self.use_proxy:
            if self._config.proxies['https']:
                replaces["<ALIAS_TERRAGRUNT>"]= "terragrunt='HTTPS_PROXY={} terragrunt'".format(
                    self._config.proxies['https'],
                )
            elif self._config.proxies['http']:
                replaces["<ALIAS_TERRAGRUNT>"]= "terragrunt='HTTP_PROXY={} terragrunt'".format(
                    self._config.proxies['http'],
                )
        return replaces

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
        if not download_file(url, self.bin_path, self._config.proxies):
            sys.exit(1)
        os.chmod(self.bin_path, 0o650)



