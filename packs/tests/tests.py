from packs.core.core_utils        import check_test


def tests(config_file):
    print("This works as expected: testing")
    print("In here you should read the config provided")

    if check_test(config_file):
        return