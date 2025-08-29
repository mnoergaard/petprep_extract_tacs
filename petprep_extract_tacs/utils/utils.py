# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""


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


def ctab_to_dsegtsv(ctab_file):
    """
    Convert a `.ctab` file to a `.tsv` file containing segmentation indices and names.

    :param ctab_file: Path to the `.ctab` file to be read.
    :type ctab_file: str
    :return: Path to the generated `.tsv` file with segmentation indices and names.
    :rtype: str

    :notes:
        This function reads the `.ctab` file into a pandas DataFrame, keeping only the first two columns.
        The columns are renamed to ``index`` and ``name``. The DataFrame is then written to a `.tsv` file
        with the same base name as the input `.ctab` file.
    """
    import pandas as pd

    # Read the .ctab file into a DataFrame
    ctab_df = pd.read_csv(
        ctab_file,
        header=None,
        delim_whitespace=True,
        usecols=[0, 1],
        names=["index", "name"],
    )

    # Create the output .tsv file name
    tsv_file = ctab_file.replace(".ctab", ".tsv")

    # Write the DataFrame to the .tsv file (without the index)
    ctab_df.to_csv(tsv_file, sep="\t", index=False)

    return tsv_file


def avgwf_to_tacs(avgwf_file, ctab_file, json_file):
    """
    Generate Time Activity Curves (TACs) from average waveform data and metadata.

    :param avgwf_file: Path to the `avgwf` `.txt` file containing average waveform data.
    :type avgwf_file: str
    :param ctab_file: Path to the `.ctab` file containing segmentation indices and names.
    :type ctab_file: str
    :param json_file: Path to the `.json` file containing frame timing information.
    :type json_file: str
    :return: Path to the generated `.tsv` file containing the TACs.
    :rtype: str

    :notes:
        This function performs the following steps:

        - Reads the `.ctab` file to obtain region names.
        - Reads the average waveform data from the `avgwf` file.
        - Reads frame timing information (``FrameTimesStart`` and ``FrameDuration``) from the `.json` file.
        - Inserts the frame timings into the waveform DataFrame.
        - Writes the combined data to a `.tsv` file with column names based on the `.ctab` file.

        The resulting `.tsv` file contains TACs suitable for further analysis.
    """
    import pandas as pd
    import numpy as np
    import json

    # Read the .ctab file and get region names
    ctab_df = pd.read_csv(
        ctab_file,
        header=None,
        delim_whitespace=True,
        usecols=[0, 1],
        names=["index", "name"],
    )
    region_names = ctab_df["name"].tolist()

    # Read the avgwf data
    avgwf_df = pd.read_csv(
        avgwf_file,
        header=None,
        delim_whitespace=True,
        names=region_names,
    )

    # Read the JSON file to get frame times and durations
    with open(json_file, "r") as f:
        json_data = json.load(f)
    frame_times = np.array(json_data["FrameTimesStart"])
    frame_durations = np.array(json_data["FrameDuration"])

    # Insert frame times and durations into the avgwf DataFrame
    avgwf_df.insert(0, "FrameTimesStart", frame_times)
    avgwf_df.insert(1, "FrameDuration", frame_durations)

    # Create the output .tsv file name
    tsv_file = avgwf_file.replace(".txt", ".tsv")

    # Write the DataFrame to a .tsv file
    avgwf_df.to_csv(tsv_file, sep="\t", index=False)

    return tsv_file


def stats_to_stats(summary_file):
    """
    Reads a 'summary.stats' file, transforms the data, and saves it as a '.tsv' file.

    :param summary_file: The path to the input '.stats' file.
    :type summary_file: str
    :returns: The path to the output '.tsv' file.
    :rtype: str

    The function performs the following steps:
    1. Reads the 'summary.stats' file into a DataFrame, ignoring lines starting with '#'.
       Only the 2nd, 4th, and 5th columns (0-indexed) are read, named 'index', 'volume_mm3', and 'name'.
    2. Renames the 'volume_mm3' column to 'volume-mm3'.
    3. Reorders the DataFrame columns to ['index', 'name', 'volume-mm3'].
    4. Writes the DataFrame to a '.tsv' file with a tab separator and without the index.
    5. Returns the path to the output '.tsv' file.
    """
    import pandas as pd

    # Read the 'summary.stats' file into a DataFrame.
    # We only take the 4th and 5th columns (0-indexed), which we name 'volume_mm3' and 'name'.
    # Lines starting with '#' are ignored.
    summary_df = pd.read_csv(
        summary_file,
        comment="#",
        header=None,
        delim_whitespace=True,
        usecols=[1, 3, 4],
        names=["index", "volume_mm3", "name"],
    )

    # Create a new DataFrame where each row of 'summary_df' is a column.
    # The column names in the new DataFrame are taken from the 'name' column of 'summary_df',
    # and the values are taken from the 'volume_mm3' column of 'summary_df'.
    # summary_df_output = pd.DataFrame([summary_df['volume_mm3'].to_list()], columns=summary_df['name'].to_list())

    # Create the output file name by replacing '.stats' with '.tsv' in the input file name.
    tsv_file = summary_file.replace(".stats", ".tsv")

    # Write the new DataFrame to the output file.
    # We use a tab separator, and we don't write the index.
    summary_df.rename(columns={"volume_mm3": "volume-mm3"}, inplace=True)
    summary_df = summary_df[["index", "name", "volume-mm3"]]
    summary_df.to_csv(tsv_file, sep="\t", index=False)

    # Return the output file name.
    return tsv_file


def summary_to_stats(summary_file):
    """
    This function reads a 'summary.stats' file, transforms the data, and saves it as a '.tsv' file.

    :param summary_file: The path to the input '.stats' file.
    :type summary_file: str

    :returns: The path to the output '.tsv' file.
    :rtype: str
    """

    import pandas as pd

    # Read the 'summary.stats' file into a DataFrame.
    # We only take the 4th and 5th columns (0-indexed), which we name 'volume_mm3' and 'name'.
    # Lines starting with '#' are ignored.
    summary_df = pd.read_csv(
        summary_file,
        comment="#",
        header=None,
        delim_whitespace=True,
        usecols=[1, 3, 4],
        names=["index", "volume_mm3", "name"],
    )

    # Create a new DataFrame where each row of 'summary_df' is a column.
    # The column names in the new DataFrame are taken from the 'name' column of 'summary_df',
    # and the values are taken from the 'volume_mm3' column of 'summary_df'.
    # summary_df_output = pd.DataFrame([summary_df['volume_mm3'].to_list()], columns=summary_df['name'].to_list())

    # Create the output file name by replacing '.stats' with '.tsv' in the input file name.
    tsv_file = summary_file.replace(".txt", ".tsv")

    # Write the new DataFrame to the output file.
    # We use a tab separator, and we don't write the index.
    summary_df.rename(columns={"volume_mm3": "volume-mm3"}, inplace=True)
    summary_df = summary_df[["index", "name", "volume-mm3"]]
    summary_df.to_csv(tsv_file, sep="\t", index=False)

    # Return the output file name.
    return tsv_file


def gtm_stats_to_stats(gtm_stats):
    import pandas as pd
    import numpy as np
    import json
    import nibabel as nib
    import os

    new_pth = os.getcwd()

    gtm_df = pd.read_csv(
        gtm_stats,
        comment="#",
        header=None,
        delim_whitespace=True,
        usecols=[1, 3, 4],
        names=["index", "volume_mm3", "name"],
    )

    # Create a new DataFrame where each row of 'summary_df' is a column.
    # The column names in the new DataFrame are taken from the 'name' column of 'summary_df',
    # and the values are taken from the 'volume_mm3' column of 'summary_df'.
    # gtm_df_output = pd.DataFrame([gtm_df['volume_mm3'].to_list()], columns=gtm_df['name'].to_list())

    # Create the output file name by replacing '.stats' with '.tsv' in the input file name.

    tsv_file = os.path.join(new_pth, "seg-gtm_desc-preproc_morph.tsv")

    # Write the new DataFrame to the output file.
    # We use a tab separator, and we don't write the index.
    gtm_df.rename(columns={"volume_mm3": "volume-mm3"}, inplace=True)
    gtm_df.to_csv(tsv_file, sep="\t", index=False)

    # Return the output file name.
    return tsv_file


def gtm_to_tacs(in_file, json_file, gtm_stats, pvc_dir):
    """
    This function reads a .ctab file and a .json file into pandas DataFrames. It also reads a .gtm file and extracts the 'FrameTimesStart' and 'FrameDuration' lists,
    which are converted into numpy arrays and inserted as the first and second columns, respectively, to the gtm DataFrame. The modified gtm DataFrame is then written to a .tsv file with column names based on the .ctab file.

    :param in_file: The path to the .gtm file to be read.
    :type in_file: str
    :param json_file: The path to the .json file to be read. The 'FrameTimesStart' and 'FrameDuration' lists from this file are added as columns to the gtm DataFrame.
    :type json_file: str
    :param ctab_file: The path to the .ctab file to be read. The first column of this file is used as column names for the gtm DataFrame.
    :type ctab_file: str
    :param gtmseg_file: The path to the .gtmseg file to be read. The data from this file is added as columns to the gtm DataFrame.
    :type gtmseg_file: str

    :returns: Path to output .tsv file with a similar name as the input .gtm file.
    :rtype: str
    """

    import pandas as pd
    import numpy as np
    import json
    import nibabel as nib

    gtm_stats = pd.read_csv(
        gtm_stats,
        header=None,
        delim_whitespace=True,
        usecols=[1, 2, 4],
        names=["index", "name", "volume_mm3"],
    )

    # Read the .gtm file into a DataFrame
    in_file_nib = nib.load(in_file)
    x, y, z, t = in_file_nib.get_fdata().shape
    in_file_data = in_file_nib.get_fdata().reshape(x, t).T

    in_file_df = pd.DataFrame(in_file_data, columns=gtm_stats["name"])

    # Load the .json file
    with open(json_file, "r") as jf:
        data = json.load(jf)

    # Convert the 'FrameTimesStart' and 'FrameDuration' lists to numpy arrays and insert them as the first and second columns in gtm_df
    in_file_df.insert(0, "frame_start", np.array(data["FrameTimesStart"]))
    in_file_df.insert(
        1,
        "frame_end",
        np.array(data["FrameTimesStart"]) + np.array(data["FrameDuration"]),
    )

    # Create the output .tsv file name
    if pvc_dir == "nopvc":
        tsv_file = in_file.replace("nopvc.nii.gz", "seg-gtm_desc-preproc_tacs.tsv")
    elif pvc_dir == "agtm":
        tsv_file = in_file.replace(
            "gtm.nii.gz", "pvc-agtm_seg-gtm_desc-preproc_tacs.tsv"
        )

    # Write the DataFrame to the .tsv file (without the index)
    in_file_df.to_csv(tsv_file, sep="\t", index=False)

    return tsv_file


def gtm_to_dsegtsv(gtm_stats):

    import pandas as pd
    import numpy as np
    import json

    gtm_df = pd.read_csv(
        gtm_stats,
        header=None,
        delim_whitespace=True,
        usecols=[1, 2],
        names=["index", "name"],
    )

    # Create the output file name by replacing '.stats' with '.tsv' in the input file name.
    tsv_file = gtm_stats.replace("gtm.stats.dat", "seg-gtm_desc-preproc_dseg.tsv")

    # Write the new DataFrame to the output file.
    # We use a tab separator, and we don't write the index.
    gtm_df.to_csv(tsv_file, sep="\t", index=False)

    # Return the output file name.
    return tsv_file


def limbic_to_dsegtsv(out_stats):

    import pandas as pd
    import numpy as np
    import json

    gtm_df = pd.read_csv(
        out_stats,
        header=None,
        comment="#",
        delim_whitespace=True,
        usecols=[1, 4],
        names=["index", "name"],
    )

    # Create the output file name by replacing '.stats' with '.tsv' in the input file name.
    tsv_file = out_stats.replace(".stats", ".tsv")

    # Write the new DataFrame to the output file.
    # We use a tab separator, and we don't write the index.
    gtm_df.to_csv(tsv_file, sep="\t", index=False)

    # Return the output file name.
    return tsv_file


def limbic_to_stats(out_stats):
    """
    This function reads a 'summary.stats' file, transforms the data, and saves it as a '.tsv' file.

    :param summary_file: The path to the input '.stats' file.
    :type summary_file: str

    :returns: The path to the output '.tsv' file.
    :rtype: str
    """

    import pandas as pd

    # Read the 'summary.stats' file into a DataFrame.
    # We only take the 4th and 5th columns (0-indexed), which we name 'volume_mm3' and 'name'.
    # Lines starting with '#' are ignored.
    summary_df = pd.read_csv(
        out_stats,
        comment="#",
        header=None,
        delim_whitespace=True,
        usecols=[1, 3, 4],
        names=["index", "volume_mm3", "name"],
    )

    # Create a new DataFrame where each row of 'summary_df' is a column.
    # The column names in the new DataFrame are taken from the 'name' column of 'summary_df',
    # and the values are taken from the 'volume_mm3' column of 'summary_df'.
    # summary_df_output = pd.DataFrame([summary_df['volume_mm3'].to_list()], columns=summary_df['name'].to_list())

    # Create the output file name by replacing '.stats' with '.tsv' in the input file name.
    tsv_file = out_stats.replace("_dseg.stats", "_morph.tsv")

    # Write the new DataFrame to the output file.
    # We use a tab separator, and we don't write the index.
    summary_df.rename(columns={"volume_mm3": "volume-mm3"}, inplace=True)
    summary_df = summary_df[["index", "name", "volume-mm3"]]
    summary_df.to_csv(tsv_file, sep="\t", index=False)

    # Return the output file name.
    return tsv_file


def plot_reg(fixed_image, moving_image):
    from niworkflows.viz.notebook import display
    import os

    display(fixed_image, moving_image, fixed_label="T1w", moving_label="PET")

    orig_svg_file = os.path.join(os.getcwd(), "report.svg")
    out_svg_file = orig_svg_file.replace("report", "from-pet_to-t1w_reg")

    os.rename(orig_svg_file, out_svg_file)

    return out_svg_file
