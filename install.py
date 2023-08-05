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
from installers.activate import Activate
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
from installers.ssh import SSH


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

    installers = [
        PythonVenv(),
        Vault(),
        Ansible(),
        Terraform(),
        Terragrunt(),
        Gcloud(),
        Kubectl(),
        K9S(),
        Gron(),
        Helm(),
        ArgoCD(),
        SSH(),
    ]

    activate_replaces = {}
    activate = Activate()

    try:
        for installer in installers:
            activate_replaces.update(installer.make_activate_replaces())
        activate.replace(activate_replaces)
        if activate.is_valid():
            activate.write_template()
        else:
            logger.error("Internal error in activate.sh template")
            sys.exit(1)

        for installer in installers:
            if installer.enabled:
                logger.info("Install {}".format(installer.__class__.__name__))
                installer.install()
            else:
                logger.info("Skip {}".format(installer.__class__.__name__))
            print()
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
    activate = Activate()
    ansible = Ansible()
    gcloud = Gcloud()
    help.append("To start working with the env: \n\tsource {}".format(activate.install_path))
    help.append("To end working with the env: \n\tdeactivate")
    help.append("Add alias to .<shell>rc: \n\t alias [alias]=\"source {}\"".format(activate.install_path))
    help.append("\nToolbox dir: {}".format(config.workdir.root))
    help.append("Ansible: {}".format(ansible.repo))
    if gcloud.version and gcloud.url:
        help.append("\nGoogle:\n\tLogin to gcloud with: gcloud auth login --no-launch-browser")
        help.append("\tToestaan == accept")
        help.append("\tUse browser with proxy (waterfox?)")
        help.append("\tExample for get kubectl creds:>")
        help.append("\t  gcloud container clusters <cluster> --region <region> --project <project>")
    help.append("\nCLI:")
    help.append("\tVault login:> vault-login <username>")
    help.append("\tVault logout:> vault-logout")
    if ansible.repo:
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

