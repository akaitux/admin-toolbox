from common.config import get_config
from common.logger import logger
import re


class Activate:
    def __init__(self):
        self._config = get_config()
        self.template_path = self._config.templates_path / 'activate.sh'
        self.install_path = self._config.workdir.root / 'activate'
        self.template = ""
        self.load_template()

    def load_template(self):
        with open(self.template_path, 'r') as f:
            self.template = f.read()
            self._apply_default_replaces()

    def write_template(self):
        with open(self.install_path, 'w') as f:
            f.write(self.template)

    def replace(self, replaces: dict[str, str]):
        for repl_from, repl_to in replaces.items():
            self.template = self.template.replace(repl_from, repl_to)

    def is_valid(self) -> bool:
        variable_regex = re.compile('.*<.*>.*')
        for line in self.template.split('\n'):
            if variable_regex.match(line):
                logger.error(
                    "Error. 'activate' contains variable from template ({})".format(line)
                )
                return False
        return True

    def _apply_default_replaces(self):
        replaces = {
            "<TOOLBOX_NAME>": str(self._config.toolbox_name),
            "<WORKDIR_ROOT>": str(self._config.workdir.root),
            "<WORKDIR_TMP>": str(self._config.workdir.tmp),
            "<WORKDIR_BIN>": str(self._config.workdir.bin),
        }
        self.replace(replaces)


