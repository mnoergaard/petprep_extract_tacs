# BIDS App for PETPrep Extract Time Activity Curves Workflow

## Overview

This BIDS App is designed to extract time activity curves (TACs) from PET data. The workflow has options to extract TACs from different regions of the brain, and it uses the Brain Imaging Data Structure (BIDS) standard for organizing and describing the data. This README will guide you through how to use the app and the various options available.

## Features

  * BIDS compliant PET data input and output
  * Time Activity Curve extraction from various brain regions
  * Options for both surface and volume-based extractions including smoothing options

## Requirements

  * Python 3.9+
  * FreeSurfer v. 7.3.2
  * MATLAB RUNTIME (`sudo fs_install_mcr R2019b` when FreeSurfer is installed)

## Installation

Clone the repository and install the required packages:

<pre>
git clone https://github.com/mnoergaard/petprep_extract_tacs.git
cd petprep_extract_tacs
pip install -e .
</pre>

The package is also pip installable and can be installed using the following command

<pre>
pip install petprep-extract-tacs
</pre>

## Quickstart

To get started, you'll need to have your data organized according to the BIDS standard. Once that's in place, you can run the app like this:

```bash
python3 run.py --bids_dir /path/to/your/bids/dataset --output_dir /path/to/output/dir --n_procs 4 --wm
```

This will run the app on your BIDS dataset and save the output to the specified directory. Additional region-specific and smoothing options can be specified as detailed below.

## Detailed Usage

### Required Arguments
Here's a detailed look at all the options you can use with this BIDS App:

#### `--bids_dir`

This is the directory with your input dataset formatted according to the BIDS standard. This argument is required.

#### `--output_dir`

This is the directory where the output files should be stored. If you are running group level analysis, this folder should be prepopulated with the results of the participant level analysis.

### Required Arguments

#### `--analysis_level`

This argument defines the level of the analysis that will be performed. Multiple participant level analyses can be run independently (in parallel) using the same output_dir. The default is 'participant'. The choices are 'participant' and 'group'.

#### `--participant_label`

This argument specifies the label(s) of the participant(s) that should be analyzed. The label corresponds to sub-<participant_label> from the BIDS spec (so it does not include "sub-"). If this parameter is not provided, all subjects should be analyzed. Multiple participants can be specified with a space-separated list.

### Processing options

#### `--n_procs`

This argument sets the number of processors to use when running the workflow. The default is 2.

#### Region extration options

`--gtm`, `--brainstem`, `--thalamicNuclei`, `--hippocampusAmygdala`, `--wm`, `--raphe`, `--limbic`

These options, when specified, instruct the workflow to extract time activity curves from the corresponding brain regions.

#### Smoothing and output space options (surface and/or volume)

`--surface`, `--surface_smooth` (e.g. `--surface_smooth 10`), `--volume`, `--volume_smooth` (e.g. `--volume_smooth 10`) 

#### Partial Volume Correction (using adaptive GTM)

`--agtm`, `--psf` (initial PSF guess, e.g. `--psf 3`)

### Advanced options

#### `--petprep_hmc`

When specified, the workflow will use outputs from petprep_hmc as input.

#### `--skip_bids_validator`

This argument, when specified, will skip the BIDS dataset validation step.

#### `--merge_runs`

Option to merge TACs across runs for each subject within a single session.

### Docker options

#### `docker`

Indicates the script will run within a Docker container.

#### `--run_as_root`

Runs the script as root if executed within Docker.

#### `-v`, `--version`

This argument displays the current version of the PETPrep extract time activity curves BIDS-App.
