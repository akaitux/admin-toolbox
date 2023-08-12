import traceback
from typing import Optional
from common.config import get_config, Config
from common.logger import logger
import shutil
from pathlib import Path
import subprocess
import os
import sys

from installers.installer import Installer


class PythonVenv(Installer):
    def __init__(self, workdir: Optional[Path] = None):
        self._config: Config = get_config()
        self.enabled = self._config.python_enabled
        self.workdir = Path()
        self.is_standalone = False
        if workdir:
            self.workdir = workdir
        else:
            self.workdir = self._config.workdir.root / 'python'
            self.is_standalone = True
        self.venv = self.workdir / 'venv'
        self.workdir_root_bin = self._config.workdir.bin

    def install(self):
        self._prepare_dirs()
        self._create_venv(force=True)
        if self.is_standalone:
            self.install_packages(self._config.python_packages)

    def make_activate_replaces(self) -> dict:
        replaces = {}
        if not self.enabled:
            replaces["<PYTHON_VENV_ENABLED>"] = ""
        else:
            replaces["<PYTHON_VENV_ENABLED>"] = "true"
        replaces["<PYTHON_VENV>"] = str(self.venv)
        return replaces

    def _prepare_dirs(self):
        self.workdir.mkdir(exist_ok=True)

    def _is_venv_valid(self):
        if not self.venv.exists():
            return False
        pip_bin = self.venv / 'bin/pip'
        try:
            p = subprocess.run(
                [str(pip_bin), '-h'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if p.stderr:
                logger.debug(p.stderr.decode("utf-8"))
            if p.returncode == 0:
                return True
        except:
            logger.debug(traceback.format_exc())
            return False
        return False

    def _create_venv(self, force=False):
        if not force and self.venv.exists():
            if not self._is_venv_valid():
                shutil.rmtree(self.venv)
            else:
                logger.debug("Python venv {} already exists and OK".format(self.venv))
        elif force and os.path.exists(self.venv):
            shutil.rmtree(self.venv)
        try:
            p = subprocess.run(
                ['virtualenv', '-p', 'python3', str(self.venv)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if p.stdout:
                logger.debug(p.stdout.decode("utf-8"))
            if p.stderr:
                logger.debug(p.stderr.decode("utf-8"))
            logger.debug('python venv created')
        except subprocess.CalledProcessError as exc:
            logger.error("Error while creating python venv")
            logger.error(exc.stdout)
            sys.exit(1)


    def install_packages(self, packages: list):
        for package in packages:
            try:
                p = subprocess.run(
                    [
                        str(self.venv / 'bin/pip'),
                        'install',
                        '--disable-pip-version-check',
                        package
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                if p.stdout:
                    logger.debug(p.stdout.decode("utf-8"))
                if p.stderr:
                    logger.debug(p.stderr.decode("utf-8"))
            except subprocess.CalledProcessError as exc:
                logger.error("Error while installing python venv packages")
                logger.error(exc.stdout)
                sys.exit(1)

    def install_requirements(self, requirements: Path):
        logger.debug('Install requirements {}'.format(requirements))
        try:
            subprocess.run(
                [
                    '{}/bin/pip'.format(self.venv),
                    '--disable-pip-version-check',
                    'install',
                    '-r',
                    requirements,
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(
                "Error while install requirements",
            )
            logger.error(exc.stdout)
            sys.exit(1)
