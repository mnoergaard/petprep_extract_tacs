.. petprep_extract_tacs documentation master file, created by
   sphinx-quickstart on Tue Nov 26 14:20:42 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to petprep_extract_tacs's documentation!
================================================

Overview
--------

This BIDS App is designed to extract time activity curves (TACs) from PET data. The workflow has options to extract TACs from different regions of the brain, and it uses the Brain Imaging Data Structure (BIDS) standard for organizing and describing the data. This README will guide you through how to use the app and the various options available. The workflow requires that freesurfer's recon-all was already executed for these subjects, and exist as a 'freesurfer' directory inside the derivatives directory for the given BIDS dataset.

Features
---------

  * BIDS compliant PET data input and output
  * Time Activity Curve extraction from various brain regions
  * Options for both surface and volume-based extractions including smoothing options

Requirements
------------

  * Python 3.9+
  * FreeSurfer v. 7.3.2
  * MATLAB RUNTIME (`sudo fs_install_mcr R2019b` when FreeSurfer is installed)

Installation
------------

Clone the repository and install the required packages:

.. code-block:: bash

   git clone
   git clone https://github.com/mnoergaard/petprep_extract_tacs.git
   cd petprep_extract_tacs
   pip install -e .

The package is also pip installable and can be installed using the following command

.. code-block:: bash
   
   pip install petprep-extract-tacs


Quickstart
----------

After installation, you'll need to have your data organized according to the BIDS standard. Once that's in place, you can run the app like this:

.. code-block:: bash

   petprep_extract_tacs /path/to/your/bids/dataset /path/to/output/dir --n_procs 4 --wm

Alternatively, you can run the code directly with Python using the `run.py` entrypoint:

.. code-block:: bash

   python3 run.py /path/to/your/bids/dataset /path/to/output/dir --n_procs 4 --wm

This will run the app on your BIDS dataset and save the output to the specified directory. Additional region-specific and smoothing options can be specified as detailed below.

.. _usage_page: usage.html

For more detailed usage see the usage_page_ section.


.. toctree::
   usage
   petprep_extract_tacs
   utils
   interfaces
   :maxdepth: 2
   :caption: Contents:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
