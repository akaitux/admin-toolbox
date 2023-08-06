from common.config import get_config
from pathlib import Path
import subprocess
import os
from common.logger import logger

from installers.installer import Installer


class SSH(Installer):

    def __init__(self):
        self._config = get_config()
        self.enabled = self._config.ssh_enabled
        self.workdir = self._config.workdir.root
        self.dir = self.workdir / "ssh"
        self.config_path = self.dir / "config"
        self.load_keys_from_host = self._config.ssh_load_keys_from_host
        self.agent_socket = self.dir / "agent.socket"
        self.agent_pid_file = self.dir / "agent.pid"
        self.enable_autocomplete_from_ansible = self._config.ssh_enable_autocomplete_from_ansible
        self.additional_config = self._load_additional_config()

    def _load_additional_config(self) -> str:
        config_dir = self._config.config_path.parents[0]
        # config.json -> config.ssh
        ssh_config_name = self._config.config_path.name.split('.')[0] + '.ssh'
        ssh_config_path = Path(config_dir / ssh_config_name)
        if not ssh_config_path.exists():
            logger.debug("No ssh additional config")
            return ""
        logger.debug("SSH: Read additional config {}".format(ssh_config_path))
        with open(ssh_config_path, 'r') as f:
            config = f.read()
            config = config.replace('<IDENTITY_AGENT>', str(self.agent_socket))
            return config

    def install(self):
        Path(self.dir).mkdir(exist_ok=True)
        self._create_config()

    def make_activate_replaces(self) -> dict:
        replaces = {}

        if self.enabled:
            replaces['<SSH_ENABLED>'] = "true"
        else:
            replaces['<SSH_ENABLED>'] = ""

        if self.enable_autocomplete_from_ansible:
            replaces["<SSH_ENABLE_AUTOCOMPLETE_FROM_ANSIBLE>"] = "true"
        else:
            replaces["<SSH_ENABLE_AUTOCOMPLETE_FROM_ANSIBLE>"] = ""

        alias = "ssh='ssh -F {}'".format(self.config_path)
        replaces["<SSH_ALIAS>"] = alias
        run_cmd = ' '.join([str(x) for x in self.generate_run_agent_cmd()])
        replaces["<SSH_AGENT_CMD_RUN>"] = run_cmd
        replaces["<SSH_AGENT_PID_PATH>"] = str(self.agent_pid_file)
        replaces["<SSH_AGENT_SOCK>"] = str(self.agent_socket)
        replaces["<SSH_LOAD_KEYS_FROM_HOST>"] = str(self.load_keys_from_host)
        replaces["<SSH_CONFIG>"] = str(self.config_path)
        return replaces

    def _create_config(self):
        config = ""
        if self.additional_config:
            config = self.additional_config

        with open(self.config_path, "w") as f:
            f.write(config)

    def generate_run_agent_cmd(self) -> list:
        return ["ssh-agent", "-a", self.agent_socket]

    def generate_stop_agent_cmd(self) -> list:
        return ["kill", "-9", "$(cat {})".format(self.agent_pid_file)]

    def run_agent_cmd(self):
        cmd = self.generate_run_agent_cmd()
        process = subprocess.Popen(cmd)
        with open(self.agent_pid_file, "w") as f:
            f.write(str(process.pid))

    def stop_agent(self):
        if not os.path.exists(self.agent_pid_file):
            print("ssh-agent doesn't exists (no pid file {})".format(self.agent_pid_file))
            return
        with open(self.agent_pid_file, "r") as f:
            pid = f.read()
        cmd = ["kill", "-9", pid]
        subprocess.run(cmd)
        os.remove(self.agent_pid_file)


