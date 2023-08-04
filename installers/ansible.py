import shutil
import os
import subprocess
import sys
from pathlib import Path
from common.logger import logger
from common.config import get_config


class Ansible:

    def __init__(self, workdir):
        self.config = get_config()
        self.repo: Path = Path(self.config.ansible_repo_path)
        self.version = self.config.ansible_version
        self.repo_url = self.config.ansible_repo_url
        self.workdir = workdir
        self.workdir_ansible = workdir.root / 'ansible/'
        self.workdir_root_bin = workdir.bin
        self.venv = self.workdir_ansible / 'venv/'
        self.ansible_cfg_path = self.config.ansible_cfg_path
        self.ansible_repo_cfg_path = self.config.ansible_repo_cfg_path
        self.activate_path = self.workdir.root / "activate"
        self._prepare_dirs()


    def _prepare_dirs(self):
        self.workdir_ansible.mkdir(exist_ok=True)

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
            logger.debug(p.stdout, p.stderr)
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
                ['git', 'clone', '--depth=1', self.repo_url, str(self.repo)],
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
        requirements = self.repo.joinpath("requirements.txt")
        if not requirements.exists():
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
            else:
                logger.debug("Skip ansible setup, no version or requirements.txt")
            return
        logger.debug('Install ansible requirements')
        try:
            subprocess.run(
                [
                    '{}/bin/pip'.format(self.venv),
                    '--disable-pip-version-check',
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
        if os.path.exists(self.ansible_repo_cfg_path):
            default_src_cfg = self.ansible_repo_cfg_path
        else:
            default_src_cfg = self.config.toolbox_repo_dir / 'ansible.cfg'
        print("Ansible source cfg: {}".format(default_src_cfg))

        tmp_src_cfg_path = self.config.workdir.root / "_tmp_ansible.cfg"
        shutil.copyfile(default_src_cfg, tmp_src_cfg_path)

        if self.config.ssh_bastion_enabled:
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
                ssh_conf += "ssh_args = -F {}\n".format(self.config.ssh_bastion_config)
                with open(tmp_src_cfg_path, 'a') as f:
                    f.write(ssh_conf)

        override = 'N'
        if os.path.exists(self.ansible_cfg_path):
            diff = subprocess.run(
                ['diff', tmp_src_cfg_path, self.ansible_cfg_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.decode('utf-8')
            if not diff:
                override = "y"
            else:
                print("Ansible config diff {} {}:".format(tmp_src_cfg_path, self.ansible_cfg_path))
                print(diff)
                override = input('ansible.cfg already exists, override? \n \t{} -> {} \n (y/N): '.format(
                    tmp_src_cfg_path,
                    self.ansible_cfg_path,
                ))

        else:
            override = "y"

        if override.lower() == 'y':
            shutil.copy(tmp_src_cfg_path, self.ansible_cfg_path)
            os.chmod(self.ansible_cfg_path, 0o0660)
        else:
            logger.info("Skip ansble.cfg")

    def install(self):
        logger.info('Install ansible ...')
        self._create_venv()
        self._clone_repo()
        self._install_venv_requirements()
        self._setup_ansible_cfg()
        self._create_bin_links()
        logger.info("Ansible installed")
        #self._delete_repo()


