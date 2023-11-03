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

func run(cli *atCli.Cli) error {
	tcmd := newCliCommand(cli)
	return tcmd.Execute()
}

func newCliCommand(cli *atCli.Cli) *cobra.Command {
	cmd := &cobra.Command{
		Use:                   "admin-toolbox [OPTIONS] COMMAND [ARG...]",
		SilenceUsage:          true,
		SilenceErrors:         true,
		TraverseChildren:      true,
		// Version:               rootCli.ShowVersion(),
		DisableFlagsInUseLine: true,
		CompletionOptions: cobra.CompletionOptions{
			DisableDefaultCmd:   false,
			HiddenDefaultCmd:    true,
			DisableDescriptions: true,
		},
        Run: func(cmd *cobra.Command, args []string) {
            if cli.Args.ShowVersion {
                fmt.Println("Version: " + Version)
                fmt.Println("Commit: " + Commit)
                fmt.Println("Default config dir: " + DefaultConfDir)
                os.Exit(0)

            }
            cmd.Help()
            os.Exit(0)
		},

	}
	cmd.SetIn(cli.In())
	cmd.SetOut(cli.Out())
	cmd.SetErr(cli.Err())

	args := atCli.CliArgs{}

	cmd.Flags().StringVarP(&args.ConfPath, "config", "c", "", "path to config file")
	cmd.Flags().StringVarP(
        &args.DefaultRootProfile,
        "defaultrootprofile", "p", "",
        fmt.Sprintf("Name of file from default profiles dir: %s", DefaultConfDir),
    )
	cmd.Flags().BoolVarP(&args.LogDebug, "debug", "d", false, "debug log")
	cmd.Flags().BoolVarP(&args.ShowVersion, "version", "v", false, "version information")

	cli.Args = &args

	commands.AddCommands(cmd, cli)
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
