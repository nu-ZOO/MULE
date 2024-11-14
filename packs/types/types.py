import numpy as np


event_info_type = np.dtype([
            ('event_number', np.uint32), 
            ('timestamp', np.uint64), 
            ('samples', np.uint32), 
            ('sampling_period', np.uint64), 
            ('channels', np.int32),
            ])

def rwf_type(samples):
    rwf_type        = nd.type([
                ('event_number', np.uint32),
                ('channels', np.int32),
                ('rwf', np.float32, (samples,))
    
    ])  