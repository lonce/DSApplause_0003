

# Setting up DSApplause_0003

## User instructions

  >> git clone https://github.com/lonce/DSApplause_0003.git

  >> cd DSApplause_0003/

  >> conda create -n DSSynth python=3.8 ipykernel numba

  >> conda activate DSSynth

  >> pip install -r requirements.txt --src '.'

# Setup and run jupyter notebook

>> pip install jupyter

>> python3.8 -m ipykernel install --user --name DSApplause_0003

>> jupyter notebook

>> Select *ApplauseViz.ipynb* in the browser interface

## Generate files from commandline

>> python DSGenerator/generate.py --configfile config_file.json --outputpath NewDataset

