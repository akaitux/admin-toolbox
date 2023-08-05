import shutil
import os
import subprocess
import sys
from pathlib import Path
from common.logger import logger
from common.config import get_config
from installers.installer import Installer


class Gron(Installer):

    def __init__(self):
        self._config = get_config()
        self.enabled = self._config.gron_enabled
        self.repo_url = self._config.gron_repo_url
        self.workdir = self._config.workdir
        self.workdir_gron = self.workdir.root / 'gron/'
        self.workdir_root_bin = self.workdir.bin
        self.venv = self.workdir_gron / 'venv/'
        self.repo = self.workdir_gron / 'repo/'
        self.gron_cfg_path = self.workdir_gron / 'gron.yml'

    def install(self):
        logger.info('Install gron ...')
        self._prepare_dirs()
        self._create_venv()
        self._clone_repo()
        self._install_venv_requirements()
        self._setup_gron_cfg()
        self._create_bin()
        logger.info("Gron installed")
        #self._delete_repo()

    def make_activate_replaces(self) -> dict:
        return {

        }


    def _prepare_dirs(self):
        self.workdir_gron.mkdir(exist_ok=True)

    def _create_venv(self, force=False):
        if not force and self.venv.exists():
            logger.debug('gron venv exists')
            return
        elif force and os.path.exists(self.venv):
            shutil.rmtree(self.venv)
        try:
            subprocess.run(
                ['virtualenv', '-p', 'python3', str(self.venv)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            logger.debug('gron venv created')
        except subprocess.CalledProcessError as exc:
            logger.error("Error while creating gron venv")
            logger.error(exc.stdout)
            sys.exit(1)

    def _clone_repo(self):
        if self.repo.exists():
            logger.info(
                ("Gron repo already exists, skip clone ({}). "
                "Do `git pull`"
                ).format(self.repo)
            )
            return
        logger.info("Clone gron repo to {}".format(self.repo))
        try:
            subprocess.run(
                ['git', 'clone', '--depth=1', self.repo_url, str(self.repo)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(
                "Error while clone gron repo {}".format(self.repo_url)
            )
            logger.error(exc.stdout)
            sys.exit(1)

    def _delete_repo(self):
        if self.repo.exists():
            shutil.rmtree(self.repo)

    def _install_venv_requirements(self):
        logger.debug('Install gron requirements')
        try:
            subprocess.run(
                [
                    '{}/bin/pip'.format(self.venv),
                    'install',
                    '-r',
                    '{}/requirements.txt'.format(self.repo)
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(
                "Error while install ansible requirements",
            )
            logger.error(exc.stdout)
            sys.exit(1)

    def _create_bin(self):
        bin_source = "{}/bin/python3 {}/src/main.py -c {} $*".format(
            self.venv, self.repo, self.gron_cfg_path,
        )
        with open(self.workdir.bin / 'gron', 'w') as f:
            f.write(bin_source)
        os.chmod(self.workdir.bin / 'gron', 0o0770)


    def _setup_gron_cfg(self):
        replaces = {
            "<ANSIBLE_PATH>": str(self._config.ansible_repo_path),
        }
        with open(self._config.templates_path / 'gron.yml', 'r') as f:
            gron_cfg = f.read()

        for repl_from, repl_to in replaces.items():
            gron_cfg = gron_cfg.replace(repl_from, repl_to)

        with open(self.gron_cfg_path, 'w') as f:
            f.write(gron_cfg)


