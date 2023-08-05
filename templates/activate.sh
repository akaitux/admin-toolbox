# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

if [ "${BASH_SOURCE-}" = "$0" ]; then
    echo "You must source this script: \$ source $0" >&2
    exit 33
fi

run_ssh_agent () {
    local SSH_AGENT_PID_PATH="<SSH_AGENT_PID_PATH>"
    local SSH_AGENT_CMD_RUN="<SSH_AGENT_CMD_RUN>"
    local SSH_AGENT_SOCK="<SSH_AGENT_SOCK>"
    local SSH_LOAD_KEYS_FROM_HOST="<SSH_LOAD_KEYS_FROM_HOST>"
    if [ -f "$SSH_AGENT_PID_PATH" ]; then
        pid=$(cat "$SSH_AGENT_PID_PATH")
        echo $pid
        if ps -p $pid > /dev/null; then
            echo "SSH Bastion: ssh agent already running"
            return
        fi
    fi
    stop_ssh_agent
    out=$(eval $SSH_AGENT_CMD_RUN)
    local pid=$(echo $out | grep -oP "SSH_AGENT_PID=\K([[:digit:]]+)")
    echo $pid > $SSH_AGENT_PID_PATH
    if [ "$SSH_LOAD_KEYS_FROM_HOST" ]; then
        SSH_AUTH_SOCK=$SSH_AGENT_SOCK /usr/bin/ssh -o 'ForwardAgent yes' $SSH_LOAD_KEYS_FROM_HOST "ssh-add 2>&1 > /dev/null" >/dev/null
    fi
}

stop_ssh_agent () {
    local SSH_AGENT_CMD_RUN="<SSH_AGENT_CMD_RUN>"
    local SSH_AGENT_PID_PATH="<SSH_AGENT_PID_PATH>"
    local SSH_AGENT_SOCK="<SSH_AGENT_SOCK>"
    ps aux | grep "$SSH_AGENT_CMD_RUN" | head -n -1 | awk '{print $2}' | xargs -I {} kill -9 {}
    rm -f $SSH_AGENT_PID_PATH
    rm -f $SSH_AGENT_SOCK
}

deactivate_vault () {
    <VAULT_DEACTIVATE LOAD_ENV_VARS>
    if ! [ -z "${_OLD_VAULT_ADDR+_}" ] ; then
        VAULT_ADDR="$_OLD_VAULT_ADDR"
        export VAULT_ADDR
        unset _OLD_VAULT_ADDR
    fi
    if ! [ -z "${_OLD_VAULT_TOKEN+_}" ] ; then
        VAULT_TOKEN="$_OLD_VAULT_TOKEN"
        export VAULT_TOKEN
        unset _OLD_VAULT_TOKEN
    fi
}

deactivate_ansible() {
    if ! [ -z "${_OLD_ANSIBLE_CONFIG+_}" ] ; then
        ANSIBLE_CONFIG="$_OLD_ANSIBLE_CONFIG"
        export ANSIBLE_CONFIG
        unset _OLD_ANSIBLE_CONFIG
    fi
    unalias ans 2>/dev/null
}

deactivate_gcloud () {
    if ! [ -z "${_OLD_CLOUDSDK_CONFIG+_}" ] ; then
        CLOUDSDK_CONFIG="$_OLD_CLOUDSDK_CONFIG"
        export CLOUDSDK_CONFIG
        unset _OLD_CLOUDSDK_CONFIG
    fi
    if ! [ -z "${_OLD_GOOGLE_APPLICATION_CREDENTIALS+_}" ] ; then
        GOOGLE_APPLICATION_CREDENTIALS="$_OLD_GOOGLE_APPLICATION_CREDENTIALS"
        export GOOGLE_APPLICATION_CREDENTIALS
        unset _OLD_GOOGLE_APPLICATION_CREDENTIALS
    fi
}

deactivate_kubectl () {
    if ! [ -z "${_OLD_KUBECONFIG+_}" ] ; then
        KUBECONFIG="$_OLD_KUBECONFIG"
        export KUBECONFIG
        unset _OLD_KUBECONFIG
    fi
}

deactivate_python_venv () {
    if ! [ -z "${_OLD_VIRTUALENVWRAPPER_PYTHON+_}" ] ; then
        VIRTUALENVWRAPPER_PYTHON="$_OLD_VIRTUALENVWRAPPER_PYTHON"
        export VIRTUALENVWRAPPER_PYTHON
        unset _OLD_VIRTUALENVWRAPPER_PYTHON
    fi
}

deactivate_terra () {
    if ! [ -z "${_OLD_TERRAFORM_ALIAS:+_}" ]; then
        eval "alias $_OLD_TERRAFORM_ALIAS";
    elif [ ! "${1-}" = "nondestructive" ] ; then
        unalias terraform 2>/dev/null
    fi
    unset _OLD_TERRAFORM_ALIAS

    if ! [ -z "${_OLD_TERRAGRUNT_ALIAS:+_}" ]; then
        eval "alias $_OLD_TERRAGRUNT_ALIAS";
    elif [ ! "${1-}" = "nondestructive" ] ; then
        unalias terragrunt 2>/dev/null
    fi
    unset _OLD_TERRAGRUNT_ALIAS

}

deactivate_argocd () {
    if ! [ -z "${_OLD_ARGOCD_ALIAS:+_}" ]; then
        eval "alias $_OLD_ARGOCD_ALIAS";
    elif [ ! "${1-}" = "nondestructive" ] ; then
        unalias argocd 2>/dev/null
    fi
    unset _OLD_ARGOCD_ALIAS
}


deactivate_ssh() {
    if ! [ -z "${_OLD_SSH_ALIAS:+_}" ]; then
        eval "alias $_OLD_SSH_ALIAS";
    elif [ ! "${1-}" = "nondestructive" ] ; then
        unalias ssh 2>/dev/null
    fi
    unset _OLD_SSH_ALIAS
    stop_ssh_agent
}

deactivate_additional_aliases () {
    unalias admin-toolbox-info 2>/dev/null
}

deactivate () {
    # reset old environment variables
    # ! [ -z ${VAR+_} ] returns true if VAR is declared at all

    if ! [ -z "${_OLD_VIRTUAL_PATH:+_}" ] ; then
        PATH="$_OLD_VIRTUAL_PATH"
        export PATH
        unset _OLD_VIRTUAL_PATH
    fi

    deactivate_vault
    deactivate_ansible
    deactivate_gcloud
    deactivate_kubectl
    deactivate_python_venv
    deactivate_terra
    deactivate_argocd
    deactivate_ssh
    deactivate_additional_aliases

    if [ ! "${1-}" = "nondestructive" ] ; then
    # Self destruct!
        unset -f deactivate
    fi

    # This should detect bash and zsh, which have a hash command that must
    # be called to get it to forget past commands.  Without forgetting
    # past commands the $PATH changes we made may not be respected
    if [ -n "${BASH-}" ] || [ -n "${ZSH_VERSION-}" ] ; then
        hash -r 2>/dev/null
    fi

    if ! [ -z "${_OLD_VIRTUAL_PS1+_}" ] ; then
        PS1="$_OLD_VIRTUAL_PS1"
        export PS1
        unset _OLD_VIRTUAL_PS1
    fi

}


activate_python_venv () {
    local PYTHON_VENV_ENABLED="<PYTHON_VENV_ENABLED>"
    local PYTHON_VENV="<PYTHON_VENV>"

    if [ "$PYTHON_VENV_ENABLED" ]; then
        _OLD_PYTHON_WRAPPER="$VIRTUALENVWRAPPER_PYTHON"
        VIRTUALENVWRAPPER_PYTHON="$PYTHON_VENV/bin/python3"
        export VIRTUALENVWRAPPER_PYTHON
        PATH="$PYTHON_VENV/bin:$PATH"
    fi
}

activate_ansible () {
    ANSIBLE_CONFIG="<ANSIBLE_CONFIG>"
    ANSIBLE_PATH="<ANSIBLE_PATH>"
    local ANSIBLE_ENABLED="<ANSIBLE_ENABLED>"
    local ANSIBLE_WORKDIR="<ANSIBLE_WORKDIR>"
    local ANSIBLE_BINDIR="<ANSIBLE_BINDIR>"

    if [ "$ANSIBLE_ENABLED" ]; then
        _OLD_ANSIBLE_CONFIG="$ANSIBLE_CONFIG"
        export ANSIBLE_CONFIG

        export ANSIBLE_PATH
        ANSIBLE_PYTHON="$ANSIBLE_WORKDIR/venv/bin/python"
        export ANSIBLE_PYTHON

        PATH="<ANSIBLE_BINDIR>:$PATH"
    fi

    alias ans='cd $ANSIBLE_PATH'
    # variable for use in cd, for exam. cd $ans/some_dir
    ans='$ANSIBLE_PATH'
    export ans
}

activate_vault () {
    _OLD_VAULT_ADDR="$VAULT_ADDR"
    local VAULT_ADDR="<VAULT_ADDR>"
    local VAULT_IS_LOAD_ENV_VARS="<VAULT_IS_LOAD_ENV_VARS>"
    local VAULT_LOGIN_METHOD="<VAULT_LOGIN_METHOD>"

    _OLD_VAULT_TOKEN="$VAULT_TOKEN"
    VAULT_TOKEN=""
    if [ -f "$WORKDIR_ROOT/vault_token" ]; then
        VAULT_TOKEN="$(cat $WORKDIR_ROOT/vault_token)"
    fi

    export VAULT_ADDR
    export VAULT_TOKEN

    if [ "$VAULT_IS_LOAD_ENV_VARS" ]; then
        is_loggedin=$(vault token lookup >/dev/null 2>&1 ; echo $?)
        if [ "$is_loggedin" != "0" ]; then
            echo "Login into vault"
            printf "Enter vault username: "
            read _vault_user
            vault-login $_vault_user
        fi
    <VAULT_LOAD_ENV_VARS>
    fi

    alias vault-login='
        f(){
            VAULT_TOKEN=$(vault login -method=$VAULT_LOGIN_METHOD -token-only username=$1)
            echo -n "$VAULT_TOKEN" > $WORKDIR_ROOT/vault_token;
            export VAULT_TOKEN
            unset -f f
        };
        f'
    alias vault-logout='rm -f <WORKDIR_ROOT>/vault_token; unset VAULT_TOKEN'
}

activate_terra () {
    _OLD_TERRAFORM_ALIAS=$(alias terraform)
    _OLD_TERRAGRUNT_ALIAS=$(alias terragrunt)
    local TERRAFORM_ENABLED="<TERRAFORM_ENABLED>"
    local TERRAGRUNT_ENABLED="<TERRAGRUNT_ENABLED>"
    if [ "$TERRAFORM_ENABLED" ]; then
        alias <ALIAS_TERRAFORM>
    fi
    if [ "$TERRAGRUNT_ENABLED" ]; then
        alias <ALIAS_TERRAGRUNT>
    fi
}

activate_argocd () {
    _OLD_ARGOCD_ALIAS=$(alias argocd)
    alias <ALIAS_ARGOCD>
}

activate_ssh () {
    _OLD_SSH_ALIAS=$(alias ssh)

    if [ "<SSH_ENABLED>" ]; then
        alias <SSH_ALIAS>
    fi
    run_ssh_agent
}

activate_gcloud () {
    local GCLOUD_ENABLED="<GCLOUD_ENABLED>"
    if [ -z "$GCLOUD_ENABLED"]; then
        return
    fi

    _OLD_CLOUDSDK_CONFIG="$CLOUDSDK_CONFIG"

    local CLOUDSDK_CONFIG="<GCLOUD_CFG_PATH>"
    export CLOUDSDK_CONFIG

    _OLD_GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_APPLICATION_CREDENTIALS"
    local GOOGLE_APPLICATION_CREDENTIALS="$CLOUDSDK_CONFIG/application_default_credentials.json"
    export GOOGLE_APPLICATION_CREDENTIALS
}

activate_kubectl () {
    _OLD_KUBECONFIG="$KUBECONFIG"
    local KUBECONFIG="<KUBE_CONFIG_PATH>/config"
    export KUBECONFIG
}

activate_additional_aliases () {
    alias admin-toolbox-info='cat $WORKDIR_ROOT/.info'
}

# unset irrelevant variables
deactivate nondestructive

WORKDIR_BIN="<WORKDIR_BIN>"
WORKDIR_ROOT="<WORKDIR_ROOT>"
TOOLBOX_NAME="<TOOLBOX_NAME>"

_OLD_VIRTUAL_PATH="$PATH"
PATH="$WORKDIR_BIN:$PATH"

activate_python_venv
activate_ansible
activate_vault
activate_terra
activate_argocd
activate_ssh
activate_gcloud
activate_kubectl
activate_additional_aliases

export PATH


if [ -z "${ADMIN_TOOLBOX_DISABLE_PROMPT-}" ] ; then
    _OLD_VIRTUAL_PS1="${PS1-}"
    if [ "x" != x ] ; then
        PS1="${PS1-}"
    else
        PS1="(`basename \"$TOOLBOX_NAME\"`) ${PS1-}"
    fi
    export PS1
fi

# This should detect bash and zsh, which have a hash command that must
# be called to get it to forget past commands.  Without forgetting
# past commands the $PATH changes we made may not be respected
if [ -n "${BASH-}" ] || [ -n "${ZSH_VERSION-}" ] ; then
    hash -r 2>/dev/null
fi

