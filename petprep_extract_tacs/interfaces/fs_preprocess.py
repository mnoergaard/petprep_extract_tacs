import os
import os.path as op
from glob import glob
import shutil
import sys

import numpy as np
from nibabel import load

from nipype import logging, LooseVersion
from nipype.utils.filemanip import fname_presuffix, check_depends
from nipype.interfaces.io import FreeSurferSource
from nipype.interfaces.base import (
    TraitedSpec,
    File,
    traits,
    Directory,
    InputMultiPath,
    OutputMultiPath,
    CommandLine,
    CommandLineInputSpec,
    isdefined,
)
from nipype.interfaces.freesurfer.base import (
    FSCommand,
    FSTraitedSpec,
    FSTraitedSpecOpenMP,
    FSCommandOpenMP,
    Info,
)
from nipype.interfaces.freesurfer.utils import copy2subjdir


class ApplyVolTransformInputSpec(FSTraitedSpec):
    source_file = File(
        exists=True,
        argstr="--mov %s",
        copyfile=False,
        mandatory=True,
        desc="Input volume you wish to transform",
    )
    transformed_file = File(desc="Output volume", argstr="--o %s", genfile=True)
    _targ_xor = ("target_file", "tal", "fs_target")
    target_file = File(
        exists=True,
        argstr="--targ %s",
        xor=_targ_xor,
        desc="Output template volume",
        mandatory=True,
    )
    tal = traits.Bool(
        argstr="--tal",
        xor=_targ_xor,
        mandatory=True,
        desc="map to a sub FOV of MNI305 (with --reg only)",
    )
    tal_resolution = traits.Float(
        argstr="--talres %.10f", desc="Resolution to sample when using tal"
    )
    fs_target = traits.Bool(
        argstr="--fstarg",
        xor=_targ_xor,
        mandatory=True,
        requires=["reg_file"],
        desc="use orig.mgz from subject in regfile as target",
    )
    _reg_xor = (
        "reg_file",
        "lta_file",
        "lta_inv_file",
        "fsl_reg_file",
        "xfm_reg_file",
        "reg_header",
        "mni_152_reg",
        "subject",
    )
    reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr="--reg %s",
        mandatory=True,
        desc="tkRAS-to-tkRAS matrix   (tkregister2 format)",
    )
    lta_file = File(
        exists=True,
        xor=_reg_xor,
        argstr="--lta %s",
        mandatory=True,
        desc="Linear Transform Array file",
    )
    lta_inv_file = File(
        exists=True,
        xor=_reg_xor,
        argstr="--lta-inv %s",
        mandatory=True,
        desc="LTA, invert",
    )
    reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr="--reg %s",
        mandatory=True,
        desc="tkRAS-to-tkRAS matrix   (tkregister2 format)",
    )
    fsl_reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr="--fsl %s",
        mandatory=True,
        desc="fslRAS-to-fslRAS matrix (FSL format)",
    )
    xfm_reg_file = File(
        exists=True,
        xor=_reg_xor,
        argstr="--xfm %s",
        mandatory=True,
        desc="ScannerRAS-to-ScannerRAS matrix (MNI format)",
    )
    reg_header = traits.Bool(
        xor=_reg_xor,
        argstr="--regheader",
        mandatory=True,
        desc="ScannerRAS-to-ScannerRAS matrix = identity",
    )
    mni_152_reg = traits.Bool(
        xor=_reg_xor, argstr="--regheader", mandatory=True, desc="target MNI152 space"
    )
    subject = traits.Str(
        xor=_reg_xor,
        argstr="--s %s",
        mandatory=True,
        desc="set matrix = identity and use subject for any templates",
    )
    inverse = traits.Bool(desc="sample from target to source", argstr="--inv")
    interp = traits.Enum(
        "trilin",
        "nearest",
        "cubic",
        argstr="--interp %s",
        desc="Interpolation method (<trilin> or nearest)",
    )
    no_resample = traits.Bool(
        desc="Do not resample; just change vox2ras matrix", argstr="--no-resample"
    )
    m3z_file = File(
        argstr="--m3z %s",
        desc=(
            "This is the morph to be applied to the volume. "
            "Unless the morph is in mri/transforms (eg.: for "
            "talairach.m3z computed by reconall), you will need "
            "to specify the full path to this morph and use the "
            "--noDefM3zPath flag."
        ),
    )
    no_ded_m3z_path = traits.Bool(
        argstr="--noDefM3zPath",
        requires=["m3z_file"],
        desc=(
            "To be used with the m3z flag. "
            "Instructs the code not to look for the"
            "m3z morph in the default location "
            "(SUBJECTS_DIR/subj/mri/transforms), "
            "but instead just use the path "
            "indicated in --m3z."
        ),
    )

    invert_morph = traits.Bool(
        argstr="--inv-morph",
        requires=["m3z_file"],
        desc=(
            "Compute and use the inverse of the "
            "non-linear morph to resample the input "
            "volume. To be used by --m3z."
        ),
    )


class ApplyVolTransformOutputSpec(TraitedSpec):
    transformed_file = File(exists=True, desc="Path to output file if used normally")


class ApplyVolTransform(FSCommand):
    """Use FreeSurfer mri_vol2vol to apply a transform.

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import ApplyVolTransform
    >>> applyreg = ApplyVolTransform()
    >>> applyreg.inputs.source_file = 'structural.nii'
    >>> applyreg.inputs.reg_file = 'register.dat'
    >>> applyreg.inputs.transformed_file = 'struct_warped.nii'
    >>> applyreg.inputs.fs_target = True
    >>> applyreg.cmdline
    'mri_vol2vol --fstarg --reg register.dat --mov structural.nii --o struct_warped.nii'

    """

    _cmd = "mri_vol2vol"
    input_spec = ApplyVolTransformInputSpec
    output_spec = ApplyVolTransformOutputSpec

    def _get_outfile(self):
        outfile = self.inputs.transformed_file
        if not isdefined(outfile):
            if self.inputs.inverse is True:
                if self.inputs.fs_target is True:
                    src = "orig.mgz"
                else:
                    src = self.inputs.target_file
            else:
                src = self.inputs.source_file
            outfile = fname_presuffix(src, newpath=os.getcwd(), suffix="_warped")
        return outfile

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["transformed_file"] = os.path.abspath(self._get_outfile())
        return outputs

    def _gen_filename(self, name):
        if name == "transformed_file":
            return self._get_outfile()
        return None


class CVSRegisterInputSpec(FSTraitedSpec):
    subject_id = File(
        argstr="--mov %s",
        mandatory=True,
        desc="Subject ID you wish to use CVS register for",
    )
    template_file = File(
        argstr="--template %s",
        desc="FreeSurfer subject name as found in $SUBJECTS_DIR (or --templatedir)",
    )
    mni = traits.Bool(
        argstr="--mni",
        desc="Use the CVS atlas in MNI152 space as a target for registration (as opposed to the default CVS template).",
    )
    cleanall = traits.Bool(
        argstr="--cleanall",
        desc="Remove all intermediate files",
    )


class CVSRegisterOutputSpec(TraitedSpec):
    m3z_file = File(desc="Path to output file if used normally")


class CVSRegister(FSCommand):
    """Use FreeSurfer mri_cvs_register to apply a transform.

    Examples
    --------
    >>> from nipype.interfaces.freesurfer import CVSRegister
    >>> cvsreg = CVSRegister()
    >>> cvsreg.inputs.source_file = 'subject_id'
    >>> cvsreg.inputs.mni = True
    >>> cvsreg.cmdline
    'mri_cvs_register --mov subject_id --mni'
    """

    _cmd = "mri_cvs_register"
    input_spec = CVSRegisterInputSpec
    output_spec = CVSRegisterOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        subj_dir = os.path.abspath(
            self.inputs.subjects_dir + "/" + self.inputs.subject_id + "/cvs/"
        )

        outputs["m3z_file"] = os.path.join(
            subj_dir, "final_CVSmorph_tocvs_avg35_inMNI152.m3z"
        )

        return outputs

    def _gen_filename(self, name):
        if name == "subjects_dir":
            return os.path.abspath(self.inputs.subject_id)
        return None
