package cmd

import (
    "os"
	"gopkg.in/yaml.v3"
)

type TConfig struct {
    AppVersion              string
    BuildDate               string

    Image                   string `yaml:"image"`
    Workdir                 string `yaml:"workdir"`
    ReplaceDotSSH           bool   `yaml:"replace_dot_ssh"`
    ReplaceDotConfig        bool   `yaml:"replace_dot_config"`
    ReplaceDotKube          bool   `yaml:"replace_dot_kube"`
    AnsibleCfg              string `yaml:"ansible_cfg"`
    CustomDockerfile        string `yaml:"custom_dockerfile"`
    EntrypointScript        string `yaml:"entrypoint_script"`
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


