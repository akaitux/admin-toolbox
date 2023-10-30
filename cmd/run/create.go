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
        Hostname:     cli.Config.Name,
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

	//ContainerConfig.Env = append(ContainerConfig.Env, os.Environ()...)
    if cli.Config.InheritEnv {
        envBlackList := []string{"SHLVL", "SHELLOPTS"}
        envBlackList = append(envBlackList, cli.Config.InheritEnvExclude...)
        for _, env := range os.Environ() {
            split := strings.SplitN(env, "=", 2)
            if contains(envBlackList, split[0]) {
                continue
            }
            ContainerConfig.Env = append(ContainerConfig.Env, env)
        }
    }

	if len(cli.Config.UserConfig.Env) != 0 {
		ContainerConfig.Env = append(ContainerConfig.Env, cli.Config.UserConfig.Env...)
	}

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

func contains(s []string, e string) bool {
    for _, a := range s {
        if a == e {
            return true
        }
    }
    return false
}

func setupMounts(cli *cli.Cli, hostConfig *container.HostConfig) error {
	// Check the home dir exists before mounting it
	_, err := os.Stat(cli.CurrentUser.HomeDir)
	if os.IsNotExist(err) {
		return fmt.Errorf("Homedir does not exist.")
	}

    containerMountPaths := []string{}

	for _, rawVolume := range cli.Config.UserConfig.HomeVolumes {
		splits := strings.Split(rawVolume, ":")
		localPath, containerPath := splits[0], splits[1]
		if err := validateHomeMount(localPath); err != nil {
			return fmt.Errorf("Home volume is not valid %s: %s", rawVolume, err)
		}
		if err := validateHomeMount(containerPath); err != nil {
			return fmt.Errorf("Home volume is not valid '%s': %s", rawVolume, err)
		}
		localPath = fmt.Sprintf("%s/%s", cli.CurrentUser.HomeDir, localPath)
		containerPath = fmt.Sprintf("%s/%s", cli.CurrentUser.HomeDir, containerPath)
        containerMountPaths = append(containerMountPaths, containerPath)
		hostConfig.Mounts = append(
			hostConfig.Mounts,
			mount.Mount{
				Type:   mount.TypeBind,
				Source: localPath,
				Target: containerPath,
			},
		)
	}

	hostConfig.Mounts = append(
		hostConfig.Mounts,
		mount.Mount{
			Type:   mount.TypeBind,
			Source: cli.CurrentUser.HomeDir,
			Target: cli.CurrentUser.HomeDir,
		},
	)

	for _, rawVolume := range cli.Config.AdditionalVolumes {
		splits := strings.Split(rawVolume, ":")
		localPath, containerPath := splits[0], splits[1]
        if !contains(containerMountPaths, containerPath) {
            hostConfig.Mounts = append(
                hostConfig.Mounts,
                mount.Mount{
                    Type:   mount.TypeBind,
                    Source: localPath,
                    Target: containerPath,
                },
            )
        } else {
            logrus.Debugf("Duplicate mounts: %s", rawVolume)
        }

	}

	return nil
}

