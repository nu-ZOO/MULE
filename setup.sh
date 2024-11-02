#!/usr/bin/env bash

PYTHON_VERSION='3.12'
DATE='10-24'
# set env name
MULE_ENV_NAME=MULE-${PYTHON_VERSION}-${DATE}

# set directory path to variable
export MULE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "$(<${MULE_DIR}/assets/MULE.txt)"

echo "Identified directory: $MULE_DIR"

# If conda isn't installed, install conda
if ! which conda >> /dev/null
then
	echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
	echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
	echo "No Conda installation detected, please install conda"
	echo "https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#regular-installation"
else
	# If conda environment exists, activate it. Otherwise create it
	if ! (conda env list | grep ${MULE_ENV_NAME}) >> /dev/null
	then
		echo "Couldn't find environment, creating environment..."
		conda env create -f MULE_environment.yml
	fi

	echo "Activating environment..."
	conda activate ${MULE_ENV_NAME}

	cd ${MULE_DIR}
fi
