import shutil
import os
import subprocess
import sys
from pathlib import Path
from common.logger import logger
from common.config import get_config
from installers.python_venv import PythonVenv
from installers.installer import Installer
from installers.ssh import SSH


class Ansible(Installer):

    def __init__(self):
        self._config = get_config()
        self.workdir = self._config.workdir
        self.enabled = self._config.ansible_enabled
        self.repo: Path = Path(self._config.ansible_repo_path)
        self.version = self._config.ansible_version
        self.repo_url = self._config.ansible_repo_url
        self.workdir_ansible = self.workdir.root / 'ansible/'
        self.workdir_root_bin = self.workdir.bin
        self.venv = self.workdir_ansible / 'venv/'
        self.cfg_path = self._config.ansible_cfg_path
        self.repo_cfg_path = self._config.ansible_repo_cfg_path
        self.activate_path = self.workdir.root / "activate"
        self.use_ssh_agent = self._config.ansible_use_ssh_agent
        self.python = PythonVenv()
        self._prepare_dirs()

    def install(self):
        self._create_venv()
        self._clone_repo()
        self._install_venv_requirements()
        self._setup_ansible_cfg()
        self._create_bin_links()
        #self._delete_repo()

    def make_activate_replaces(self) -> dict:
        replaces = {
            "<ANSIBLE_PATH>": str(self.repo),
            "<ANSIBLE_CONFIG>": str(self.cfg_path),
            "<ANSIBLE_WORKDIR>": str(self.workdir_ansible),
            "<ANSIBLE_BINDIR>":  str(self.workdir_root_bin / 'ansible'),
        }
        if not self.enabled:
            replaces["<ANSIBLE_ENABLED>"] = ""
        else:
            replaces["<ANSIBLE_ENABLED>"] = "true"
        return replaces

    def _prepare_dirs(self):
        self.workdir_ansible.mkdir(exist_ok=True)

    def _create_venv(self):
        if self.venv.exists():
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
            logger.debug('ansible venv created')
        except subprocess.CalledProcessError as exc:
            logger.error("Error while creating ansible venv")
            logger.error(exc.stdout)
            sys.exit(1)

    def _clone_repo(self):
        if not self.repo_url:
            logger.info("No ansible repo, skip clone")
            return
        if self.repo.exists():
            logger.info(
                ("Ansible repo already exists, skip clone ({}). "
                "Do `git pull`"
                ).format(self.repo)
            )
            return
        logger.info("Clone ansible repo to {}".format(self.repo))
        try:
            subprocess.run(
                ['git', 'clone', self.repo_url, str(self.repo)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(
                "Error while clone ansible repo {}".format(self.repo_url)
            )
            logger.error(exc.stdout)
            sys.exit(1)

    def _delete_repo(self):
        if self.repo.exists():
            shutil.rmtree(self.repo)

    def _install_venv_requirements(self):
        if self.version:
            subprocess.run(
                [
                    '{}/bin/pip'.format(self.venv),
                    '--disable-pip-version-check',
                    'install',
                    'ansible=={}'.format(self.version),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        requirements = self.repo.joinpath("requirements.txt")
        logger.debug('Install ansible requirements')
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
                "Error while install ansible requirements",
            )
            logger.error(exc.stdout)
            sys.exit(1)

    def _create_bin_links(self):
        bin_files = [
            f
            for f in os.listdir(self.venv / 'bin')
            if f.startswith('ansible')
        ]
        ansible_bin_dir = self.workdir_root_bin / 'ansible'
        ansible_bin_dir.mkdir(exist_ok=True)
        for f in bin_files:
            link_from = self.venv / 'bin/{}'.format(f)

            link_to = ansible_bin_dir / f

            try:
                subprocess.run(
                    ['ln', '-f', link_from, link_to],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                logger.debug('Link created: {}'.format(link_to))
            except subprocess.CalledProcessError as exc:
                logger.error(
                    "Error while link ansible bin {}".format(f),
                )
                logger.error(exc.stdout)
                sys.exit(1)

    def _setup_ansible_cfg(self):
        if os.path.exists(self.repo_cfg_path):
            default_src_cfg = self.repo_cfg_path
        else:
            default_src_cfg = self._config.toolbox_repo_dir / 'ansible.cfg'
        print("Ansible source cfg: {}".format(default_src_cfg))

        tmp_src_cfg_path = self._config.workdir.root / "_tmp_ansible.cfg"
        shutil.copyfile(default_src_cfg, tmp_src_cfg_path)

        ssh = SSH()

        if ssh.enabled and self.use_ssh_agent:
            is_ssh_connection_exists = False
            with open(tmp_src_cfg_path, 'r') as f:
                cfg = f.read()
                if "[ssh_connection]" in cfg:
                    print(
                        "[ssh_connection] section already exists in ansible config {}, ".format(default_src_cfg),
                        "skip ssh bastion setup for ansible"
                    )
                    is_ssh_connection_exists = True

            if not is_ssh_connection_exists:
                ssh_conf = "[ssh_connection]\n"
                ssh_conf += "ssh_args = -F {}\n".format(ssh.config_path)
                with open(tmp_src_cfg_path, 'a') as f:
                    f.write(ssh_conf)

        override = 'N'
        if os.path.exists(self.cfg_path):
            diff = subprocess.run(
                ['diff', tmp_src_cfg_path, self.cfg_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.decode('utf-8')
            if not diff:
                override = "y"
            else:
                print("Ansible config diff {} {}:".format(tmp_src_cfg_path, self.cfg_path))
                print(diff)
                override = input('ansible.cfg already exists, override? \n \t{} -> {} \n (y/N): '.format(
                    tmp_src_cfg_path,
                    self.cfg_path,
                ))

        else:
            override = "y"

        if override.lower() == 'y':
            shutil.copy(tmp_src_cfg_path, self.cfg_path)
            os.chmod(self.cfg_path, 0o0660)
        else:
            logger.info("Skip ansble.cfg")



