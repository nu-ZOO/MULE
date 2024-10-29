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
    poispeaks_pos = np.arange(0, scs.poisson.ppf(maxpercent, 1))
    realpeaks_pos = gain * poispeaks_pos + bl
    realpeaks_amp = amp * scs.poisson.pmf(poispeaks_pos, poismu)
    result        = np.zeros_like(xs)

    result += realpeaks_amp[0] * scs.norm.pdf(xs, loc=realpeaks_pos[0], scale=sigmabl)

    for i in range(1, len(poispeaks_pos)):
        result += realpeaks_amp[i] * scs.norm.pdf(xs, loc=realpeaks_pos[i],
                                                  scale=np.sqrt(sigmabl**2 + sigmaq**2 * i))
    return result