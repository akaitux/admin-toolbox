import subprocess
from common.logger import logger

def download_file(url, save_to, proxies = None):
    cmd = ['curl', '-q', '-o', str(save_to), '--fail', '-L']
    if proxies:
        if proxies['https']:
            cmd += ['-x', proxies['https']]
        elif proxies['http']:
            cmd += ['-x', proxies['http']]
    cmd.append(url)
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("Error while download {}".format(url))
        logger.error(exc.stdout)
        return False

