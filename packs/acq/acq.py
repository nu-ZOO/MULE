from packs.core.core_utils        import check_test


def acq(config_file):
    print("This works as expected: acquisition")
    print("In here you should read the config provided")

    if check_test(config_file):
        return

