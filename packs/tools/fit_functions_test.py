import numpy       as np
import scipy.stats as scs

from . fit_functions import finger_signal

from hypothesis            import given
from hypothesis.strategies import floats

@given(floats(min_value =  -10, max_value =  10),
       floats(min_value = -500, max_value = 500),
       floats(min_value =    1, max_value =   2),
       floats(min_value =    0, max_value = 200))
def test_finger_signal_gaus_when_poisson_zero(bl, gain, sbl, sq):
    xaux = np.linspace(-10, 10, 1000)
    yres = finger_signal(xaux,  bl, 1, gain, sbl, sq, 0)
    ygau =  scs.norm.pdf(xaux, loc=bl, scale=sbl)

    assert np.array_equal(yres, ygau)

