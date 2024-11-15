#!/usr/bin/env bash


function install_conda {
	# This function has been heavily inspired by Invisible Cities (next-exp/IC on github).

	# Conda installation for MacOS and Linux
	case "$(uname -s)" in	
	       Darwin)
	           export CONDA_OS=MacOSX
	           ;;	
	       Linux)
	           export CONDA_OS=Linux
	           ;;
			*)
				echo Installation only support on MacOS and Linux.;
				exit 1;;
	esac

	echo Installing conda for $CONDA_OS # This doesn't currently understand/recognise arm based architectures. Fix!
	CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-py${PYTHON_VERSION//.}_24.9.2-0-${CONDA_OS}-x86_64.sh"
	if which wget; then
        wget ${CONDA_URL} -O miniconda.sh
    else
        curl ${CONDA_URL} -o miniconda.sh
    fi
    bash miniconda.sh -b -p $HOME/miniconda
	CONDA_SH=$HOME/miniconda/etc/profile.d/conda.sh
    source $CONDA_SH
    echo Activated conda by sourcing $CONDA_SH
}			



PYTHON_VERSION='3.12'
DATE='10-24'
# set env name
MULE_ENV_NAME=MULE-${PYTHON_VERSION}-${DATE}

# set directory path to variable
export MULE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# setup environment variables
export PATH=$MULE_DIR/bin:$PATH


echo "$(<${MULE_DIR}/assets/MULE.txt)"

echo "Identified directory: $MULE_DIR"

# If conda isn't installed, install conda
if ! which conda >> /dev/null
then
	echo "No Conda installation detected."
	echo @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
	echo 'Download conda? [Y/N]'
	select yn in "Yes" "No"; do
		case $yn in
			Y ) install_conda; break;;
			N ) echo "MULE activation aborted"; exit;;
		esac
	done
fi

# If conda environment exists, activate it. Otherwise create it
if ! (conda env list | grep ${MULE_ENV_NAME}) >> /dev/null
then
	echo "Couldn't find environment, creating environment..."
	conda env create -f MULE_environment.yml
fi

echo "Activating environment..."
conda activate ${MULE_ENV_NAME}

cd ${MULE_DIR}

