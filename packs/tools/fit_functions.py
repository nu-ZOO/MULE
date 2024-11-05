import numpy as np
import scipy.stats as scs


def finger_signal(xs         : np.array,
                  bl         : float   ,
                  amp        : float   ,
                  gain       : float   ,
                  sigmabl    : float   ,
                  sigmaq     : float   ,
                  poismu     : float   ,
                  maxpercent : float = 0.999
                  ) -> np.array:
    '''
    A function that returns a `finger plot' distribution; a
    poissonian distribution convoluted with gaussians. This distribution
    characterises the output expected from a PMT/SiPM charge histogram
    where x is the charge or PEs and y is the number of counts.

    Parameters
    ----------
    xs             : An array of 'x' values, typically PEs or ADCs
    bl             : The value beyond zero at which the poisson peaks occur [1]
    amp            : The amplitude applied to the poissonian peaks
    gain           : The gain (shift in x) applied to the poissonian peaks
    sigmabl        : The inherent sigma of each gaussian.
    sigmaq         : The sigma of each gaussian related to which poisson peak
                     it's related to.
    maxpercent     : The percentage of the poissonian distribution that is  

    Returns
    -------
    result         : The expected y values that given (x,y) describe the
                     finger plot distribution.

    Footnotes
    ---------
    [1] Generally these peaks would initialise at begin at x = 0 but in
    practice this isn't always the case
    '''

    # Collect the position and amplitudes of the finger plot peaks
    poispeaks_pos = np.arange(0, scs.poisson.ppf(maxpercent, 1))
    realpeaks_pos = gain * poispeaks_pos + bl
    realpeaks_amp = amp * scs.poisson.pmf(poispeaks_pos, poismu)

    # start y values collection
    result        = np.zeros_like(xs)

    # generate y values (results) that describe the poissonian distribution with
    # gaussian convolution across each peak
    for i in range(0, len(poispeaks_pos)):
            result += realpeaks_amp[i] * scs.norm.pdf(xs, loc=realpeaks_pos[i],
                                                    scale=np.sqrt(sigmabl**2 + sigmaq**2 * i))

    return result