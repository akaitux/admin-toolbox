import subprocess
import re
import os
import sys
import shutil
from pathlib import Path
from common.logger import logger
from common.config import get_config
from common.download_file import download_file


class Gcloud:

    def __init__(self, workdir):
        self.config = get_config()
        self.workdir = workdir
        self.workdir_gcloud = workdir.root / 'gcloud/'
        self.desired_platform = self.config.platform
        self.desired_ver = self.config.gcloud_ver
        self.download_url = self.config.gcloud_url
        self.bin_path = workdir.bin / 'gcloud'

        self._prepare()

    def _prepare(self):
        self.workdir_gcloud.mkdir(exist_ok=True)
        self.config.gcloud_cfg_path.mkdir(exist_ok=True)

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
                raise Exception("Gcloud stdout -v is empty")
            out = p.stdout.split('\n')
            if not len(out):
                raise Exception("Wrong gcloud output: {}".format(out))
            out = out[0].split(' ')
            if len(out) != 4:
                raise Exception("Wrong gcloud output: {}".format(out))
            return out[3] # 390.0.0

        except subprocess.CalledProcessError as exc:
            logger.error("Error while check gcloud version")
            logger.error(exc.stdout)
            sys.exit(1)

    def _download(self):
        url = self.download_url.format(
            ver=self.desired_ver,
            os=self.desired_platform,
            arch="x86_64",
        )
        zip_arch = self.workdir.tmp / 'gcloud.zip'

        logger.debug('Download gcloud {} -> {}'.format(url, zip_arch))
        if not download_file(url, zip_arch, self.config.proxies):
            sys.exit(1)

        # Remove old version
        release_dir = self.workdir_gcloud / 'google-cloud-sdk'
        if os.path.exists(release_dir):
            shutil.rmtree(release_dir)

        # Unzip
        logger.debug('Unzip gcloud {}'.format(zip_arch))
        try:
            Path(self.workdir.root / 'gcloud').mkdir(exist_ok=True)
            subprocess.run(
                ['tar', '-x', '-f', zip_arch, '-C', self.workdir.root / 'gcloud'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("Error while unpack gcloud")
            logger.error(exc.stdout)
            sys.exit(1)

        logger.debug('Link gcloud bin to {}'.format(self.bin_path))
        os.remove(zip_arch)

        # ln -s to bin
        try:
            subprocess.run(
                ['ln', '-s', '-f', self.workdir.root / 'gcloud/google-cloud-sdk/bin/gcloud', self.bin_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("Error while ln -s gcloud")
            logger.error(exc.stdout)
            sys.exit(1)


    def _install_components(self):
        components = ['gke-gcloud-auth-plugin']
        for component in components:
            logger.info("\tInstall gcloud component: {} ...".format(component))
            try:
                subprocess.run(
                    [self.bin_path, 'components', 'install', '-q', component],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as exc:
                logger.error(
                    "Error while install gcloud component {}".format(component)
                )
                logger.error(exc.stdout)
                sys.exit(1)

    def _exec(self, cmd):
        os.environ['CLOUDSDK_CONFIG'] = str(self.config.gcloud_cfg_path)
        try:
            p = subprocess.run(
                [self.bin_path,] + cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if p.stdout:
                return p.stdout.decode("utf-8")
        except subprocess.CalledProcessError as exc:
            logger.error("Error while get config list")
            logger.error(exc.stdout)
            sys.exit(1)

    def _prepare_config(self):
        proxy = self.config.proxies['http']
        if proxy:
            proxy = proxy.replace('http://', '')
            addr = proxy
            port = '80'
            if ':' in proxy:
                addr, port = proxy.split(':')
            self._exec(['config', 'set', 'proxy/type', 'http'])
            self._exec(['config', 'set', 'proxy/address', addr])
            self._exec(['config', 'set', 'proxy/port', port])
        else:
            logger.warning('No http proxy for gcloud')


    def install(self):
        logger.info('Install gcloud ...')
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('Gcloud already installed')
        else:
            self._download()
            logger.info("Gcloud installed")
        self._install_components()
        logger.info("Gcloud components installed")
        self._prepare_config()
