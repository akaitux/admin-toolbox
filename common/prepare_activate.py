from common.config import Config
from common.logger import logger
from installers.ssh_bastion import SSHBastion
from installers.vault import Vault
from installers.python_venv import PythonVenv
from installers.ansible import Ansible


def prepare_activate(config: Config):
    replaces = {
        "<TOOLBOX_NAME>": str(config.toolbox_name),
        "<ANSIBLE_PATH>": str(config.ansible_repo_path),
        "<ANSIBLE_CONFIG>": str(config.ansible_cfg_path),
        "<VAULT_ADDR>": str(config.vault_addr),
        "<VAULT_LOGIN_METHOD>": str(config.vault_login_method),
        "<WORKDIR_ROOT>": str(config.workdir.root),
        "<WORKDIR_TMP>": str(config.workdir.tmp),
        "<WORKDIR_BIN>": str(config.workdir.bin),
        "<WORKDIR_ANSIBLE>": str(config.workdir.root / 'ansible/'),
        "<GCLOUD_ENABLED>": str(config.gcloud_enabled),
        "<GCLOUD_CFG_PATH>": str(config.gcloud_cfg_path),
        "<KUBE_ENABLED>": str(config.kubectl_enabled),
        "<KUBE_CONFIG_PATH>": str(config.kube_config_path),
    }
    with open(config.activate_tpl_path, 'r') as f:
        activate_tpl = f.read()

    for repl_from, repl_to in replaces.items():
        activate_tpl = activate_tpl.replace(repl_from, repl_to)

    activate_tpl = _add_terra_aliases(activate_tpl, config)
    activate_tpl = _add_ssh_aliases(activate_tpl, config)
    activate_tpl = _add_vault(activate_tpl)
    activate_tpl = _add_python(activate_tpl)
    activate_tpl = _add_ansible(activate_tpl, config)

    with open(config.activate_path, 'w') as f:
        f.write(activate_tpl)


def _add_ansible(activate_tpl, config):
    ansible = Ansible()
    if not ansible.enabled:
        activate_tpl = activate_tpl.replace("<ANSIBLE_ENABLED>", "")
        return activate_tpl
    activate_tpl = activate_tpl.replace("<ANSIBLE_ENABLED>", "true")
    activate_tpl = activate_tpl.replace("<ANSIBLE_CONFIG>", str(ansible.repo_cfg_path))
    activate_tpl = activate_tpl.replace("<ANSIBLE_PATH>", str(ansible.repo))
    return activate_tpl


def _add_python(activate_tpl):
    python_venv = PythonVenv()
    if not python_venv.enabled:
        activate_tpl = activate_tpl.replace("<PYTHON_VENV_ENABLED>", "")
        return activate_tpl
    activate_tpl = activate_tpl.replace("<PYTHON_VENV_ENABLED>", "true")
    activate_tpl = activate_tpl.replace("<PYTHON_VENV>", str(python_venv.venv))
    return activate_tpl

def _add_vault(activate_tpl):
    vault = Vault()
    load_env_vars = vault.generate_env_load()
    deactivate_env_vars = vault.generate_env_deactivate()
    if load_env_vars:
        load_env_vars = '\n'.join(load_env_vars)
        deactivate_env_vars = '\n'.join(deactivate_env_vars)
        activate_tpl = activate_tpl.replace("<VAULT_IS_LOAD_ENV_VARS>", "TRUE")
        activate_tpl = activate_tpl.replace("<VAULT_LOAD_ENV_VARS>", load_env_vars)
        activate_tpl = activate_tpl.replace("<VAULT_LOAD_ENV_VARS>", load_env_vars)
        activate_tpl = activate_tpl.replace("<VAULT_DEACTIVATE LOAD_ENV_VARS>", deactivate_env_vars)
    else:
        activate_tpl = activate_tpl.replace("<VAULT_IS_LOAD_ENV_VARS>", "")
    return activate_tpl


def _add_ssh_aliases(activate_tpl, config):
    ssh = SSHBastion()
    if not config.ssh_bastion_enabled:
        return activate_tpl
    alias = "ssh='ssh -F {}'".format(config.ssh_bastion_config)
    activate_tpl = activate_tpl.replace("<SSH_ALIAS>", alias)
    run_cmd = ' '.join([str(x) for x in ssh.generate_run_agent_cmd()])
    activate_tpl = activate_tpl.replace("<SSH_AGENT_CMD_RUN>", run_cmd)
    activate_tpl = activate_tpl.replace("<SSH_AGENT_PID_PATH>", str(ssh.agent_pid_file))
    activate_tpl = activate_tpl.replace("<SSH_AGENT_SOCK>", str(ssh.agent_socket))
    activate_tpl = activate_tpl.replace("<SSH_BASTION_HOST>", str(ssh.host))
    return activate_tpl



def _add_terra_aliases(activate_tpl, config):
    aliases = {
        "<ALIAS_TERRAFORM>": "terraform='terraform'",
        "<ALIAS_TERRAGRUNT>": "terragrunt='terragrunt'",
        "<ALIAS_ARGOCD>": f"argocd='argocd --config {config.argocd_cfg_path}'",
    }
    if config.terraform_use_proxy:
        if config.proxies['https']:
            aliases["<ALIAS_TERRAFORM>"]= "terraform='HTTPS_PROXY={} terraform'".format(
                config.proxies['https'],
            )
        elif config.proxies['http']:
            aliases["<ALIAS_TERRAFORM>"]= "terraform='HTTP_PROXY={} terraform'".format(
                config.proxies['http'],
            )
    if config.terragrunt_use_proxy:
        if config.proxies['https']:
            aliases["<ALIAS_TERRAGRUNT>"]= "terragrunt='HTTPS_PROXY={} terragrunt'".format(
                config.proxies['https'],
            )
        elif config.proxies['http']:
            aliases["<ALIAS_TERRAGRUNT>"]= "terragrunt='HTTP_PROXY={} terragrunt'".format(
                config.proxies['http'],
            )
    for repl_from, repl_to in aliases.items():
        activate_tpl = activate_tpl.replace(repl_from, repl_to)
    return activate_tpl
