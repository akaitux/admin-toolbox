from typing import Optional
from common.config import get_config, Config
from common.logger import logger
import shutil
from pathlib import Path
import subprocess
import os
import sys


class PythonVenv:
    def __init__(self, workdir: Optional[Path] = None):
        self.config: Config = get_config()
        self.enabled = self.config.python_enabled
        self.workdir = Path()
        self.is_standalone = False
        if workdir:
            self.workdir = workdir
        else:
            self.workdir = self.config.workdir.root / 'python'
            self.is_standalone = True
        self.venv = self.workdir / 'venv'
        self.workdir_root_bin = self.config.workdir.bin

    def install(self):
        self._prepare_dirs()
        self._create_venv()
        if self.is_standalone:
            self.install_packages(self.config.python_packages)

    def _prepare_dirs(self):
        if self.workdir.exists():
            shutil.rmtree(self.workdir)
        self.workdir.mkdir()

    def _create_venv(self, force=False):
        if not force and self.venv.exists():
            logger.debug('ansible venv exists')
            return
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
