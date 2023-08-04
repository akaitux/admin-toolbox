import shutil
import sys
from common.logger import logger
from common.config import get_config

def check_dependencies():
    if not shutil.which('virtualenv'):
        logger.error("Dependency error: No python 'virtualenv' in PATH")
        sys.exit(1)
    if not shutil.which('git'):
        logger.error("Dependency error: No 'git' in PATH")
        sys.exit(1)
    if not shutil.which('curl'):
        logger.error("Dependency error: No 'curl' in PATH")
        sys.exit(1)
    if not shutil.which('unzip'):
        logger.error("Dependency error: No 'unzip' in PATH")
        sys.exit(1)
    if not shutil.which('tar'):
        logger.error("Dependency error: No 'tar' in PATH")
        sys.exit(1)

def validate_platform():
    config = get_config()
    if not config.is_x64 or not config.platform:
        logger.error("Current platform not supported (not x64)")
        sys.exit(1)
    if config.platform not in ('linux', 'darwin'):
        logger.error(
            "Current platform not supported ({})".format(config.platform)
        )
        sys.exit(1)


