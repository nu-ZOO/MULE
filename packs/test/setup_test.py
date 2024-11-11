import os
import subprocess

from pytest                import mark
from pytest                import raises



@mark.parametrize("pack", ["acq", "proc", "test"])
def test_executable_runs_successfully(pack):
    '''
    This test is made to check if the current executable method for
    `bin/mule` to work as intended, accessing the relevant files when run.
    '''
    bin_dir = str(os.environ['MULE_DIR'])
                                                            # config will need to be improved
    run_pack = ["python3", bin_dir + "/bin/mule", str(pack), "config"]

    # ensure output is successful (no errors)

    # this should be more complex in the future, such as if the config (which
    # will be a default for the tests) returns the test flag return a number, or
    # something in particular from subprocess
    assert subprocess.run(run_pack).returncode == 0


def test_incorrect_pack_returns_error():
    bin_dir = str(os.environ['MULE_DIR'])

    # give an incorrect pack
    run_pack = ["python3", bin_dir + "/bin/mule", "donkey", "config"]

    with raises(subprocess.CalledProcessError):
        subprocess.run(run_pack, check = True)
