import subprocess
import os
import sys
from common.logger import logger
from common.config import get_config
from common.download_file import download_file
from installers.installer import Installer

class Vault(Installer):

    def __init__(self):
        self._config = get_config()
        self.enabled = self._config.vault_enabled
        self.workdir = self._config.workdir
        self.desired_platform = self._config.platform
        self.desired_ver = self._config.vault_ver
        self.download_url = self._config.vault_download_url
        self.bin_path = self.workdir.bin / 'vault'

        self.addr = self._config.vault_addr
        self.login_method = self._config.vault_login_method

    def install(self):
        current_version = self._check_current_ver()
        if current_version == self.desired_ver:
            logger.info('Vault already installed')
            return
        self._download()
        logger.info("Vault installed")

    def make_activate_replaces(self) -> dict:
        replaces = {
            "<VAULT_ADDR>": str(self.addr),
            "<VAULT_LOGIN_METHOD>": str(self.login_method),
            "<VAULT_IS_LOAD_ENV_VARS>": "",
            "<VAULT_LOAD_ENV_VARS>": "",
            "<VAULT_DEACTIVATE LOAD_ENV_VARS>": "",
        }
        load_env_vars = self.generate_env_load()
        deactivate_env_vars = self.generate_env_deactivate()
        if load_env_vars:
            load_env_vars = '\n'.join(load_env_vars)
            deactivate_env_vars = '\n'.join(deactivate_env_vars)
            replaces["<VAULT_IS_LOAD_ENV_VARS>"] = "TRUE"
            replaces["<VAULT_LOAD_ENV_VARS>"] = load_env_vars
            replaces["<VAULT_DEACTIVATE LOAD_ENV_VARS>"] = deactivate_env_vars
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
                raise Exception("Vault stdout -v is empty")
            out = p.stdout.split(' ')
            if len(out) != 3 or out[1][0] != 'v':
                raise Exception("Wrong vault output: {}".format(out))
            return out[1][1:] # v1.0.0[1:] -> 1.0.0

        except subprocess.CalledProcessError as exc:
            logger.error("Error while check vault version")
            logger.error(exc.stdout)
            sys.exit(1)

    def _download(self):
        url = self.download_url.format(
            ver=self.desired_ver,
            os=self.desired_platform,
            arch="amd64",
        )
        zip_arch = self.workdir.tmp / 'vault.zip'

        logger.debug('Download vault {} -> {}'.format(url, zip_arch))
        if not download_file(url, zip_arch, self._config.proxies):
            sys.exit(1)

        # Unzip
        logger.debug('Unzip vault {}'.format(zip_arch))
        try:
            subprocess.run(
                ['unzip', '-d', self.workdir.tmp / 'vault', zip_arch],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("Error while unzip vault")
            logger.error(exc.stdout)
            sys.exit(1)

        logger.debug('Move vault bin to {}'.format(self.bin_path))
        os.remove(zip_arch)
        os.replace(
            self.workdir.tmp / 'vault/vault',
            self.bin_path,
        )
        os.rmdir(self.workdir.tmp / 'vault')

    def generate_env_deactivate(self) -> list:
        load_env_vars = self._config.vault_load_env_vars
        cmds = []
        if not load_env_vars:
            return []
        for env_var, _ in load_env_vars.items():
            cmds.append(
                "unset {}".format(env_var)
            )
        return cmds


    def generate_env_load(self) -> list:
        load_env_vars = self._config.vault_load_env_vars
        cmds = []
        if not load_env_vars:
            return []
        for env_var, vault_key in load_env_vars.items():
            if ";;" not in vault_key:
                print("Error. load_env_vars key must contains ;; ({}: >> {})".format(env_var, vault_key))
                continue
            vault_path, vault_item = [x.strip() for x in vault_key.split(";;")]
            cmds.append(
                "export {}=$(vault kv get -format=json {} | jq -r .data.data.{})".format(env_var, vault_path, vault_item)
            )
        return cmds

