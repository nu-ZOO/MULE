'''
Testing of the logger
'''

import os
import logging
from pathlib import Path

from packs.core.logging import setup_logging


def test_logfile_exists(tmp_path):
    '''
    check logfile exists upon initialisation
    '''
    log_name = 'test_log.log'
    setup_logging(tmp_path, log_name)

    full_path = os.path.join(tmp_path, log_name)
    assert os.path.exists(full_path)


def test_logfile_contents(tmp_path):
    '''
    check logfile contents match as expected when output.
    '''
    log_name = 'test_log.log'
    setup_logging(tmp_path, log_name)

    full_path = os.path.join(tmp_path, log_name)

    logging.warning('Test warning, this shouldnt cause any issues')

    # flush the logging handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # open and check log content
    log_content = Path(full_path).read_text()
    assert "WARNING" in log_content
    assert "Test warning, this shouldnt cause any issues" in log_content

