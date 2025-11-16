from packs.core.core_utils        import check_test
import logging

def acq(config_file):
    logging.info("This works as expected: acquisition")
    logging.info("In here you should read the config provided")

    if check_test(config_file):
        return

