import os
import subprocess
import configparser

from pytest                import mark
from pytest                import raises

from packs.core.io         import read_config_file


@mark.parametrize("pack", ["acq", "proc", "tests"])
def test_executable_runs_successfully(pack):
    '''
    This test is made to check if the current executable method for
    `bin/mule` to work as intended, accessing the relevant files when run.
    '''
    bin_dir = str(os.environ['MULE_DIR'])
                                                            # config will need to be improved
    run_pack = ["python3", bin_dir + "/bin/mule", str(pack), "test_config"]

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

def test_config_read_correctly():

    MULE_dir = str(os.environ['MULE_DIR'])
    file_path = MULE_dir + '/packs/tests/data/configs/test_config.conf'

    expected_dict = {'test_1': 'a string', 'test_2': 6.03, 'test_3': 5, 'test_4': True}

    x = read_config_file(file_path)

    assert (x == expected_dict)


@mark.parametrize("config, error", [('malformed_header.conf', configparser.MissingSectionHeaderError),
                                    ('empty_entry.conf', SyntaxError),
                                    ('incorrect_format.conf', configparser.ParsingError)])
def test_malformed_config(config, error):
    # provides expected output when config file is malformed
    MULE_dir = str(os.environ['MULE_DIR'])
    file_path = MULE_dir + '/packs/tests/data/configs/' + config

    with raises(error):
        x = read_config_file(file_path)
