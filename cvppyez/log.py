import logging


def setup_log(filename):
    new_log = logging.getLogger(__name__)
    new_log.setLevel(logging.WARNING)

    sh = logging.FileHandler(filename)
    fh = logging.Formatter('%(levelname)s:%(message)s')
    sh.setFormatter(fh)
    new_log.addHandler(sh)
    return new_log
