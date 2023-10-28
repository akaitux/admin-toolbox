package cmd

import (
    "os"
    "os/user"
    "errors"
	"gopkg.in/yaml.v3"
    log "github.com/sirupsen/logrus"
)

type SSHAgent struct {
    Host        string `yaml:"host"`
    KeyPath     string `yaml:"key_path"`
}


type TUserConfig struct {
    Cmd                     []string            `yaml:"cmd"`
    Entrypoint              []string            `yaml:"entrypoint"`
    Env                     map[string]string   `yaml:"env"`
    SSHAgent                SSHAgent            `yaml:"ssh_agent"`
    HomeVolumes             []string            `yaml:"home_volumes"`
}


type TConfig struct {
    Name                    string
    AppVersion              string
    BuildDate               string
    ConfDir                 string
    Workdir                 string

    Image                   string              `yaml:"image"`
    AdditionalVolumes       []string            `yaml:"additional_volumes"`

    userConfig              TUserConfig         `yaml:"user_config"`
}


func (config *TConfig) Load(filepath string) error {
    defaultConfPath := config.ConfDir + "/default.yaml"

    usr, err := user.Current()
    if err != nil {
        return err
    }

    isDefaultConfExists := true
    if _, err := os.Stat(defaultConfPath); errors.Is(err, os.ErrNotExist) {
        isDefaultConfExists = false
    }

    if usr.Uid == "0" || isDefaultConfExists == false {
        // If user is root or default config doesn't exists - just load config as main config
        log.Debugf("Load config without default.conf")
        configData, err := os.ReadFile(filepath)
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

    userConfigData, err := os.ReadFile(filepath)
    if err != nil {
        return err
    }
    userConfig := TUserConfig{}
    if err := yaml.Unmarshal(userConfigData, &userConfig); err != nil {
        return err
    }
    config.userConfig = userConfig
    return nil
}

var Config TConfig;

