<a href="https://github.com/jwaiton/MULE">
    <img src="assets/mulepngfull.png" alt="MULE" style="display: block; margin: 0;"/>
</a>
<p align="right" style="margin-top: 0;">
    <sub>Modification of <a href="https://commons.wikimedia.org/wiki/File:SupaiUSMailMules.jpg">photograph</a> taken by Elf, distributed under CC BY-SA 3.0 license.</sub>
</p>

_<p align="left">
Less is known of "The Mule" than of any character of comparable signifigance to Galactic history. His real name is unknown; his early life mere conjecture. Even the period of his greatest renown is known to us chiefly through the eyes of his antagonists and, principally, through those of a young bride. </p>_

**<p align="right"> -Encyclopedia Galactica </p>**

# <p align="center"> **M**easurement and **U**tilisation of **L**ight **E**xperiments @ the UoM neutrino laboratory. </p>

### What is MULE?

**MULE** is a centralised repository for the data acquisition and analysis software used within the University of Manchester's neutrino lab.

The functionality of this repository should cover:
- **Data acquisition** and **processing** for **PMTs** and **SiPMs** interfaced with CAEN hardware/software,
- **Analysis software** and scripts implemented directly upon the acquired data or provided for use once data is processed,
- **Adequate documentation** to allow for simple use of the respective tools provided within this repository.

## Usage

Usage is currently focused on binary files for readout from the above named systems.

After data collection and having saved the .bin files into the desired directory, one should copy the file path into the config file using a text editor (such as vim). In addtion, the destination file path and name should be enetered in the save_path line. Finally, ensure to have the correct wavedump edition as that will affect decoding.

> **_NOTE_** One can find the config file in /MULE/packs/configs

Once the config file has been edited and saved, one can execute the program from the terminal, after navigating to the directory where the config file was saved, by running:

`mule proc process_WD2_3channel.conf`

This will generate the .h5 file and store them in the predefined location.

In addition, there are several processing funcitons which are not yet run automatically from the config file but that can be found in /MULE/packs/proc

## Getting Started

The simplest method of installation is one done by cloning the github repository and running the setup.sh file from the terminal, as explained below.

To clone the directory one should install git from the terminal with something like pip:

`pip install git`

then, one can clone the repo to the desired directory by using,

`git clone https://github.com/nu-ZOO/MULE.git`

> **_NOTE_** The above link is taken from the repo's github page

The environemnt then needs to be created and activated. This can be achieved by running the following command from the MULE directory:

`source setup.sh`

One can also create an alias to activate the environment easily on every session.

