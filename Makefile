export SHELL:=/bin/bash
export SHELLOPTS:=$(if $(SHELLOPTS),$(SHELLOPTS):)pipefail:errexit
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.ONESHELL:
.PHONY: run-suid
run-suid:
	function teardown  {
		rm -f ${ROOT_DIR}/main
	}
	trap teardown EXIT
	go build -ldflags="-X 'main.DefaultConfDir=${ROOT_DIR}'" ${ROOT_DIR}/cmd/admin_toolbox/main.go
	chmod +x ${ROOT_DIR}/main
	sudo chown root:root ${ROOT_DIR}/main
	sudo chmod u+s ${ROOT_DIR}/main
	${ROOT_DIR}/main -c ${ROOT_DIR}/user_config.yaml -d run
