# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly


# TOOLBOX_WORKDIR - path to workdir of env
# VAULT_LOGIN_METHOD
# VAULT_LOAD_VAR_<ENV_NAME> = <PATH_INTO_VAULT>:value
# GITLAB_ADDR - without protocol (for example, gitlab.domain.com)

TOOLBOX_WORKDIR=$(eval echo -e -n "$TOOLBOX_WORKDIR")
GITLAB_TOKEN_FILE="${TOOLBOX_WORKDIR}/.gitlab_token"
VAULT_TOKEN_PATH="$TOOLBOX_WORKDIR/.vault_token"

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

activate_vault () {
    vault_login='
    f(){
        VAULT_TOKEN=$(vault login -method=${VAULT_LOGIN_METHOD:-ldap} -token-only username=$1);
        exit_code="$?";
        if [ "$exit_code" != "0" ]; then
            echo ">> Error. Invalid Vault creds";
            return;
        fi;
        echo -n "$VAULT_TOKEN" > "${VAULT_TOKEN_PATH}";
        export VAULT_TOKEN;
        unset -f f;
    };
    f'
    alias vault-login="$vault_login"

    alias vault-logout='rm -f $TOOLBOX_WORKDIR/.vault_token; unset VAULT_TOKEN'

    VAULT_TOKEN=""
    if [ -f "$TOOLBOX_WORKDIR/.vault_token" ]; then
        VAULT_TOKEN="$(cat $TOOLBOX_WORKDIR/.vault_token)"
        export VAULT_TOKEN=$VAULT_TOKEN
    fi

    is_token_loaded="false"
    is_vault_load_vars="false"
    prefix="VAULT_LOAD_VAR" # delete longest match from back (everything after first _)
    while IFS='=' read -r name value ; do
        if [[ "$name" == "$prefix"* ]]; then
           is_vault_load_vars="true"
           break
        fi
    done < <(env)

    if [ "$is_vault_load_vars" != "true" ]; then
        return
    fi

    is_loggedin=$(vault token lookup >/dev/null 2>&1 ; echo $?)
    if [ "$is_loggedin" != "0" ]; then
        printf "Enter vault username: "
        read _vault_user
        eval $vault_login $_vault_user
    fi

    is_loggedin=$(vault token lookup >/dev/null 2>&1 ; echo $?)
    [ "$is_loggedin" != "0" ] && return

    while IFS='=' read -r name value ; do
        if [[ "$name" != "$prefix"* ]]; then
            continue
        fi
        name=$(echo -n $name | sed 's/"//')
        var_name=${name#"${prefix}_"}
        vault_path=$(echo -n $value | cut -d "^" -f1)
        vault_key=$(echo -n $value | cut -d "^" -f2)
        set +e
        vault_value=$( vault kv get -field="$vault_key" "$vault_path")
        if [ "$?" != "0" ]; then
            echo "Error while load data from vault: $name=$value"
            continue
        fi
        set -e
        command="$var_name=$vault_value"
        export "$command"
        export -n "$name"
    done < <(env)
}

function activate_gitlab_token {
    if [ ! -f "$GITLAB_TOKEN_FILE" ]; then
        get_new_gitlab_token
    fi
    token=$(cat $GITLAB_TOKEN_FILE)
    is_has_access=$(test_gitlab_access $token)
    if [ "$is_has_access" != "0" ]; then
        get_new_gitlab_token
        is_has_access=$(test_gitlab_access $token)
        if [ "$is_has_access" != "0" ]; then
            echo ">> Error. No access to gitlab by ssh"
        fi
    fi
    export TG_GITLAB_USER="git"
    export TG_GITLAB_PASSWORD="$(cat $GITLAB_TOKEN_FILE)"
}

function test_gitlab_access {
    #param $0 - token
    curl -s -f -L -H "PRIVATE-TOKEN: $0" https://$GITLAB_ADDR >/dev/null; echo $?
}

function get_new_gitlab_token {
    local data=$(ssh git@${GITLAB_ADDR} personal_access_token admin-toolbox-$(date +%s) api,read_api,read_repository,write_repository,read_registry,write_registry 363 || return "1")
    echo $data | grep "Token:" | awk '{print $2}' > $GITLAB_TOKEN_FILE
}

function activate_terraform {
    export TF_PLUGIN_CACHE_DIR="$TOOLBOX_WORKDIR/.terraform.d/plugin-cache"
}

#activate_ssh () {
#    _OLD_SSH_ALIAS=$(alias ssh 2>/dev/null)
#    local SSH_ENABLED="<SSH_ENABLED>"
#    local SSH_ENABLE_AUTOCOMPLETE_FROM_ANSIBLE="<SSH_ENABLE_AUTOCOMPLETE_FROM_ANSIBLE>"
#
#    if [ "$SSH_ENABLED" ]; then
#        alias <SSH_ALIAS>
#    fi
#    run_ssh_agent
#
#    if [ "$SSH_ENABLE_AUTOCOMPLETE_FROM_ANSIBLE" ]; then
#        ssh_ansible_autocomplete
#    fi
#}

# unset irrelevant variables


activate_vault
activate_terraform
if [ "$GITLAB_ADDR" ]; then
    activate_gitlab_token
fi

#activate_ssh

