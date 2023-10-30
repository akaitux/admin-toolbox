package commands

import (
    "admin-toolbox/cmd/cli"
    "admin-toolbox/cmd/run"
    "github.com/spf13/cobra"
)

func AddCommands(cmd *cobra.Command, cli *cli.Cli) {
    cmd.AddCommand(
        run.NewRunCommand(cli),
    )
}
