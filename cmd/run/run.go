package run

import (
	"admin-toolbox/cmd/cli"
	"admin-toolbox/streams"
	"context"
	"fmt"
	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/mount"
	"github.com/docker/docker/client"
	"github.com/moby/term"
	"github.com/sirupsen/logrus"
	"io"
	"os"
	"strings"
	"time"
)

var CONTAINER_NAME string
var OPTIONS runOptions

func run(cli *cli.Cli, options runOptions) error {
	CONTAINER_NAME = createContainerName(cli)
	OPTIONS = options

	ctx, cancelFun := context.WithCancel(context.Background())
	defer cancelFun()

	var errCh chan error

	_, stderr := cli.Out(), cli.Err()

	cont, err := containerCreate(ctx, cli)
	if err != nil {
		return fmt.Errorf("Create container error: %s", err)
	}

	closeFn, err := containerAttach(ctx, cli, &cont, &errCh)
	if err != nil {
		return err
	}
	defer closeFn()

	statusChan := waitExitOrRemoved(ctx, cli.Client, cont.ID, true)

	// start the container
	if err := cli.Client.ContainerStart(ctx, cont.ID, types.ContainerStartOptions{}); err != nil {
		// If we have hijackedIOStreamer, we should notify
		// hijackedIOStreamer we are going to exit and wait
		// to avoid the terminal are not restored.
		cancelFun()
		<-errCh

		reportError(stderr, "run", err.Error(), false)
		// wait container to be removed
		<-statusChan
		return runStartContainerErr(err)
	}

	if err := MonitorTtySize(ctx, cli, cont.ID, false); err != nil {
		_, _ = fmt.Fprintln(stderr, "Error monitoring TTY size:", err)
	}

	if errCh != nil {
		if err := <-errCh; err != nil {
			if _, ok := err.(term.EscapeError); ok {
				// The user entered the detach escape sequence.
				return nil
			}

			logrus.Debugf("Error hijack: %s", err)
			return err
		}
	}

	status := <-statusChan
	if status != 0 {
		return fmt.Errorf("Exit, status %d", status)
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
			return fmt.Errorf("Home volume is not valid %s: %s", rawVolume, err)
		}
		if err := validateHomeMount(containerPath); err != nil {
			return fmt.Errorf("Home volume is not valid '%s': %s", rawVolume, err)
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

func containerAttach(
	ctx context.Context,
	cli *cli.Cli,
	cont *container.CreateResponse,
	errCh *chan error,
) (func(), error) {

	resp, errAttach := cli.Client.ContainerAttach(ctx, cont.ID, types.ContainerAttachOptions{
		Stderr: true,
		Stdout: true,
		Stdin:  true,
		Stream: true,
	})

	if errAttach != nil {
		return nil, errAttach
	}

	var (
		out, cerr io.Writer
		in        io.ReadCloser
	)
	in = cli.In()
	out = cli.Out()
	cerr = cli.Err()

	ch := make(chan error, 1)
	*errCh = ch

	go func() {
		ch <- func() error {
			streamer := streams.HijackedIOStreamer{
				Streams:      cli,
				InputStream:  in,
				OutputStream: out,
				ErrorStream:  cerr,
				Resp:         resp,
				Tty:          true,
				DetachKeys:   "ctrl-e,e",
			}

			if errHijack := streamer.Stream(ctx); errHijack != nil {
				return errHijack
			}
			return errAttach
		}()
	}()
	return resp.Close, nil
}

func execInContainer(cli *client.Client, cont *container.CreateResponse, cmd []string) error {

	// Custom entrypoint after start container
	execConfig := types.ExecConfig{
		AttachStderr: true,
		AttachStdout: true,
		Cmd:          cmd,
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
