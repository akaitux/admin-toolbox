package config

import (
    "fmt"
	"os"
	"os/user"
	"path/filepath"
	"strings"
	"errors"
	"admin-toolbox/workdir"
	"dario.cat/mergo"
	log "github.com/sirupsen/logrus"
	"gopkg.in/yaml.v3"
)

type SSHAgent struct {
	Host    string `yaml:"host"`
	KeyPath string `yaml:"key_path"`
}

type UserConfig struct {
	Cmd         []string `yaml:"cmd"`
	Entrypoint  []string `yaml:"entrypoint"`
	Env         []string `yaml:"env"`
	SSHAgent    SSHAgent `yaml:"ssh_agent"`
	HomeVolumes []string `yaml:"home_volumes"`
}

type Config struct {
	Name                string
	Workdir             workdir.Workdir

	Image               string   `yaml:"image"`
	AdditionalVolumes   []string `yaml:"additional_volumes"`
    InheritEnv          bool     `yaml:"inherit_env"`
    InheritEnvExclude   []string `yaml:"inherit_env_exclude"`

	UserConfig UserConfig `yaml:"user_config"`
}

func (config *Config) Init(
    defaultConfDir string,
    defaultRootProfile string,
    fpath string,
    usr *user.User,
) error {
	var err error

    if strings.Contains(defaultRootProfile, "..") {
        return fmt.Errorf("Error. Profile must be a file name, not path")
    }
    if strings.Contains(defaultRootProfile, "/") {
        return fmt.Errorf("Error. Profile must be a file name, not path")
    }

	basename := filepath.Base(fpath)
	config.Name = strings.TrimSuffix(basename, filepath.Ext(basename))

	isDefaultConfExists := true
	if _, err := os.Stat(defaultConfDir); errors.Is(err, os.ErrNotExist) {
		isDefaultConfExists = false
	}

	if usr.Uid == "0" || isDefaultConfExists == false {
		// If user is root or default config doesn't exists - just load config as main config
		log.Debugf("Load config without default configs")
		configData, err := os.ReadFile(fpath)
		if err != nil {
			return err
		}
		if err := yaml.Unmarshal(configData, config); err != nil {
			return err
		}
		return nil
	}

	log.Debugf("Load config from defaults")

    if defaultRootProfile == "" {
        return fmt.Errorf(
            "No default profile (-p) with filename from '%s', it's needed because it's suid mode",
            defaultConfDir,
        )
    }

    defaultConfPath := fmt.Sprintf("%s/%s", defaultConfDir, defaultRootProfile)
	defaultConfig, err := os.ReadFile(defaultConfPath)
	if err != nil {
        return fmt.Errorf("Error while open file with default profile from %s: %s", defaultConfPath, err)
	}
	if err := yaml.Unmarshal(defaultConfig, config); err != nil {
		return err
	}

	userConfigData, err := os.ReadFile(fpath)
	if err != nil {
		return err
	}
	userConfig := UserConfig{}
	if err := yaml.Unmarshal(userConfigData, &userConfig); err != nil {
		return err
	}
	//config.userConfig = userConfig
	if err := mergo.Merge(&config.UserConfig, userConfig); err != nil {
		return err
	}
	return nil
}
