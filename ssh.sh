_ssh()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts=$($ans/inventory/zabbix.py --list | jq -r ".group_all.hosts[]")

    COMPREPLY=( $(compgen -W "$opts" -- ${cur}) )
    return 0
}
complete -F _ssh ssh

zstyle ':completion:*:(ssh|scp|sftp):*' hosts $(./inventory/zabbix.py --list | jq -r ".group_all.hosts[]" | awk '{s = s $1 " "} END {print s}')
