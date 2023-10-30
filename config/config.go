package config

import (
    "os"
    "os/user"
    "errors"
    "path/filepath"
    "strings"
    "admin-toolbox/workdir"
	"gopkg.in/yaml.v3"
    log "github.com/sirupsen/logrus"
    "dario.cat/mergo"
)

type SSHAgent struct {
    Host        string `yaml:"host"`
    KeyPath     string `yaml:"key_path"`
}


type UserConfig struct {
    Cmd                     []string            `yaml:"cmd"`
    Entrypoint              []string            `yaml:"entrypoint"`
    Env                     []string            `yaml:"env"`
    SSHAgent                SSHAgent            `yaml:"ssh_agent"`
    HomeVolumes             []string            `yaml:"home_volumes"`
}


type Config struct {
    Name                    string
    DefaultConfDir          string
    Workdir                 workdir.Workdir

    Image                   string              `yaml:"image"`
    AdditionalVolumes       []string            `yaml:"additional_volumes"`

    UserConfig              UserConfig         `yaml:"user_config"`
}


func (config *Config) Init(defaultConfDir string, fpath string, usr *user.User) error {
    var err error

    config.DefaultConfDir = defaultConfDir

    defaultConfPath := config.DefaultConfDir + "/default.yaml"

    basename := filepath.Base(fpath)
    config.Name = strings.TrimSuffix(basename, filepath.Ext(basename))

    isDefaultConfExists := true
    if _, err := os.Stat(defaultConfPath); errors.Is(err, os.ErrNotExist) {
        isDefaultConfExists = false
    }

    if usr.Uid == "0" || isDefaultConfExists == false {
        // If user is root or default config doesn't exists - just load config as main config
        log.Debugf("Load config without default.conf")
        configData, err := os.ReadFile(fpath)
        if err != nil {
            return err
        }
        if err := yaml.Unmarshal(configData, config); err != nil {
            return err
        }
        return nil
    }

    log.Debugf("Load config from default.conf")

    defaultConfig, err := os.ReadFile(defaultConfPath)
    if err != nil {
        return err
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

