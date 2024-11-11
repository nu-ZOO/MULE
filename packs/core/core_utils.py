

def flatten(xss):
    '''
    Flattens a 2D list
    eg: [[0,1,2,3], [4,5,6,7]] -> [0,1,2,3,4,5,6,7]
    '''
    return [x for xs in xss for x in xs]