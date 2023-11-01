# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

if [ "${BASH_SOURCE-}" = "$0" ]; then
    echo "You must source this script: \$ source $0" >&2
    exit 33
fi

ssh_ansible_autocomplete () {
    SSH_CONFIG="<SSH_CONFIG>"
    hosts=""
    if [[ -r ~/.ssh/config ]]; then
        hosts=($hosts $(awk 'match($0, /^Host \s*([^*]\w+)/, a) {s = s a[1] " "} END {print s}' ~/.ssh/config))
    fi
    if [[ -r $SSH_CONFIG ]]; then
        hosts=($hosts $(awk 'match($0, /^Host \s*([^*]\w+)/, a) {s = s a[1] " "} END {print s}' $SSH_CONFIG))
    fi
    if [[ -r ~/.ssh/known_hosts ]]; then
        hosts=($hosts $(awk 'match($0, /^([^|][a-z.0-9]+) /, a) {s = s a[0] " "} END {print s}' ~/.ssh/known_hosts))
    fi
    hosts=($hosts $(get_hosts_from_ansible))
    current_shell=$(ps -o comm= -p $$)
    if [ "$current_shell" = "zsh" ]; then
        _ssh_autocomplete_zsh "${hosts}"
    fi
    if [ "$current_shell" = "bash" ]; then
        _ssh_autocomplete_bash "${hosts[*]}"
    fi

}

_ssh_autocomplete_bash() {
    _hosts="$1"
    _ssh() {
        local cur prev opts
        COMPREPLY=()
        cur="${COMP_WORDS[COMP_CWORD]}"
        prev="${COMP_WORDS[COMP_CWORD-1]}"
        opts="$_hosts"

        COMPREPLY=( $(compgen -W "$opts" -- ${cur}) )
        return 0
    }
    complete -F _ssh ssh
}


get_hosts_from_ansible () {
    ansible all --list-hosts | tail -n +2 | awk '{s = s $1 " "} END {print s}'
}

_ssh_autocomplete_zsh () {
    zstyle ':completion:*:(ssh|scp|sftp):*' hosts $(print "$1")
}

_ssh_autocomplete_zsh_deactivate () {
    if [ "$current_shell" = "zsh" ]; then
        zstyle ':completion:*:(ssh|scp|sftp):*' hosts
    fi
}

_ssh_autocomplete_bash_deactivate () {
    if [ "$current_shell" = "bash" ]; then
        complete -r ssh
    fi
}

run_ssh_agent () {
    local SSH_AGENT_PID_PATH="<SSH_AGENT_PID_PATH>"
    local SSH_AGENT_CMD_RUN="<SSH_AGENT_CMD_RUN>"
    local SSH_AGENT_SOCK="<SSH_AGENT_SOCK>"
    local SSH_LOAD_KEYS_FROM_HOST="<SSH_LOAD_KEYS_FROM_HOST>"
    if [ -f "$SSH_AGENT_PID_PATH" ]; then
        pid=$(cat "$SSH_AGENT_PID_PATH")
        echo $pid
        if ps -p $pid > /dev/null; then
            echo "SSH: ssh agent already running"
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
    ps aux | grep "$SSH_AGENT_CMD_RUN" | grep -v grep | head -n -1 | awk '{print $2}' | xargs -I {} kill -9 {}
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

activate_vault () {
    _OLD_VAULT_ADDR="$VAULT_ADDR"
    VAULT_ADDR="<VAULT_ADDR>"
    local VAULT_IS_LOAD_ENV_VARS="<VAULT_IS_LOAD_ENV_VARS>"
    VAULT_LOGIN_METHOD="<VAULT_LOGIN_METHOD>"

    _OLD_VAULT_TOKEN="$VAULT_TOKEN"
    VAULT_TOKEN=""
    if [ -f "$WORKDIR_ROOT/vault_token" ]; then
        VAULT_TOKEN="$(cat $WORKDIR_ROOT/vault_token)"
    fi

    export VAULT_ADDR
    export VAULT_TOKEN
    export VAULT_LOGIN_METHOD

    vault_login='
    f(){
        VAULT_TOKEN=$(vault login -method=$VAULT_LOGIN_METHOD -token-only username=$1)
        echo -n "$VAULT_TOKEN" > $WORKDIR_ROOT/vault_token;
        export VAULT_TOKEN
        unset -f f
    };
    f'
    alias vault-login="$vault_login"

    alias vault-logout='rm -f <WORKDIR_ROOT>/vault_token; unset VAULT_TOKEN'

    if [ "$VAULT_IS_LOAD_ENV_VARS" ]; then
        is_loggedin=$(vault token lookup >/dev/null 2>&1 ; echo $?)
        if [ "$is_loggedin" != "0" ]; then
            echo "Login into vault"
            printf "Enter vault username: "
            read _vault_user
            eval $vault_login $_vault_user
        fi
    <VAULT_LOAD_ENV_VARS>
    fi

}

activate_ssh () {
    _OLD_SSH_ALIAS=$(alias ssh 2>/dev/null)
    local SSH_ENABLED="<SSH_ENABLED>"
    local SSH_ENABLE_AUTOCOMPLETE_FROM_ANSIBLE="<SSH_ENABLE_AUTOCOMPLETE_FROM_ANSIBLE>"

    if [ "$SSH_ENABLED" ]; then
        alias <SSH_ALIAS>
    fi
    run_ssh_agent

    if [ "$SSH_ENABLE_AUTOCOMPLETE_FROM_ANSIBLE" ]; then
        ssh_ansible_autocomplete
    fi
}

activate_gcloud () {
    local GCLOUD_ENABLED="<GCLOUD_ENABLED>"
    if [ -z "$GCLOUD_ENABLED"]; then
        return
    fi

    _OLD_CLOUDSDK_CONFIG="$CLOUDSDK_CONFIG"

    CLOUDSDK_CONFIG="<GCLOUD_CFG_PATH>"
    export CLOUDSDK_CONFIG

    _OLD_GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_APPLICATION_CREDENTIALS"
    GOOGLE_APPLICATION_CREDENTIALS="$CLOUDSDK_CONFIG/application_default_credentials.json"
    export GOOGLE_APPLICATION_CREDENTIALS
}

# unset irrelevant variables
deactivate nondestructive

activate_vault
activate_ssh


