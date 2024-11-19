def flatten(xss):
    '''
    Flattens a 2D list
    eg: [[0,1,2,3], [4,5,6,7]] -> [0,1,2,3,4,5,6,7]
    '''
    return [x for xs in xss for x in xs]

def check_test(file):
    # quick check for test config
    if file == "test_config":
        print("Test config executable run successfully")
        return True
    else:
        return False