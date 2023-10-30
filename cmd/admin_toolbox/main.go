package main

import (
    "os"
    "fmt"
    "admin-toolbox/cmd/cli"
    "admin-toolbox/cmd/commands"
    "github.com/spf13/cobra"
    "github.com/sirupsen/logrus"
)


var (
	Version             = "dev"
	Commit              = ""
    DefaultConfDir      = "/opt/admin-toolbox"
)



func run(rootCli *cli.Cli) error {
    tcmd := newCliCommand(rootCli)
    return tcmd.Cmd.Execute()
}

func newCliCommand(rootCli *cli.Cli) *cli.TopLevelCommand {
    cmd := &cobra.Command{
		Use:              "admin-toolbox [OPTIONS] COMMAND [ARG...]",
		SilenceUsage:     true,
		SilenceErrors:    true,
		TraverseChildren: true,
		Version:          fmt.Sprintf("%s, build %s", rootCli.Version, rootCli.Commit),
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

    args := cli.CliArgs{}

	cmd.Flags().StringVarP(&args.ConfPath, "config", "c", "", "path to config file")
	cmd.Flags().BoolVarP(&args.LogDebug, "debug", "d", false, "debug log")
	cmd.Flags().BoolVarP(&args.ShowVersion, "version", "v", false, "version information")

    rootCli.Args = &args

    commands.AddCommands(cmd, rootCli)

    return &cli.TopLevelCommand{
        Cmd: cmd,
        Cli: rootCli,
        Flags: cmd.Flags(),
    }
}

func main() {
    cli, err := cli.NewCli(Version, Commit, DefaultConfDir)
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

