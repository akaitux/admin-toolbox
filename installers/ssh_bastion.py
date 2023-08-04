from common.config import get_config
from pathlib import Path
import subprocess
import os


class SSHBastion:

    def __init__(self):
        self.config = get_config()
        self.workdir = self.config.workdir.root
        self.dir = Path(self.config.ssh_bastion_dir)
        self.user = self.config.ssh_bastion_user
        self.config_path = self.config.ssh_bastion_config
        self.host = self.config.ssh_bastion_host
        self.agent_socket = self.dir / "agent.socket"
        self.agent_pid_file = self.dir / "agent.pid"

    def install(self):
        Path(self.dir).mkdir(exist_ok=True)
        self._create_config()

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


