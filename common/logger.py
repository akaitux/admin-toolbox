import logging


logger = logging.getLogger()


def setup_logger(debug=False):
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
            '%(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


