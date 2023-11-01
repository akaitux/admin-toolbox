package main

import (
	"admin-toolbox/cmd/atCli"
	"admin-toolbox/cmd/commands"
	"fmt"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"os"
)

var (
	Version        = "dev"
	Commit         = ""
	DefaultConfDir = "/opt/admin-toolbox/defaults"
)

func run(rootCli *atCli.Cli) error {
	tcmd := newCliCommand(rootCli)
	return tcmd.Execute()
}

func newCliCommand(rootCli *atCli.Cli) *cobra.Command {
	cmd := &cobra.Command{
		Use:                   "admin-toolbox [OPTIONS] COMMAND [ARG...]",
		SilenceUsage:          true,
		SilenceErrors:         true,
		TraverseChildren:      true,
		Version:               fmt.Sprintf("%s, build %s", rootCli.Version, rootCli.Commit),
		DisableFlagsInUseLine: true,
		CompletionOptions: cobra.CompletionOptions{
			DisableDefaultCmd:   false,
			HiddenDefaultCmd:    true,
			DisableDescriptions: true,
		},
	}
	cmd.SetIn(rootCli.In())
	cmd.SetOut(rootCli.Out())
	cmd.SetErr(rootCli.Err())

	args := atCli.CliArgs{}

	cmd.Flags().StringVarP(&args.ConfPath, "config", "c", "", "path to config file")
	cmd.Flags().StringVarP(
        &args.DefaultRootProfile,
        "defaultrootprofile", "p", "",
        fmt.Sprintf("Name of file from default profiles dir: %s", DefaultConfDir),
    )
	cmd.Flags().BoolVarP(&args.LogDebug, "debug", "d", false, "debug log")
	cmd.Flags().BoolVarP(&args.ShowVersion, "version", "v", false, "version information")

	rootCli.Args = &args

	commands.AddCommands(cmd, rootCli)
	return cmd

}

func main() {
	cli, err := atCli.NewCli(Version, Commit, DefaultConfDir)
	if err != nil {
		logrus.Errorf("Error in setup Cli: %s", err)
		os.Exit(1)
	}
	logrus.SetOutput(cli.Err())
	if err := run(cli); err != nil {
		logrus.Errorf("%s", err)
		logrus.Debugf("Cleanup workdir %s", cli.Workdir.Fullpath)
		cli.Workdir.Cleanup()
		os.Exit(1)
	}
}
