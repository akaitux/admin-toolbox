package atCli

import (
	"admin-toolbox/config"
	"admin-toolbox/streams"
	"admin-toolbox/workdir"
	"github.com/docker/docker/client"
	"github.com/moby/term"
	"github.com/sirupsen/logrus"
	"io"
	"os"
	"os/user"
)

type CliArgs struct {
	ShowVersion         bool
	LogDebug            bool
	ConfPath            string
	DefaultRootProfile string
}

type Cli struct {
	Version                 string
	Commit                  string
	DefaultConfDir          string
	DefaultRootProfile      string
	Config                  config.Config
	CurrentUser             *user.User
	Workdir                 workdir.Workdir
	Args                    *CliArgs
	Client                  *client.Client
	in                      *streams.In
	out                     *streams.Out
	err                     io.Writer
}


func (cli *Cli) Init() error {
	var err error

	if cli.Args.LogDebug {
		logrus.SetLevel(logrus.DebugLevel)
	} else {
		logrus.SetLevel(logrus.InfoLevel)
	}
	if cli.Args.ConfPath == "" {
		logrus.Error("-c argument required (no config path)")
		os.Exit(1)
	}

	cli.CurrentUser, err = user.Current()
	if err != nil {
		return err
	}

	logrus.Debugf("DefaultConfDir: %s", cli.DefaultConfDir)

    cli.DefaultRootProfile = cli.Args.DefaultRootProfile

	err = cli.Config.Init(cli.DefaultConfDir, cli.DefaultRootProfile, cli.Args.ConfPath, cli.CurrentUser)
	if err != nil {
		logrus.Errorf("Error while read config file '%s': %s", cli.Args.ConfPath, err)
		os.Exit(1)
	}

	cli.Workdir = workdir.NewWorkdir(cli.Config.Name, cli.CurrentUser)

	cli.Client, err = client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		logrus.Errorf("Error while build docker client: %s", err)
		os.Exit(1)
	}

	if err = cli.Workdir.MakeWorkdir(); err != nil {
		logrus.Errorf("Error while make workdir: %s", err)
		os.Exit(1)
	}
	return nil
}

func NewCli(version string, commit string, defaultConfDir string) (*Cli, error) {
	cli := Cli{
		Version:        version,
		Commit:         commit,
		DefaultConfDir: defaultConfDir,
	}
	cli.setupDefaultStreams()

	return &cli, nil
}

// Out returns the writer used for stdout
func (cli *Cli) Out() *streams.Out {
	return cli.out
}

// Err returns the writer used for stderr
func (cli *Cli) Err() io.Writer {
	return cli.err
}

// SetIn sets the reader used for stdin
func (cli *Cli) SetIn(in *streams.In) {
	cli.in = in
}

// In returns the reader used for stdin
func (cli *Cli) In() *streams.In {
	return cli.in
}

func (cli *Cli) setupDefaultStreams() {
	stdin, stdout, stderr := term.StdStreams()
	cli.in = streams.NewIn(stdin)
	cli.out = streams.NewOut(stdout)
	cli.err = stderr
}
