package run

import(
    "time"
    "context"
    "fmt"
    "strings"
    "os"
    "io"
    "bufio"
    "admin-toolbox/cmd/cli"
    "github.com/sirupsen/logrus"
    "github.com/docker/docker/api/types"
    "github.com/docker/docker/api/types/container"
    "github.com/docker/docker/api/types/mount"
    "github.com/docker/docker/client"
    "golang.org/x/crypto/ssh/terminal"

)


var CONTAINER_NAME string


func run(cli *cli.Cli, options runOptions) error {
    CONTAINER_NAME = createContainerName(cli)

    cont, err := containerCreate(cli)
    if err != nil {
        return fmt.Errorf("Create container error: %s", err)
    }

    if err := containerAttach(cli.Client, &cont); err != nil {
        return err
    }
    return nil
}


func createContainerName(cli *cli.Cli) string {

    t := time.Now()
    return fmt.Sprintf(
        "admbox-%s-%s-%d%d%d-%d%d%d",
        cli.CurrentUser.Username,
        cli.Config.Name,
        t.Hour(), t.Minute(), t.Second(), t.Day(), t.Month(), t.Year(),
    )
}


func containerCreate(cli *cli.Cli) (container.CreateResponse, error) {
    nilReturn := container.CreateResponse{}

    if cli.Config.Image == "" {
        return nilReturn, fmt.Errorf("'image' is empty")
    }

    cont, err := containerCreateNoPullFallback(cli)
    if err != nil {
        if !strings.Contains(err.Error()," No such image") {
            return nilReturn, err
        }
        logrus.Info("Pull image ...");
        err = pullImage(cli);
        if err != nil {
            return nilReturn, err
        }
        return containerCreateNoPullFallback(cli)
    }
	return cont, err;
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
        User: fmt.Sprintf("%s:%s", usr.Uid, usr.Gid),
		Image: cli.Config.Image,
		AttachStderr:true,
		AttachStdin: true,
		Tty:		 true,
		AttachStdout:true,
		OpenStdin:   true,
		Labels: labels,
        WorkingDir: pwd,
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
		Mounts: emptyMountsSliceEntry,
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
		);
}

func setupMounts(cli *cli.Cli, hostConfig *container.HostConfig) error {
    // Check the home dir exists before mounting it
    _, err := os.Stat(cli.CurrentUser.HomeDir)
    if os.IsNotExist(err) {
        return fmt.Errorf("Homedir does not exist.")
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
		hostConfig.Mounts = append(
			hostConfig.Mounts,
			mount.Mount{
				Type:   mount.TypeBind,
				Source: localPath,
				Target: containerPath,
			},
		)
	}

    for _, rawVolume := range cli.Config.UserConfig.HomeVolumes {
		splits := strings.Split(rawVolume, ":")
		localPath, containerPath := splits[0], splits[1]
        if err := validateHomeMount(localPath); err != nil {
            return fmt.Errorf("Home volume is not valid %s: %s",rawVolume, err)
        }
        if err := validateHomeMount(containerPath); err != nil {
            return fmt.Errorf("Home volume is not valid '%s': %s",rawVolume, err)
        }
        localPath = fmt.Sprintf("%s/%s", cli.CurrentUser.HomeDir, localPath)
        containerPath = fmt.Sprintf("%s/%s", cli.CurrentUser.HomeDir, containerPath)
		hostConfig.Mounts = append(
			hostConfig.Mounts,
			mount.Mount{
				Type:   mount.TypeBind,
				Source: localPath,
				Target: containerPath,
			},
		)
    }

    return nil
}

func validateHomeMount(mount string) error {
    // direction - host/container
    if strings.Contains(mount, "..") {
        return fmt.Errorf("'..' is denied")
    }
    if strings.HasPrefix(mount, "/") {
        return fmt.Errorf("'/' in begin of volume is denied ")
    }
    if strings.HasPrefix(mount, "./") {
        return fmt.Errorf("'./' in begin of volume is denied ")
    }
    return nil
}

func pullImage(cli *cli.Cli) error {
	logrus.Info("Pulling image");
	_, err := cli.Client.ImagePull(
		context.Background(),
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

func containerAttach(cli *client.Client, cont *container.CreateResponse) error {
    waiter, err := cli.ContainerAttach(context.Background(), cont.ID, types.ContainerAttachOptions{
		Stderr:	   true,
		Stdout:	   true,
		Stdin:		true,
		Stream:	   true,
	})
    if err != nil {
        return fmt.Errorf("Error while boostrap contaner: %s", err)
    }


    // waiter.Conn.Write([]byte("source $HOME/.startup.sh;clear -x"))
    // waiter.Conn.Write([]byte{0x0a}) // \n


	// When TTY is ON, just copy stdout
	// See: https://github.com/docker/cli/blob/70a00157f161b109be77cd4f30ce0662bfe8cc32/cli/command/container/hijack.go#L121-L130
	go io.Copy(os.Stdout, waiter.Reader)

    err = cli.ContainerStart(context.Background(), cont.ID, types.ContainerStartOptions{})
    if err != nil {
        return fmt.Errorf("Error Starting container (%s): %s", cont.ID, err)
    }

	fd := int(os.Stdin.Fd())
	var oldState *terminal.State
	if terminal.IsTerminal(fd) {
		oldState, err = terminal.MakeRaw(fd)
		if err != nil {
			return fmt.Errorf("Terminal: make raw ERROR")
		}

        go func () {
            for {
                width, height, err := terminal.GetSize(0)
                if err == nil {
                    cli.ContainerResize(context.Background(), cont.ID, types.ResizeOptions{
                        Height: uint(height),
                        Width: uint(width),
                    })
                }
                time.Sleep(500 * time.Millisecond)
            }
        }()

		go func() {
			consoleReader := bufio.NewReaderSize(os.Stdin, 1)
            exitCounter := 0
			for {
				input, _ := consoleReader.ReadByte()
				// Ctrl-D = 4
				if input == 4 {
                    if exitCounter == 0 {
                        waiter.Conn.Write([]byte{0x0a})
                        waiter.Conn.Write([]byte("echo 'Press Ctrl-D again for exit'"))
                        waiter.Conn.Write([]byte{0x0a})
				        input, _ = consoleReader.ReadByte()
                        if input == 4 {
                            cli.ContainerRemove( context.Background(), cont.ID, types.ContainerRemoveOptions{
                                Force: true,
                            } )
                        }
                    }
				}
				waiter.Conn.Write([]byte{input})
		}
		}()
	}

	statusCh, errCh := cli.ContainerWait(context.Background(), cont.ID, container.WaitConditionNotRunning)
	select {
	case err := <-errCh:
		if err != nil {
			panic(err)
		}
	case <-statusCh:
	}

	logrus.Debug("Restoring terminal");
	if terminal.IsTerminal(fd) {
		terminal.Restore(fd, oldState)
	}
	fmt.Println("");

	logrus.Debug("Ensuring Container Removal: " + cont.ID);
	cli.ContainerRemove( context.Background(), cont.ID, types.ContainerRemoveOptions{
		Force: true,
	} )
    return nil
}

func execInContainer(cli *client.Client, cont *container.CreateResponse, cmd []string) error {

    // Custom entrypoint after start container
    execConfig := types.ExecConfig {
        AttachStderr: true,
        AttachStdout: true,
        Cmd: cmd,
    }
    execResponse, err := cli.ContainerExecCreate(context.Background(), cont.ID, execConfig)
    if err != nil {
        logrus.Debugf("ContainerExecCreateResponse: %v", execResponse)
        return err
    }
    execAttachConfig := types.ExecStartCheck{
        Tty: false,
    }
    resp, err := cli.ContainerExecAttach(context.Background(), execResponse.ID, execAttachConfig)
    if err != nil {
        logrus.Debugf("ContainerExecAttachResponse: %v", resp)
        return err
    }
    return nil
}
