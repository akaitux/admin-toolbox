#!/usr/bin/python3
import os
import sys
from pathlib import Path
from argparse import ArgumentParser
from common.logger import logger
from common.validators import check_dependencies, validate_platform
from common.logger import setup_logger
from common.config import Config
from common.workdir import Workdir
from common.prepare_activate import prepare_activate
from installers.python_venv import PythonVenv
from installers.ansible import Ansible
from installers.vault import Vault
from installers.terraform import Terraform
from installers.terragrunt import Terragrunt
from installers.gcloud import Gcloud
from installers.k9s import K9S
from installers.kubectl import Kubectl
from installers.gron import Gron
from installers.helm import Helm
from installers.argocd import ArgoCD
from installers.ssh_bastion import SSHBastion


def run(args):
    setup_logger(debug=args.debug)

    workdir = Workdir(root_dir=args.workdir)
    workdir.prepare()

    # Init config
    current_exec_dir_path = Path(os.path.realpath(__file__)).parent
    config = Config(
        toolbox_name=args.toolbox_name,
        toolbox_repo_dir=current_exec_dir_path,
        workdir=workdir,
        config_ini_path=args.config,
    )

    if args.info:
        print("\n\n")
        print(get_info(config))
        sys.exit(0)

    check_dependencies()

    validate_platform()

    try:
        logger.info("Make 'activate' ...")

        prepare_activate(config)

        logger.info("Install ...")

        if config.python_enabled:
            python_venv = PythonVenv()
            print("\n")
            python_venv.install()
        else:
            logger.info("Skip python")

        if config.ansible_enabled:
            ansible = Ansible()
            print("\n")
            ansible.install()
        else:
            logger.info("Skip ansible")

        if config.vault_enabled:
            vault = Vault()
            print("\n")
            vault.install()
        else:
            logger.info("Skip vault")

        if config.terraform_enabled:
            terraform = Terraform(workdir)
            print("\n")
            terraform.install()
        else:
            logger.info("Skip terraform")

        if config.terragrunt_enabled:
            terragrunt = Terragrunt(workdir)
            print("\n")
            terragrunt.install()
        else:
            logger.info("Skip terragrunt")

        if config.gcloud_enabled:
            gcloud = Gcloud(workdir)
            print("\n")
            gcloud.install()
        else:
            logger.info("Skip gcloud")

        if config.kubectl_enabled:
            kubectl = Kubectl(workdir)
            print("\n")
            kubectl.install()
        else:
            logger.info("Skip kubectl")

        if config.k9s_enabled:
            k9s = K9S(workdir)
            print("\n")
            k9s.install()
        else:
            logger.info("Skip k9s")

        if config.gron_enabled:
            gron = Gron(workdir)
            print("\n")
            gron.install()
        else:
            logger.info("Skip gron")

        if config.helm_enabled:
            helm = Helm(workdir)
            print("\n")
            helm.install()
        else:
            logger.info("Skip helm")

        if config.argocd_enabled:
            argocd = ArgoCD(workdir)
            print("\n")
            argocd.install()
        else:
            logger.info("Skip argocd")

        if config.ssh_bastion_enabled:
            ssh= SSHBastion()
            print("\n")
            ssh.install()
        else:
            logger.info("Skip ssh bastion")
    finally:
        workdir.cleanup()

    info = get_info(config)
    _save_info_to_file(config)
    print("\n\n")
    print(info)


# for alias admin-toolbox-info
def _save_info_to_file(config):
    with open(config.workdir.root / '.info', 'w') as f:
        f.write(get_info(config))


def get_info(config):
    help = []
    help.append("To start working with the env: \n\tsource {}".format(config.activate_path))
    help.append("To end working with the env: \n\tdeactivate")
    help.append("Add alias to .<shell>rc: \n\t alias [alias]=\"source {}\"".format(config.activate_path))
    help.append("\nToolbox dir: {}".format(config.workdir.root))
    help.append("Ansible: {}".format(config.ansible_repo_path))
    if config.gcloud_ver and config.gcloud_url:
        help.append("\nGoogle:\n\tLogin to gcloud with: gcloud auth login --no-launch-browser")
        help.append("\tToestaan == accept")
        help.append("\tUse browser with proxy (waterfox?)")
        help.append("\tExample for get kubectl creds:>")
        help.append("\t  gcloud container clusters <cluster> --region <region> --project <project>")
    help.append("\nCLI:")
    help.append("\tVault login:> vault-login <username>")
    help.append("\tVault logout:> vault-logout")
    if config.ansible_repo_path:
        help.append("\tcd to Ansible dir:> ans")
        help.append("\tcd to dir in Ansible:> cd $ans/common_roles")
    return '\n'.join(help)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config",
        required=True,
    )
    parser.add_argument(
        "-w", "--workdir",
        help="Workdir with binaries and configs (default: ~/.admin-toolbox)",
        required=True,
    )
    parser.add_argument(
        "-n", "--toolbox-name",
        help="Toolbox name",
        required=True,
    )
    parser.add_argument(
        "-i", "--info",
        action='store_true',
        default=False,
    )
    parser.add_argument(
        "--debug",
        action='store_true',
        help="debug log",
        default=False,
    )
    args = parser.parse_args()
    run(args)

