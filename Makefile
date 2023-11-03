export SHELL:=/bin/bash
export SHELLOPTS:=$(if $(SHELLOPTS),$(SHELLOPTS):)pipefail:errexit
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DEFAULT_CONFDIR:="${ROOT_DIR}/config/defaults"

.ONESHELL:
.PHONY: run-suid
build:
	mkdir -p "${ROOT_DIR}/_locals"
	if [ -d "${ROOT_DIR}/_locals/defaults" ]; then
		CONFDIR="${ROOT_DIR}/_locals/defaults";
	else
		CONFDIR="$DEFAULT_CONFDIR"
	fi
	cd src;
	go build -ldflags="-X 'main.DefaultConfDir=$${CONFDIR}'" ${ROOT_DIR}/src/cmd/admin_toolbox/main.go
	mv -f ${ROOT_DIR}/src/main ${ROOT_DIR}/_locals/main
	chmod +x ${ROOT_DIR}/_locals/main


.ONESHELL:
.PHONY: run-suid
run-suid: build
	#function teardown  {
	#	rm -f ${ROOT_DIR}/main
	#}
	#trap teardown EXIT
	#go build -ldflags="-X 'main.DefaultConfDir=${ROOT_DIR}/_locals/defaults'" ${ROOT_DIR}/cmd/admin_toolbox/main.go _C ${ROOT_DIR}/_locals/main
	#chmod +x ${ROOT_DIR}/_locals/main
	sudo chown root:root ${ROOT_DIR}/_locals/main
	sudo chmod u+s ${ROOT_DIR}/_locals/main
	if [ -d "${ROOT_DIR}/_locals/defaults" ]; then
		${ROOT_DIR}/_locals/main -p default.yaml -c ${ROOT_DIR}/_locals/user_config.yaml -d run
	else
		${ROOT_DIR}/_locals/main -p default.yaml -c ${ROOT_DIR}/config/user_config.yaml -d run

	fi
