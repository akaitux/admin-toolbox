package workdir

import (
	"fmt"
	"github.com/sirupsen/logrus"
	"os"
	"os/user"
	"strconv"
)

type Workdir struct {
	Basepath   string
	Fullpath   string
	configName string
	User       *user.User
}

func NewWorkdir(configName string, user *user.User) Workdir {
	workdir := Workdir{configName: configName}
	workdir.User = user
	workdir.Basepath = workdir.User.HomeDir + "/.cache/admin-toolbox/"
	workdir.Fullpath = workdir.Basepath + configName
	return workdir
}

func (workdir *Workdir) MakeWorkdir() error {
	logrus.Debugf("Workdir is %s", workdir.Fullpath)
	err := os.MkdirAll(workdir.Fullpath, os.FileMode(0700))
	if err != nil {
		return fmt.Errorf("Error while creating workidr: %s", err)
	}
	uid, _ := strconv.Atoi(workdir.User.Uid)
	gid, _ := strconv.Atoi(workdir.User.Gid)
	err = os.Chown(workdir.Basepath, uid, gid)
	if err != nil {
		return fmt.Errorf("Error while chown workidr: %s", err)
	}
	err = os.Chown(workdir.Fullpath, uid, gid)
	if err != nil {
		return fmt.Errorf("Error while chown workidr: %s", err)
	}

	return nil
}

func (workdir *Workdir) Cleanup() error {
	return os.RemoveAll(workdir.Fullpath)
}
