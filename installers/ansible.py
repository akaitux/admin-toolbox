import shutil
import os
import subprocess
import sys
from pathlib import Path
from common.logger import logger
from common.config import get_config
from configparser import ConfigParser
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
        self.venv = PythonVenv(self.workdir_ansible / 'venv/')
        self.cfg_path = self._config.ansible_cfg_path
        self.repo_cfg_path = self._config.ansible_repo_cfg_path
        self.activate_path = self.workdir.root / "activate"
        self.inventory_file_path = self.workdir_ansible / "inventory.ini"
        self.use_ssh_agent = self._config.ansible_use_ssh_agent
        self.use_venv_for_localhost_delegation = self._config.ansible_use_venv_for_localhost_delegation
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
        self.venv.create_venv(force=True)

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
            self.venv.install_packages(['ansible=={}'.format(self.version)])
        requirements = self.repo.joinpath("requirements.txt")
        logger.debug('Install ansible requirements')
        if requirements.exists():
            try:
                self.venv.install_requirements(requirements)
            except subprocess.CalledProcessError as exc:
                logger.error(
                    "Error while install ansible requirements",
                )
                logger.error(exc.stdout)
                sys.exit(1)

    def _create_bin_links(self):
        bin_files = [
            f
            for f in os.listdir(self.venv.bin_path)
            if f.startswith('ansible')
        ]
        ansible_bin_dir = self.workdir_root_bin / 'ansible'
        ansible_bin_dir.mkdir(exist_ok=True)
        for f in bin_files:
            link_from = self.venv.bin_path / f
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

    def _setup_ansible_cfg_ssh(self, tmp_src_cfg_path: Path, default_src_cfg: Path):
        ssh = SSH()
        if not ssh.enabled or not self.use_ssh_agent:
            logger.debug("Ansible: not ssh.enabled or not self.use_ssh_agent")
            return
        config = ConfigParser()
        config.read(tmp_src_cfg_path)
        if "ssh_connection" in config:
            logger.warn(
                "[ssh_connection] section already exists in ansible config {}, ".format(default_src_cfg),
                "skip ssh bastion setup for ansible"
            )
            return
        config["ssh_connection"] = {}
        config["ssh_connection"]["ssh_args"] = "-F {}\n".format(ssh.config_path)
        with open(tmp_src_cfg_path, 'w') as f:
            config.write(f)

    def _setup_ansible_cfg_inventory(
            self,
            tmp_src_cfg_path: Path,
            tmp_src_inventory_path: Path
        ):
        if not self.use_venv_for_localhost_delegation:
            logger.debug("Ansible: use_venv_for_localhost_delegation is false")
            return
        from configparser import ConfigParser
        config = ConfigParser()
        config.read(tmp_src_cfg_path)

        inventory_content = (
            "localhost ansible_connection=local "
            "ansible_python_interpreter={}/python\n".format(self.venv.bin_path)
        )

        with open(tmp_src_inventory_path, 'w') as f:
            f.write(inventory_content)

        self._copy_file(tmp_src_inventory_path, self.inventory_file_path)

        if not 'defaults' in config:
            config['defaults'] = {}

        if not 'inventory' in config['defaults']:
            config['default']['inventory'] = str(self.inventory_file_path)
        else:
            current_inventory = config['defaults']['inventory']
            config['defaults']['inventory'] = "{},{}".format(
                current_inventory,
                self.inventory_file_path,
            )

        with open(tmp_src_cfg_path, 'w') as f:
            config.write(f)


    def _setup_ansible_cfg(self):
        if os.path.exists(self.repo_cfg_path):
            default_src_cfg = Path(self.repo_cfg_path)
        else:
            default_src_cfg = self._config.toolbox_repo_dir / 'ansible.cfg'
        print("Ansible source cfg: {}".format(default_src_cfg))

        tmp_src_cfg_path = self._config.workdir.root / "_tmp_ansible.cfg"
        shutil.copyfile(default_src_cfg, tmp_src_cfg_path)

        self._setup_ansible_cfg_ssh(tmp_src_cfg_path, default_src_cfg)

        tmp_src_inventory_path = self._config.workdir.root / "_tmp_inventory.ini"
        self._setup_ansible_cfg_inventory(tmp_src_cfg_path, tmp_src_inventory_path)

        self._copy_file(tmp_src_cfg_path, self.cfg_path)
        os.chmod(self.cfg_path, 0o0660)

    def _copy_file(self, src, dest, no_ask=False):
        if no_ask:
            override = 'Y'
        else:
            override = 'N'
        if not no_ask and os.path.exists(self.cfg_path):
            diff = subprocess.run(
                ['diff', src, dest],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.decode('utf-8')
            if not diff:
                override = "y"
            else:
                print("File config diff {} {}:".format(src, dest))
                print(diff)
                override = input('File already exists, override? \n \t{} -> {} \n (y/N): '.format(
                    src, dest
                ))

        else:
            override = "y"

        if override.lower() == 'y':
            shutil.copy(src, dest)
        else:
            logger.info("Skip {}", dest)

