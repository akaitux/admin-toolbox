#!/usr/bin/env

if [ -z "$TOOLBOX_WORKDIR" ]; then
    echo "No 'TOOLBOX_WORKDIR', skip load source script"
else
    set +e
    source /scripts/source_script.sh
    set -e
fi

exec ${SHELL:-/bin/bash}

