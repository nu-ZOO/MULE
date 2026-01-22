from packs.core.core_utils        import check_test
import logging

def tests(config_file):
    logging.info("This works as expected: testing")
    logging.info("In here you should read the config provided")

    if check_test(config_file):
        return
