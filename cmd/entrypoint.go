package cmd

import (
    "fmt"
    "os"
    "strings"
    "strconv"
    "os/user"
    "path/filepath"

    "github.com/spf13/cobra"
    log "github.com/sirupsen/logrus"
)


type tCliArgs struct {
    showVersion    bool
    logDebug       bool
    configPath     string
    forcePullImage bool
}

var cliArgs tCliArgs;


func Execute(appVersion string, buildDate string, confDir string) {
	rootCmd.PersistentFlags().StringVarP(&cliArgs.configPath, "config", "c", "", "path to config file")
	rootCmd.PersistentFlags().StringVarP(&cliArgs.configPath, "uid", "u", "", "run with custom uid. Needs for run with sudo")
	rootCmd.PersistentFlags().BoolVarP(&cliArgs.forcePullImage, "pull", "p", false, "force pull image")
	rootCmd.PersistentFlags().BoolVarP(&cliArgs.logDebug, "debug", "d", false, "debug log")
	rootCmd.PersistentFlags().BoolVarP(&cliArgs.showVersion, "version", "", false, "version information")


	Config.AppVersion = appVersion
	Config.BuildDate = buildDate
    Config.ConfDir = confDir

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
			exit(0)
		}

        if(cliArgs.configPath == "") {
            log.Error("-c argument required (no config path)")
            os.Exit(1)
        }
        err := Config.Load(cliArgs.configPath)
        if err != nil {
            log.Errorf("Error while read config file '%s': %s", cliArgs.configPath, err)
            exit(1)
        }

        usr, err := user.Current()
        if err != nil {
            log.Errorf("Cobra. Error while get current user: %s", err)
            exit(1)
        }
        basename :=filepath.Base(cliArgs.configPath)
        Config.Name = strings.TrimSuffix(basename, filepath.Ext(basename))
        workdirBasePath := usr.HomeDir + "/.cache/admin-toolbox/"
        workdirFullPath := workdirBasePath + Config.Name
        Config.Workdir = workdirFullPath
        log.Debugf("Workdir is %s", Config.Workdir)
        err = os.MkdirAll(Config.Workdir, os.FileMode(0700))
        if err != nil {
            log.Errorf("Error while creating workidr: %s", err)
            exit(1)
        }
        uid, _ := strconv.Atoi(usr.Uid)
        gid, _ := strconv.Atoi(usr.Gid)
        err = os.Chown(workdirBasePath, uid, gid)
        if err != nil {
            log.Errorf("Error while chown workidr: %s", err)
            exit(1)
        }
        err = os.Chown(workdirFullPath, uid, gid)
        if err != nil {
            log.Errorf("Error while chown workidr: %s", err)
            exit(1)
        }
		Run()
        exit(0)
	},
}
