export SHELL:=/bin/bash
export SHELLOPTS:=$(if $(SHELLOPTS),$(SHELLOPTS):)pipefail:errexit
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.ONESHELL:
.PHONY: run-suid
build:
	go build -ldflags="-X 'main.DefaultConfDir=${ROOT_DIR}/_locals/defaults'" ${ROOT_DIR}/cmd/admin_toolbox/main.go
	mv -f main ${ROOT_DIR}/_locals/main
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
	${ROOT_DIR}/_locals/main -p default.yaml -c ${ROOT_DIR}/_locals/user_config.yaml -d run
