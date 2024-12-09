# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "petprep_extract_tacs"
copyright = "2024, Martin Norgaard"
author = "Martin Norgaard"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
# html_static_path = ["_static"]


def get_opt_fwhm(opt_params):
    """
    Obtain optimal FWHM values from a parameters file.

    :param opt_params: Path to the file containing optimal FWHM parameters.
    :type opt_params: str
    :return: A tuple containing:

        - **fwhm_x** (*float*): FWHM value along the x-axis.
        - **fwhm_y** (*float*): FWHM value along the y-axis.
        - **fwhm_z** (*float*): FWHM value along the z-axis.
        - **tsv_file** (*str*): Path to the generated TSV file with FWHM values.
    :rtype: tuple

    :notes:
        This function reads the optimal FWHM parameters from the given file, creates a DataFrame,
        saves it as a TSV file named `pvc-agtm_desc-fwhm_confounds.tsv` in the current working directory,
        and returns the FWHM values along with the path to the TSV file.
    """
    import os
    import pandas as pd

    new_pth = os.getcwd()

    with open(opt_params, "r") as file:
        contents = file.read()

    # Extracting the FWHM values for x, y, and z from the file
    fwhm_values = contents.split()

    # Assigning the values to fwhm_x, fwhm_y, and fwhm_z
    fwhm_x, fwhm_y, fwhm_z = map(float, fwhm_values)

    fwhm = pd.DataFrame({"fwhm_x": [fwhm_x], "fwhm_y": [fwhm_y], "fwhm_z": [fwhm_z]})

    fwhm.to_csv(
        os.path.join(new_pth, "pvc-agtm_desc-fwhm_confounds.tsv"), sep="\t", index=False
    )

    tsv_file = os.path.join(new_pth, "pvc-agtm_desc-fwhm_confounds.tsv")

    return fwhm_x, fwhm_y, fwhm_z, tsv_file
