import subprocess
import os
import sys
from common.logger import logger
from common.config import get_config
from common.download_file import download_file


class Terraform:

    def __init__(self, workdir):
        self.config = get_config()
        self.workdir = workdir
        self.desired_platform = self.config.platform
        self.desired_ver = self.config.terraform_ver
        self.download_url = self.config.terraform_url
        self.bin_path = self.workdir.bin / 'terraform'

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
                raise Exception("Terraform stdout -v is empty")
            out = p.stdout.split('\n')
            if not len(out):
                raise Exception("Wrong terraform output: {}".format(out))
            out = out[0].split(' ')
            if len(out) != 2 or out[1][0] != 'v':
                raise Exception("Wrong terraform output: {}".format(out))
            return out[1][1:] # v1.0.0[1:] -> 1.0.0

        except subprocess.CalledProcessError as exc:
            logger.error("Error while check terraform version")
            logger.error(exc.stdout)
            sys.exit(1)

    def _download(self):
        url = self.download_url.format(
            ver=self.desired_ver,
            os=self.desired_platform,
            arch="amd64",
        )
        zip_arch = self.workdir.tmp / 'terraform.zip'

        logger.debug('Download terraform {} -> {}'.format(url, zip_arch))
        if not download_file(url, zip_arch, self.config.proxies):
            sys.exit(1)

        # Unzip
        logger.debug('Unzip terraform {}'.format(zip_arch))
        try:
            subprocess.run(
                ['unzip', '-d', self.workdir.tmp / 'terraform', zip_arch],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("Error while unzip terraform")
            logger.error(exc.stdout)
            sys.exit(1)

        logger.debug('Move terraform bin to {}'.format(self.bin_path))
        os.remove(zip_arch)
        os.replace(
            self.workdir.tmp / 'terraform/terraform',
            self.bin_path,
        )
        os.rmdir(self.workdir.tmp / 'terraform')


    def install(self):
        logger.info('Install terraform ...')
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('Terraform already installed')
            return
        self._download()
        logger.info("Terraform installed")


