'''
Simple logging script with file name altering based on date and time
'''

import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

def setup_logging(log_dir = None, log_name = None) -> None:
    '''
    Setup the logging configuration.
    Taken wholeheartedly from CARP
    '''
    # set and create log_dir if None
    if log_dir is None:
        log_dir = f'{os.environ['MULE_DIR']}/logs'
    os.makedirs(log_dir, exist_ok=True)

    # create unique log file name based on current date and time, or provided name
    if log_name is None:
        log_file = os.path.join(log_dir, f"MULE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    else:
        log_file = os.path.join(log_dir, log_name)

    # clear existing handlers so basicConfig works
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # basic logging config
    logging.basicConfig(
        level    = logging.DEBUG,
        format   = '%(levelname)-8s | %(asctime)s | %(message)s',
        handlers = [
            TimedRotatingFileHandler(log_file,
                                     when        = "midnight",
                                     interval    = 1,
                                     backupCount = 7),
            logging.StreamHandler()
            ]
        )
