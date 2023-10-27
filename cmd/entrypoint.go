package cmd

import (
    "fmt"
    "os"

    "github.com/spf13/cobra"
    log "github.com/sirupsen/logrus"
)


type tCliArgs struct {
    showVersion    bool
    logDebug       bool
    configPath     string
}

var cliArgs tCliArgs;


func Execute(appVersion string, buildDate string) {
	rootCmd.PersistentFlags().StringVarP(&cliArgs.configPath, "config", "c", "", "path to config file")
	rootCmd.PersistentFlags().StringVarP(&cliArgs.configPath, "uid", "u", "", "run with custom uid")
	rootCmd.PersistentFlags().BoolVarP(&cliArgs.logDebug, "debug", "d", false, "debug")
	rootCmd.PersistentFlags().BoolVarP(&cliArgs.showVersion, "version", "", false, "version information")


	Config.AppVersion = appVersion
	Config.BuildDate = buildDate

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

var rootCmd = &cobra.Command{
	Use: "admin-toolbox -c [path_to_config]",
	Run: func(cmd *cobra.Command, args []string) {
        if cliArgs.logDebug {
            log.SetLevel(log.DebugLevel)
        } else {
            log.SetLevel(log.InfoLevel)
        }

		if(cliArgs.showVersion){
			fmt.Println("Version: " + Config.AppVersion)
			fmt.Println("Built at : " + Config.BuildDate)
			os.Exit(0)
		}

        if(cliArgs.configPath == "") {
            log.Error("-c argument required (no config path)")
            os.Exit(1)
        }
        err := Config.LoadFromFile(cliArgs.configPath)
        if err != nil {
            log.Errorf("Error while read config file '%s': %s", cliArgs.configPath, err)
            os.Exit(1)
        }

		Run()
	},
}
