package cmd

import (
    "os"
	"gopkg.in/yaml.v3"
)

type SSHAgent struct {
    Host        string `yaml:"host"`
    KeyPath     string `yaml:"key_path"`
}

type TConfig struct {
    Name                    string
    AppVersion              string
    BuildDate               string
    Workdir                 string

    Image                   string        `yaml:"image"`
    AdditionalVolumes       []string      `yaml:"additional_volumes"`
    SSHAgent                SSHAgent      `yaml:"ssh_agent"`
    DefaultShell            string        `default:"/bin/bash" yaml:"default_shell"`
    EntrypointScript        string        `yaml:"entrypoint_script"`
}


func (config *TConfig) LoadFromFile(filepath string) error {
    data, err := os.ReadFile(filepath)

    if err != nil {
        return err
    }

    if err := yaml.Unmarshal(data, config); err != nil {
        return err
    }

    return nil
}

var Config TConfig;


