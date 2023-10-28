package cmd

import (
    "os"
    "io"
    "bufio"
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


func Run() {
    cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
    if err != nil {
        log.Errorf("Unable to create docker client: %s", err)
        os.Exit(1)
    }

    cont, err := containerCreate(cli)
    if err != nil {
        log.Errorf("Create container error: %s", err)
        exit(1)
    }
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

		// Wrapper around Stdin for the container, to detect Ctrl+C (as we are in raw mode)
		go func() {
			consoleReader := bufio.NewReaderSize(os.Stdin, 1)
			for {
				input, _ := consoleReader.ReadByte()
				// Ctrl-C = 3
				if input == 3 {
					log.Debug("Detected Ctrl+C, so telling docker to remove the container: " + cont.ID)
					// cli.ContainerRemove( context.Background(), cont.ID, types.ContainerRemoveOptions{
					// 	Force: true,
					// } )
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

	ContainerConfig := &container.Config{
        User: fmt.Sprintf("%s:%s", usr.Uid, usr.Gid),
		Image: Config.Image,
		AttachStderr:true,
		AttachStdin: true,
		Tty:		 true,
		AttachStdout:true,
		OpenStdin:   true,
		Labels: labels,
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

	var emptyMountsSliceEntry []mount.Mount

	HostConfig := &container.HostConfig{
		Mounts: emptyMountsSliceEntry,
		AutoRemove: true,
	}

    // Check the home dir exists before mounting it
    _, err = os.Stat(usr.HomeDir)
    if os.IsNotExist(err) {
        fmt.Println("Homedir does not exist.")
        exit(1)
    }
    HostConfig.Mounts = append(
        HostConfig.Mounts,
        mount.Mount{
            Type:   mount.TypeBind,
            Source: usr.HomeDir,
            Target: usr.HomeDir,
        },
    )

	// for i := 0; i < len(fVolume); i++ {
	// 	splits := strings.Split(fVolume[i], ":")
	// 	localPath, containerPath := splits[0], splits[1]
	// 	HostConfig.Mounts = append(
	// 		HostConfig.Mounts,
	// 		mount.Mount{
	// 			Type:   mount.TypeBind,
	// 			Source: localPath,
	// 			Target: containerPath,
	// 		},
	// 	)
	// }
	// ContainerConfig.Env = fEnv

	return cli.ContainerCreate(
		context.Background(),
		ContainerConfig,
		HostConfig,
		nil,
		nil,
		"",
		);
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
