#!/bin/bash

#if [ -z "$TOOLBOX_WORKDIR" ]; then
#    echo "No 'TOOLBOX_WORKDIR', skip load source script"
#else
#    set +e
#    source /scripts/source_script.sh
#    set -e
#fi

if [[ "$SHELL" =~ .*/bash ]]; then
    exec ${SHELL} --init-file /scripts/source_script.sh
fi

if [[ "$SHELL" =~ .*/zsh ]]; then
    tmp=$(mktemp -d ${TMPDIR:-/tmp}/zsh.XXXXXXXXXX) || return
    for f in .zshenv .zprofile .zshrc .zlogin .zlogout; do
        if [ -f "$HOME/$f" ]; then
            cp "$HOME/$f" $tmp/$f
        fi
    done
    echo "source /scripts/source_script.sh" >> $tmp/.zshrc
    echo "unsetopt	ERR_EXIT" >> $tmp/.zshrc
    export ZDOTDIR=$tmp
    exec ${SHELL}
fi


exec ${SHELL:-/bin/bash}
