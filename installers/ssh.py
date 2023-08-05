from common.config import get_config
from pathlib import Path
import subprocess
import os

from installers.installer import Installer


class SSH(Installer):

    def __init__(self):
        self._config = get_config()
        self.enabled = self._config.ssh_enabled
        self.workdir = self._config.workdir.root
        self.dir = self.workdir / "ssh"
        self.config_path = self.dir / "config"
        self.user = self._config.ssh_user
        self.host = self._config.ssh_host
        self.agent_socket = self.dir / "agent.socket"
        self.agent_pid_file = self.dir / "agent.pid"

    def install(self):
        Path(self.dir).mkdir(exist_ok=True)
        self._create_config()

    def make_activate_replaces(self) -> dict:
        replaces = {}
        if self.enabled:
            replaces['<SSH_ENABLED>'] = "true"
        else:
            replaces['<SSH_ENABLED>'] = ""
        alias = "ssh='ssh -F {}'".format(self.config_path)
        replaces["<SSH_ALIAS>"] = alias
        run_cmd = ' '.join([str(x) for x in self.generate_run_agent_cmd()])
        replaces["<SSH_AGENT_CMD_RUN>"] = run_cmd
        replaces["<SSH_AGENT_PID_PATH>"] = str(self.agent_pid_file)
        replaces["<SSH_AGENT_SOCK>"] = str(self.agent_socket)
        replaces["<SSH_HOST>"] = str(self.host)
        return replaces

    def _create_config(self):
        config = "HOST *\n"
        config += "\tAddKeysToAgent yes\n"
        config += "\tForwardAgent yes\n"

        config += "\tIdentityAgent {}".format(self.agent_socket)
        if self.user:
            config += "\n\tUser {}".format(self.user)
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


