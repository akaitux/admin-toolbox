package cmd

import (
    "os"
    "io"
    "bufio"
    "time"
    "os/user"
    "fmt"
    "strings"
    "context"
    log "github.com/sirupsen/logrus"
    "github.com/docker/docker/api/types"
    "github.com/docker/docker/api/types/container"
    "github.com/docker/docker/api/types/mount"
    "github.com/docker/docker/client"
    "golang.org/x/crypto/ssh/terminal"
)


var USER *user.User
var CONTAINER_NAME string

func Run() {
    cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
    if err != nil {
        log.Errorf("Unable to create docker client: %s", err)
        os.Exit(1)
    }

    USER, err = user.Current()
    if err != nil {
        log.Errorf("Error while get current user: %s", err)
        exit(1)
    }

    CONTAINER_NAME = createContainerName()

    cont, err := containerCreate(cli)
    if err != nil {
        log.Errorf("Create container error: %s", err)
        exit(1)
    }

    if err := containerAttach(cli, &cont); err != nil {
        log.Error(err)
        exit(1)
    }
}

func createContainerName() string {

    t := time.Now()
    return fmt.Sprintf(
        "admin-toolbox-%s-%s-%d%d%d%d%d",
        USER.Username,
        Config.Name,
        t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second(),
    )
}


func containerCreate(cli *client.Client) (container.CreateResponse, error) {
    nilReturn := container.CreateResponse{}

    if Config.Image == "" {
        return nilReturn, fmt.Errorf("'image' is empty")
    }

    cont, err := containerCreateNoPullFallback(cli)
    if err != nil {
        if !strings.Contains(err.Error()," No such image") {
            return nilReturn, err
        }
        log.Info("Pull image ...");
        err = pullImage(cli);
        if err != nil {
            return nilReturn, err
        }
        return containerCreateNoPullFallback(cli)
    }
	return cont, err;
}

func containerCreateNoPullFallback(cli *client.Client) (container.CreateResponse, error) {
    nilReturn := container.CreateResponse{}
    usr, err := user.Current()
    if err != nil {
        return nilReturn, err
    }

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
		Image: Config.Image,
		AttachStderr:true,
		AttachStdin: true,
		Tty:		 true,
		AttachStdout:true,
		OpenStdin:   true,
		Labels: labels,
        WorkingDir: pwd,
	}

    if len(Config.userConfig.Entrypoint) != 0 {
        ContainerConfig.Entrypoint = Config.userConfig.Entrypoint
    }

    if len(Config.userConfig.Cmd) != 0 {
        ContainerConfig.Cmd = Config.userConfig.Cmd
    }

    if len(Config.userConfig.Env) != 0 {
        ContainerConfig.Env = append(ContainerConfig.Env, Config.userConfig.Env...)
    }
    ContainerConfig.Env = append(ContainerConfig.Env, os.Environ()...)


	var emptyMountsSliceEntry []mount.Mount

	HostConfig := &container.HostConfig{
		Mounts: emptyMountsSliceEntry,
		AutoRemove: true,
	}

    if err := setupMounts(HostConfig); err != nil {
        return nilReturn, err
    }

	return cli.ContainerCreate(
		context.Background(),
		ContainerConfig,
		HostConfig,
		nil,
		nil,
		CONTAINER_NAME,
		);
}

func setupMounts(hostConfig *container.HostConfig) error {
    // Check the home dir exists before mounting it
    _, err := os.Stat(USER.HomeDir)
    if os.IsNotExist(err) {
        return fmt.Errorf("Homedir does not exist.")
    }
    hostConfig.Mounts = append(
        hostConfig.Mounts,
        mount.Mount{
            Type:   mount.TypeBind,
            Source: USER.HomeDir,
            Target: USER.HomeDir,
        },
    )

    for _, rawVolume := range Config.AdditionalVolumes {
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

    for _, rawVolume := range Config.userConfig.HomeVolumes {
		splits := strings.Split(rawVolume, ":")
		localPath, containerPath := splits[0], splits[1]
        if err := validateHomeMount(localPath); err != nil {
            return fmt.Errorf("Home volume is not valid %s: %s",rawVolume, err)
        }
        if err := validateHomeMount(containerPath); err != nil {
            return fmt.Errorf("Home volume is not valid '%s': %s",rawVolume, err)
        }
        localPath = fmt.Sprintf("%s/%s", USER.HomeDir, localPath)
        containerPath = fmt.Sprintf("%s/%s", USER.HomeDir, containerPath)
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

func pullImage(cli *client.Client) error {
	log.Info("Pulling image");
	_, err := cli.ImagePull(
		context.Background(),
		Config.Image,
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

	// When TTY is ON, just copy stdout
	// See: https://github.com/docker/cli/blob/70a00157f161b109be77cd4f30ce0662bfe8cc32/cli/command/container/hijack.go#L121-L130
	go io.Copy(os.Stdout, waiter.Reader)

	err = cli.ContainerStart(context.Background(), cont.ID, types.ContainerStartOptions{})
	if err != nil {
        log.Errorf("Error Starting container (%s): %s", cont.ID, err)
        exit(1)
	}

	fd := int(os.Stdin.Fd())
	var oldState *terminal.State
	if terminal.IsTerminal(fd) {
		oldState, err = terminal.MakeRaw(fd)
		if err != nil {
			log.Error("Terminal: make raw ERROR")
            exit(1)
		}

		go func() {
			consoleReader := bufio.NewReaderSize(os.Stdin, 1)
			for {
				input, _ := consoleReader.ReadByte()
				// Ctrl-D = 4
				if input == 4 {
					log.Debug("Detected Ctrl+D")
					cli.ContainerRemove( context.Background(), cont.ID, types.ContainerRemoveOptions{
						Force: true,
					} )
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

	log.Debug("Restoring terminal");
	if terminal.IsTerminal(fd) {
		terminal.Restore(fd, oldState)
	}
	fmt.Println("");

	// log.Debug("Ensuring Container Removal: " + cont.ID);
	// cli.ContainerRemove( context.Background(), cont.ID, types.ContainerRemoveOptions{
	// 	Force: true,
	// } )
    return nil
}
