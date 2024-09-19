import logging

logFormatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d %(levelname)s %(name)s pid=%(process)d tid=%(thread)d file=%(filename)s func=%(funcName)s line=%(lineno)d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

fileHandler = logging.FileHandler("splunk-add-on-ucc-modinput-test-functional.log")
fileHandler.setFormatter(logFormatter)

logger = logging.getLogger("splunk-add-on-ucc-modinput-test-functional")
logger.addHandler(fileHandler)
logger.setLevel(logging.DEBUG)
