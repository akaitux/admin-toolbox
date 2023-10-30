package run

import (
	"admin-toolbox/cmd/cli"
	"context"
	"fmt"
	"os"
    "io"
	"strings"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/mount"
	"github.com/docker/docker/api/types"
	"github.com/sirupsen/logrus"
)


func pullImage(ctx context.Context, cli *cli.Cli) error {
	logrus.Info("Pulling image...")
	_, err := cli.Client.ImagePull(
        ctx,
		cli.Config.Image,
		types.ImagePullOptions{},
	)
	if err != nil {
		return err
	}

	return nil
	// TODO fixme this is super verbose...
	// if Verbose {
	// 	io.Copy(os.Stdout, r)
	// } else {
	// 	io.Copy(ioutil.Discard, r)
	// }
}



func containerCreate(ctx context.Context, cli *cli.Cli) (container.CreateResponse, error) {
	nilReturn := container.CreateResponse{}

	if cli.Config.Image == "" {
		return nilReturn, fmt.Errorf("'image' is empty")
	}

	cont, err := containerCreateNoPullFallback(cli)
	if err != nil {
		if !strings.Contains(err.Error(), " No such image") {
			return nilReturn, err
		}
        reader, err := cli.Client.ImagePull(
            ctx,
            cli.Config.Image,
            types.ImagePullOptions{},
        )
        buf := new(strings.Builder)
        io.Copy(buf, reader)
        logrus.Debugf("%s", buf)
		if err != nil {
			return nilReturn, err
		}
		return containerCreateNoPullFallback(cli)
	}
	return cont, err
}

func containerCreateNoPullFallback(cli *cli.Cli) (container.CreateResponse, error) {
	nilReturn := container.CreateResponse{}

	usr := cli.CurrentUser

	labels := make(map[string]string)
	labels["admin_toolbox"] = "true"
	labels["for_uid"] = usr.Uid

	currentPwd, err := os.Getwd()
	if err != nil {
		return nilReturn, err
	}

	pwd := usr.HomeDir
	if strings.HasPrefix(currentPwd, usr.HomeDir) {
		pwd = currentPwd
	}

	ContainerConfig := &container.Config{
		User:         fmt.Sprintf("%s:%s", usr.Uid, usr.Gid),
		Image:        cli.Config.Image,
		AttachStderr: true,
		AttachStdin:  true,
		Tty:          true,
		AttachStdout: true,
		OpenStdin:    true,
		Labels:       labels,
		WorkingDir:   pwd,
	}

	if len(cli.Config.UserConfig.Entrypoint) != 0 {
		ContainerConfig.Entrypoint = cli.Config.UserConfig.Entrypoint
	}

	if len(cli.Config.UserConfig.Cmd) != 0 {
		ContainerConfig.Cmd = cli.Config.UserConfig.Cmd
	}

	if len(cli.Config.UserConfig.Env) != 0 {
		ContainerConfig.Env = append(ContainerConfig.Env, cli.Config.UserConfig.Env...)
	}
	ContainerConfig.Env = append(ContainerConfig.Env, os.Environ()...)

	var emptyMountsSliceEntry []mount.Mount

	HostConfig := &container.HostConfig{
		Mounts:     emptyMountsSliceEntry,
		AutoRemove: true,
	}

	if err := setupMounts(cli, HostConfig); err != nil {
		return nilReturn, err
	}

	return cli.Client.ContainerCreate(
		context.Background(),
		ContainerConfig,
		HostConfig,
		nil,
		nil,
		CONTAINER_NAME,
	)
}

