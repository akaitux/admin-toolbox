package cmd

import (
    "os"
	"gopkg.in/yaml.v3"
)

type TConfig struct {
    AppVersion              string
    BuildDate               string

    Image                   string        `yaml:"image"`
    AdditionalVolumes       []string      `yaml:"additional_volumes"`
    CustomDockerfile        string        `yaml:"custom_dockerfile"`
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


