import logging


LOG_FORMAT = "[%(asctime)s] - %(levelname)s ==> %(message)s"
DATE_FORMAT = "%m/%d %H:%M:%S"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)


class logger:
    def info(msg):
        logging.info(msg)

    def warning(msg):
        logging.warning(msg)

    def error(msg):
        logging.error(msg)
