import subprocess
import configparser

from pytest                import mark
from pytest                import raises
from pytest                import fixture

from packs.core.io         import read_config_file


@mark.parametrize("pack", ["acq", "proc", "tests"])
def test_executable_runs_successfully(pack, MULE_dir):
    '''
    This test is made to check if the current executable method for
    `bin/mule` to work as intended, accessing the relevant files when run.
    '''
                   # config will need to be improved
    run_pack = ["python3", MULE_dir + "/bin/mule", str(pack), "test_config"]

    # ensure output is successful (no errors)

    # this should be more complex in the future, such as if the config (which
    # will be a default for the tests) returns the test flag return a number, or
    # something in particular from subprocess
    assert subprocess.run(run_pack).returncode == 0


def test_incorrect_pack_returns_error(MULE_dir):

    # give an incorrect pack
    run_pack = ["python3", MULE_dir + "/bin/mule", "donkey", "config"]

    with raises(subprocess.CalledProcessError):
        subprocess.run(run_pack, check = True)

def test_config_read_correctly(data_dir):

    file_path = data_dir + 'configs/test_config.conf'

    expected_dict = {'test_1': 'a string', 'test_2': 6.03, 'test_3': 5, 'test_4': True}

    x = read_config_file(file_path)

    assert (x == expected_dict)


@mark.parametrize("config, error", [('malformed_header.conf', configparser.MissingSectionHeaderError),
                                    ('empty_entry.conf', SyntaxError),
                                    ('incorrect_format.conf', configparser.ParsingError)])
def test_malformed_config(config, error, data_dir):
    # provides expected output when config file is malformed
    file_path = data_dir + 'configs/' + config

    with raises(error):
        x = read_config_file(file_path)

@mark.parametrize("config, error", [('nonexistent_WD_version.conf', RuntimeError),
                                    ('nonexistent_process.conf', ValueError),
                                    ('single_multi_chan.conf', RuntimeError)])
                                    # these will change to value errors when other
                                    # packs are implemented
def test_processing_catches(config, error, MULE_dir, data_dir):

    config_path = data_dir + "configs/" + config

    run_pack = ["python3", MULE_dir + "/bin/mule", "proc", config_path]

    with raises(subprocess.CalledProcessError):
        subprocess.run(run_pack, check = True)
  
        
