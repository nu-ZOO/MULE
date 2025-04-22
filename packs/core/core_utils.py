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


# THIS SHOULD BE MOVED ELSEWHERE
class MalformedHeaderError(Exception):
    '''
    Header created for when two headers don't match up consecutively.
    Created initially for WD1 processing, but should be back-ported for WD2
    '''

    def __init__(self, header1, header2):
        self.header1 = header1
        self.header2 = header2

    def __str__(self):
        return f"MalformedHeaderError: Headers don't output expected result. Ensure the .dat file provided is formatted correctly.\nFirst Header {self.header1}\nSecond Header {self.header2}"

