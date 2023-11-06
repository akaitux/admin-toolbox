export SHELL:=/bin/bash
export SHELLOPTS:=$(if $(SHELLOPTS),$(SHELLOPTS):)pipefail:errexit
:q
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DEFAULT_CONFDIR:="${ROOT_DIR}/config"
LOCALS_CONFDIR:="${ROOT_DIR}/_locals"

.ONESHELL:
.PHONY: run-suid
build:
	mkdir -p "${LOCALS_CONFDIR}"
	if [ -d "${LOCALS_CONFDIR}/defaults" ]; then
		CONFDIR="${LOCALS_CONFDIR}/defaults";
	else
		CONFDIR="${DEFAULT_CONFDIR}/defaults"
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
	if [ -d "${LOCALS_CONFDIR}/defaults" ]; then
		${ROOT_DIR}/_locals/main -p default.yaml -c ${ROOT_DIR}/_locals/user_config.yaml -d run
	else
		${ROOT_DIR}/_locals/main -p default.yaml -c ${ROOT_DIR}/config/user_config.yaml -d run

	fi
