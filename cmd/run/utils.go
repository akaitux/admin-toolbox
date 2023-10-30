package run

import (
	"context"
	"fmt"
	"io"
	"strconv"
	"strings"
	"syscall"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/events"
	"github.com/docker/docker/api/types/filters"
	"github.com/docker/docker/api/types/versions"
	"github.com/docker/docker/client"
	"github.com/sirupsen/logrus"
)

func waitExitOrRemoved(ctx context.Context, apiClient client.APIClient, containerID string, waitRemove bool) <-chan int {
	if len(containerID) == 0 {
		// containerID can never be empty
		panic("Internal Error: waitExitOrRemoved needs a containerID as parameter")
	}

	// Older versions used the Events API, and even older versions did not
	// support server-side removal. This legacyWaitExitOrRemoved method
	// preserves that old behavior and any issues it may have.
	if versions.LessThan(apiClient.ClientVersion(), "1.30") {
		return legacyWaitExitOrRemoved(ctx, apiClient, containerID, waitRemove)
	}

	condition := container.WaitConditionNextExit
	if waitRemove {
		condition = container.WaitConditionRemoved
	}

	resultC, errC := apiClient.ContainerWait(ctx, containerID, condition)

	statusC := make(chan int)
	go func() {
		select {
		case result := <-resultC:
			if result.Error != nil {
				logrus.Errorf("Error waiting for container: %v", result.Error.Message)
				statusC <- 125
			} else {
				statusC <- int(result.StatusCode)
			}
		case err := <-errC:
			logrus.Errorf("error waiting for container: %v", err)
			statusC <- 125
		}
	}()

	return statusC
}

func legacyWaitExitOrRemoved(ctx context.Context, apiClient client.APIClient, containerID string, waitRemove bool) <-chan int {
	var removeErr error
	statusChan := make(chan int)
	exitCode := 125

	// Get events via Events API
	f := filters.NewArgs()
	f.Add("type", "container")
	f.Add("container", containerID)
	options := types.EventsOptions{
		Filters: f,
	}
	eventCtx, cancel := context.WithCancel(ctx)
	eventq, errq := apiClient.Events(eventCtx, options)

	eventProcessor := func(e events.Message) bool {
		stopProcessing := false
		switch e.Status {
		case "die":
			if v, ok := e.Actor.Attributes["exitCode"]; ok {
				code, cerr := strconv.Atoi(v)
				if cerr != nil {
					logrus.Errorf("failed to convert exitcode '%q' to int: %v", v, cerr)
				} else {
					exitCode = code
				}
			}
			if !waitRemove {
				stopProcessing = true
			} else {
				// If we are talking to an older daemon, `AutoRemove` is not supported.
				// We need to fall back to the old behavior, which is client-side removal
				if versions.LessThan(apiClient.ClientVersion(), "1.25") {
					go func() {
						removeErr = apiClient.ContainerRemove(ctx, containerID, types.ContainerRemoveOptions{RemoveVolumes: true})
						if removeErr != nil {
							logrus.Errorf("error removing container: %v", removeErr)
							cancel() // cancel the event Q
						}
					}()
				}
			}
		case "detach":
			exitCode = 0
			stopProcessing = true
		case "destroy":
			stopProcessing = true
		}
		return stopProcessing
	}

	go func() {
		defer func() {
			statusChan <- exitCode // must always send an exit code or the caller will block
			cancel()
		}()

		for {
			select {
			case <-eventCtx.Done():
				if removeErr != nil {
					return
				}
			case evt := <-eventq:
				if eventProcessor(evt) {
					return
				}
			case err := <-errq:
				logrus.Errorf("error getting events from daemon: %v", err)
				return
			}
		}
	}()

	return statusChan
}

// reportError is a utility method that prints a user-friendly message
// containing the error that occurred during parsing and a suggestion to get help
func reportError(stderr io.Writer, name string, str string, withHelp bool) {
	str = strings.TrimSuffix(str, ".") + "."
	if withHelp {
		str += "\nSee 'docker " + name + " --help'."
	}
	_, _ = fmt.Fprintln(stderr, "docker:", str)
}

// if container start fails with 'not found'/'no such' error, return 127
// if container start fails with 'permission denied' error, return 126
// return 125 for generic docker daemon failures
func runStartContainerErr(err error) error {
	trimmedErr := strings.TrimPrefix(err.Error(), "Error response from daemon: ")
	statusError := StatusError{StatusCode: 125}
	if strings.Contains(trimmedErr, "executable file not found") ||
		strings.Contains(trimmedErr, "no such file or directory") ||
		strings.Contains(trimmedErr, "system cannot find the file specified") {
		statusError = StatusError{StatusCode: 127}
	} else if strings.Contains(trimmedErr, syscall.EACCES.Error()) ||
		strings.Contains(trimmedErr, syscall.EISDIR.Error()) {
		statusError = StatusError{StatusCode: 126}
	}

	return statusError
}

// StatusError reports an unsuccessful exit by a command.
type StatusError struct {
	Status     string
	StatusCode int
}

func (e StatusError) Error() string {
	return fmt.Sprintf("Status: %s, Code: %d", e.Status, e.StatusCode)
}
