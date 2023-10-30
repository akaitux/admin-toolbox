package run

import (
	"admin-toolbox/cmd/cli"
	"github.com/spf13/cobra"
)

type runOptions struct {
	forcePullImage bool
	customUid      int
}

func NewRunCommand(cli *cli.Cli) *cobra.Command {
	//https://github.com/docker/cli/blob/master/cli/command/container/run.go#L32
	var options runOptions
	cmd := &cobra.Command{
		Use:   "run",
		Short: "run your container",
		RunE: func(cmd *cobra.Command, args []string) error {
			if err := cli.Init(); err != nil {
				return nil
			}
			return run(cli, options)
		},
	}

	cmd.Flags().BoolVarP(&options.forcePullImage, "pull", "p", false, "force pull image")
	cmd.Flags().IntVarP(&options.customUid, "uid", "u", 1000, "run with custom uid. Needs for run with sudo")
	return cmd
}
