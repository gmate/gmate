import logging

LEVEL = logging.ERROR
#  Setup
log = logging.getLogger("GeditOpenFiles")
log.setLevel(LEVEL)

#create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(LEVEL)

#create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s -" +
    " %(levelname)s - %(message)s")

#add formatter to ch
ch.setFormatter(formatter)

#add ch to log
log.addHandler(ch)
