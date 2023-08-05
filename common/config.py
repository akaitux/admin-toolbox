import sys
from common.workdir import Workdir
import os
import json
import platform
from pathlib import Path
from common.singleton import Singleton
from typing import Optional


class Config(metaclass=Singleton):

    def  __init__(
            self,
            toolbox_name: str,
            toolbox_repo_dir: Path,
            workdir: Workdir,
            config_ini_path: Path,
        ):

        self.toolbox_name = toolbox_name
        self.config_path = Path(config_ini_path).expanduser().resolve()

        if not toolbox_repo_dir:
            return

        self.home = os.environ.get('HOME')
        self.workdir = workdir

        self.toolbox_repo_dir = toolbox_repo_dir

        self.templates_path = self.toolbox_repo_dir / 'templates/'
        self.activate_tpl_path = self.templates_path / 'activate/'
        self.activate_path = self.workdir.root / 'activate'

        self.platform = ""
        if sys.platform.startswith("linux"):
            self.platform = "linux"
        elif sys.platform == "darwin":
            self.platform = "darwin"
        self.is_x64 = platform.machine() in ("i386", "AMD64", "x86_64")

        self.python_enabled = False
        self.python_packages = []

        self.vault_enabled = False
        self.vault_addr = ""
        self.vault_ver = ""
        self.vault_url = ""

        self.terraform_enabled = False
        self.terraform_ver = ""
        self.terraform_url = ""
        self.terraform_use_proxy = False

        self.terragrunt_enabled = False
        self.terragrunt_ver = ""
        self.terragrunt_url = ""
        self.terragrunt_use_proxy = False

        self.k9s_enabled = False
        self.k9s_ver = ""
        self.k9s_url = ""

        self.kubectl_enabled = False
        self.kubectl_ver = ""
        self.kubectl_url = ""
        self.kube_config_path = self.workdir.root / 'kube'

        self.gcloud_enabled = False
        self.gcloud_ver = ""
        self.gcloud_url = ""
        self.gcloud_cfg_path = self.workdir.root / 'gcloud/cfg'

        self.proxies = {'http': '', 'https': ''}

        self.ansible_enabled = False
        self.ansible_repo_url = ""
        self.ansible_repo_path: Path = Path()
        self.ansible_version = ""
        self.ansible_venv_packages = []
        self._ansible_repo_path_file = self.workdir.root / '.ansible_path'
        self.ansible_cfg_path = ""

        self.argocd_enabled = False
        self.argocd_cfg_path = self.workdir.root / "argocd.cfg"

        self.gron_enabled = False
        self.gron_repo_url = ""

        self.ssh_bastion_enabled = False
        self.ssh_bastion_user = ""
        self.ssh_bastion_host = ""
        self.ssh_bastion_dir = self.workdir.root / "ssh"
        self.ssh_bastion_config = self.ssh_bastion_dir / "config"

        self._parse_config()

        self.ansible_repo_cfg_path = ""
        self.ansible_cfg_path = Path(self.workdir.root , "ansible") / "ansible.cfg"
        if self.ansible_repo_path:
            ansible_repo_cfg_path = Path(self.ansible_repo_path) / "ansible.cfg"
            if ansible_repo_cfg_path.exists():
                self.ansible_repo_cfg_path = ansible_repo_cfg_path


    def configure_python(self, config: dict):
        section_name = "python"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.python_enabled = section_cfg.get("enabled", False)
        self.python_packages = section_cfg.get("packages", [])


    def configure_vault(self, config: dict):
        section_name = "vault"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.vault_enabled = True
        self.vault_ver = section_cfg.get("version", "")
        self.vault_url = section_cfg.get("download_url", "")
        self.vault_addr = section_cfg.get('addr', "")
        self.vault_login_method = section_cfg.get('login_method', "userpass")
        self.vault_load_env_vars = section_cfg.get('load_env_vars', {})

    def configure_terraform(self, config: dict):
        section_name = "terraform"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.terraform_enabled = True
        self.terraform_ver = section_cfg.get("version", "")
        self.terraform_url = section_cfg.get("download_url", "")
        self.terraform_use_proxy = section_cfg.get("use_proxy", False)

    def configure_terragrunt(self, config: dict):
        section_name = "terragrunt"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.terragrunt_enabled = True
        self.terragrunt_ver = section_cfg.get("version", "")
        self.terragrunt_url = section_cfg.get("download_url", "")
        self.terragrunt_use_proxy = section_cfg.get("use_proxy", False)


    def configure_gcloud(self, config: dict):
        section_name = "gcloud"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.gcloud_enabled = True
        self.gcloud_ver = section_cfg.get("version", "")
        self.gcloud_url = section_cfg.get("download_url", "")

    def configure_k9s(self, config: dict):
        section_name = "k9s"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.k9s_enabled = True
        self.k9s_ver = section_cfg.get("version", "")
        self.k9s_url = section_cfg.get("download_url", "")

    def configure_kubectl(self, config: dict):
        section_name = "kubectl"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.kubectl_enabled = True
        self.kubectl_ver = section_cfg.get("version", "")
        self.kubectl_url = section_cfg.get("download_url", "")

    def configure_gron(self, config: dict):
        section_name = "gron"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.gron_enabled = True
        self.gron_repo_url = section_cfg.get("repo_url")

    def configure_helm(self, config: dict):
        section_name = "helm"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.helm_enabled = True
        self.helm_ver = section_cfg.get("version", "")
        self.helm_url = section_cfg.get("download_url", "")

    def configure_argocd(self, config: dict):
        section_name = "argocd"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.argocd_enabled = True
        self.argocd_ver = section_cfg.get("version", "")
        self.argocd_url = section_cfg.get("download_url", "")

    def configure_ansible(self, config: dict):
        section_name = "ansible"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.ansible_enabled = True
        self.ansible_version = section_cfg.get("version", "")
        self.ansible_venv_packages = section_cfg.get("venv_packages", [])
        self.ansible_repo_url = section_cfg.get("repo_url", "")
        ansible_repo_path = section_cfg.get("repo_path", "")
        if ansible_repo_path:
            self.ansible_repo_path = Path(ansible_repo_path).expanduser().resolve()


    def configure_proxy(self, config: dict):
        section_name = "proxy"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.proxies['http'] = section_cfg.get('http_addr', '')
        self.proxies['https'] = section_cfg.get('https_addr', '')

    def configure_ssh_bastion(self, config: dict):
        section_name = "ssh_bastion"
        section_cfg = config.get(section_name, {})
        if not section_cfg:
            print("No {n} in config or {n} is empty, skip".format(n=section_name))
            return
        if not section_cfg.get("enabled", False):
            print("{} disabled, skip".format(section_name))
            return
        self.ssh_bastion_enabled = True
        self.ssh_bastion_user = section_cfg.get("user", "")
        self.ssh_bastion_host = section_cfg.get("host", "")



    def _parse_config(self):
        config: dict = self._load_from_file()
        self.configure_python(config)
        self.configure_vault(config)
        self.configure_terraform(config)
        self.configure_terragrunt(config)
        self.configure_gcloud(config)
        self.configure_k9s(config)
        self.configure_kubectl(config)
        self.configure_gron(config)
        self.configure_helm(config)
        self.configure_argocd(config)
        self.configure_ansible(config)
        self.configure_proxy(config)
        self.configure_ssh_bastion(config)


    def _load_from_file(self) -> dict:
        # toolbox_repo_dir - abs path to dir with current admin toolbox repo
        # Needs for access to internal files like templates
        config_path = ""
        if self.config_path:
           config_path = self.config_path
        else:
            config_path = Path(self.toolbox_repo_dir) / 'config.json'
        with open(config_path, 'r') as f:
            try:
                return json.loads(f.read())
            except json.decoder.JSONDecodeError as e:
                print("JSON config invalid: {}\n\t{}".format(config_path, e))
                sys.exit(1)

    def _read_ansible_repo_path_from_file(self):
        if not os.path.exists(self._ansible_repo_path_file):
            return
        with open(self._ansible_repo_path_file, 'r') as f:
            return Path(f.read())

    def _save_ansible_repo_path_to_file(self):
        with open(self._ansible_repo_path_file, 'w') as f:
            f.write(str(self.ansible_repo_path))


def get_config():
    return Config(None, None, None)
