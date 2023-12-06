Node: subject_02_wf (convert_brainmask (freesurfer)
===================================================


 Hierarchy : petprep_extract_tacs_wf.subject_02_wf.convert_brainmask
 Exec ID : convert_brainmask.a1


Original Inputs
---------------


* apply_inv_transform : <undefined>
* apply_transform : <undefined>
* args : <undefined>
* ascii : <undefined>
* autoalign_matrix : <undefined>
* color_file : <undefined>
* conform : <undefined>
* conform_min : <undefined>
* conform_size : <undefined>
* crop_center : <undefined>
* crop_gdf : <undefined>
* crop_size : <undefined>
* cut_ends : <undefined>
* cw256 : <undefined>
* devolve_transform : <undefined>
* drop_n : <undefined>
* environ : {'SUBJECTS_DIR': '/Applications/freesurfer/7.4.1/subjects'}
* fill_parcellation : <undefined>
* force_ras : <undefined>
* frame : <undefined>
* frame_subsample : <undefined>
* fwhm : <undefined>
* in_center : <undefined>
* in_file : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer/sub-02/mri/brainmask.mgz
* in_i_dir : <undefined>
* in_i_size : <undefined>
* in_info : <undefined>
* in_j_dir : <undefined>
* in_j_size : <undefined>
* in_k_dir : <undefined>
* in_k_size : <undefined>
* in_like : <undefined>
* in_matrix : <undefined>
* in_orientation : <undefined>
* in_scale : <undefined>
* in_stats : <undefined>
* in_type : <undefined>
* invert_contrast : <undefined>
* midframe : <undefined>
* no_change : <undefined>
* no_scale : <undefined>
* no_translate : <undefined>
* no_write : <undefined>
* out_center : <undefined>
* out_datatype : <undefined>
* out_file : space-T1w_desc-brain_mask.nii.gz
* out_i_count : <undefined>
* out_i_dir : <undefined>
* out_i_size : <undefined>
* out_info : <undefined>
* out_j_count : <undefined>
* out_j_dir : <undefined>
* out_j_size : <undefined>
* out_k_count : <undefined>
* out_k_dir : <undefined>
* out_k_size : <undefined>
* out_matrix : <undefined>
* out_orientation : <undefined>
* out_scale : <undefined>
* out_stats : <undefined>
* out_type : <undefined>
* parse_only : <undefined>
* read_only : <undefined>
* reorder : <undefined>
* resample_type : <undefined>
* reslice_like : <undefined>
* sdcm_list : <undefined>
* skip_n : <undefined>
* slice_bias : <undefined>
* slice_crop : <undefined>
* slice_reverse : <undefined>
* smooth_parcellation : <undefined>
* sphinx : <undefined>
* split : <undefined>
* status_file : <undefined>
* subject_name : <undefined>
* subjects_dir : /Applications/freesurfer/7.4.1/subjects
* te : <undefined>
* template_info : <undefined>
* template_type : <undefined>
* ti : <undefined>
* tr : <undefined>
* unwarp_gradient : <undefined>
* vox_size : <undefined>
* zero_ge_z_offset : <undefined>
* zero_outlines : <undefined>


Execution Inputs
----------------


* apply_inv_transform : <undefined>
* apply_transform : <undefined>
* args : <undefined>
* ascii : <undefined>
* autoalign_matrix : <undefined>
* color_file : <undefined>
* conform : <undefined>
* conform_min : <undefined>
* conform_size : <undefined>
* crop_center : <undefined>
* crop_gdf : <undefined>
* crop_size : <undefined>
* cut_ends : <undefined>
* cw256 : <undefined>
* devolve_transform : <undefined>
* drop_n : <undefined>
* environ : {'SUBJECTS_DIR': '/Applications/freesurfer/7.4.1/subjects'}
* fill_parcellation : <undefined>
* force_ras : <undefined>
* frame : <undefined>
* frame_subsample : <undefined>
* fwhm : <undefined>
* in_center : <undefined>
* in_file : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer/sub-02/mri/brainmask.mgz
* in_i_dir : <undefined>
* in_i_size : <undefined>
* in_info : <undefined>
* in_j_dir : <undefined>
* in_j_size : <undefined>
* in_k_dir : <undefined>
* in_k_size : <undefined>
* in_like : <undefined>
* in_matrix : <undefined>
* in_orientation : <undefined>
* in_scale : <undefined>
* in_stats : <undefined>
* in_type : <undefined>
* invert_contrast : <undefined>
* midframe : <undefined>
* no_change : <undefined>
* no_scale : <undefined>
* no_translate : <undefined>
* no_write : <undefined>
* out_center : <undefined>
* out_datatype : <undefined>
* out_file : space-T1w_desc-brain_mask.nii.gz
* out_i_count : <undefined>
* out_i_dir : <undefined>
* out_i_size : <undefined>
* out_info : <undefined>
* out_j_count : <undefined>
* out_j_dir : <undefined>
* out_j_size : <undefined>
* out_k_count : <undefined>
* out_k_dir : <undefined>
* out_k_size : <undefined>
* out_matrix : <undefined>
* out_orientation : <undefined>
* out_scale : <undefined>
* out_stats : <undefined>
* out_type : <undefined>
* parse_only : <undefined>
* read_only : <undefined>
* reorder : <undefined>
* resample_type : <undefined>
* reslice_like : <undefined>
* sdcm_list : <undefined>
* skip_n : <undefined>
* slice_bias : <undefined>
* slice_crop : <undefined>
* slice_reverse : <undefined>
* smooth_parcellation : <undefined>
* sphinx : <undefined>
* split : <undefined>
* status_file : <undefined>
* subject_name : <undefined>
* subjects_dir : /Applications/freesurfer/7.4.1/subjects
* te : <undefined>
* template_info : <undefined>
* template_type : <undefined>
* ti : <undefined>
* tr : <undefined>
* unwarp_gradient : <undefined>
* vox_size : <undefined>
* zero_ge_z_offset : <undefined>
* zero_outlines : <undefined>


Execution Outputs
-----------------


* out_file : /Users/martinnorgaard/Dropbox/Mac/Documents/GitHub/petprep_extract_tacs/data/petprep_extract_tacs_wf/subject_02_wf/_pet_file_sub-02_ses-blocked_pet/convert_brainmask/space-T1w_desc-brain_mask.nii.gz


Runtime info
------------


* cmdline : mri_convert --input_volume /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer/sub-02/mri/brainmask.mgz --output_volume space-T1w_desc-brain_mask.nii.gz
* duration : 0.649006
* hostname : martinnoergaard.local
* prev_wd : /Users/martinnorgaard/Dropbox/Mac/Documents/GitHub/petprep_extract_tacs
* working_dir : /Users/martinnorgaard/Dropbox/Mac/Documents/GitHub/petprep_extract_tacs/data/petprep_extract_tacs_wf/subject_02_wf/_pet_file_sub-02_ses-blocked_pet/convert_brainmask


Terminal output
~~~~~~~~~~~~~~~


 


Terminal - standard output
~~~~~~~~~~~~~~~~~~~~~~~~~~


 mri_convert --input_volume /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer/sub-02/mri/brainmask.mgz --output_volume space-T1w_desc-brain_mask.nii.gz 
reading from /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data/derivatives/freesurfer/sub-02/mri/brainmask.mgz...
TR=0.00, TE=0.00, TI=0.00, flip angle=0.00
i_ras = (-1, 9.31323e-10, 0)
j_ras = (0, 7.45058e-09, -1)
k_ras = (-9.31323e-10, 1, 0)
writing to space-T1w_desc-brain_mask.nii.gz...


Terminal - standard error
~~~~~~~~~~~~~~~~~~~~~~~~~


 


Environment
~~~~~~~~~~~


* CONDA_DEFAULT_ENV : petprep_extract_tacs
* CONDA_EXE : /Users/martinnorgaard/anaconda3/bin/conda
* CONDA_PREFIX : /Users/martinnorgaard/anaconda3/envs/petprep_extract_tacs
* CONDA_PREFIX_1 : /Users/martinnorgaard/anaconda3
* CONDA_PROMPT_MODIFIER : (petprep_extract_tacs) 
* CONDA_PYTHON_EXE : /Users/martinnorgaard/anaconda3/bin/python
* CONDA_SHLVL : 2
* DISPLAY : /private/tmp/com.apple.launchd.jikPtoX4Vp/org.xquartz:0
* DYLD_LIBRARY_PATH : /Applications/freesurfer/7.4.1/lib/gcc/lib:/opt/X11/lib/flat_namespace
* FIX_VERTEX_AREA : 
* FMRI_ANALYSIS_DIR : /Applications/freesurfer/7.4.1/fsfast
* FREESURFER : /Applications/freesurfer/7.4.1
* FREESURFER_HOME : /Applications/freesurfer/7.4.1
* FSFAST_HOME : /Applications/freesurfer/7.4.1/fsfast
* FSF_OUTPUT_FORMAT : nii.gz
* FSLDIR : /opt/fsl
* FSLGECUDAQ : cuda.q
* FSLLOCKDIR : 
* FSLMACHINELIST : 
* FSLMULTIFILEQUIT : TRUE
* FSLOUTPUTTYPE : NIFTI_GZ
* FSLREMOTECALL : 
* FSLTCLSH : /opt/fsl/bin/fsltclsh
* FSLWISH : /opt/fsl/bin/fslwish
* FS_OVERRIDE : 0
* FUNCTIONALS_DIR : /Applications/freesurfer/7.4.1/sessions
* HOME : /Users/martinnorgaard
* HOMEBREW_CELLAR : /opt/homebrew/Cellar
* HOMEBREW_PREFIX : /opt/homebrew
* HOMEBREW_REPOSITORY : /opt/homebrew
* INFOPATH : /opt/homebrew/share/info:
* LC_CTYPE : UTF-8
* LOCAL_DIR : /Applications/freesurfer/7.4.1/local
* LOGNAME : martinnorgaard
* MANPATH : /opt/homebrew/share/man:
* MINC_BIN_DIR : /Applications/freesurfer/7.4.1/mni/bin
* MINC_LIB_DIR : /Applications/freesurfer/7.4.1/mni/lib
* MNI_DATAPATH : /Applications/freesurfer/7.4.1/mni/data
* MNI_DIR : /Applications/freesurfer/7.4.1/mni
* MNI_PERL5LIB : /Applications/freesurfer/7.4.1/mni/lib/../Library/Perl/Updates/5.12.3
* NIPYPE_NO_ET : 1
* OLDPWD : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs/data
* OS : Darwin
* PATH : /Users/martinnorgaard/anaconda3/envs/petprep_extract_tacs/bin:/Users/martinnorgaard/anaconda3/condabin:/opt/homebrew/bin:/opt/homebrew/sbin:/opt/fsl/bin:/usr/local/bin:/Applications/freesurfer/7.4.1/bin:/Applications/freesurfer/7.4.1/fsfast/bin:/Applications/freesurfer/7.4.1/mni/bin:/Applications/CMake.app/Contents/bin:/usr/local/ants/bin:/usr/local/infomap:/Applications/AIR5.3.0/bin:/Users/martinnorgaard/Documents/Work/Code/volio/mriwarp-1.52:/Applications/Octave-6.3.0.app/Contents/MacOS/applet:/Applications/PETPVC-1.2.10/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/X11/bin:/Library/Apple/usr/bin:/Users/martinnorgaard/afni
* PERL5LIB : /Applications/freesurfer/7.4.1/mni/lib/../Library/Perl/Updates/5.12.3
* PS1 : (petprep_extract_tacs) $ 
* PWD : /Users/martinnorgaard/Documents/GitHub/petprep_extract_tacs
* SHELL : /bin/bash
* SHLVL : 1
* SSH_AUTH_SOCK : /private/tmp/com.apple.launchd.gYwZbsMErK/Listeners
* SUBJECTS_DIR : /Applications/freesurfer/7.4.1/subjects
* TERM : xterm-256color
* TERM_PROGRAM : Apple_Terminal
* TERM_PROGRAM_VERSION : 450
* TERM_SESSION_ID : CAF401A8-796A-4896-B0EC-497DA71F3377
* TMPDIR : /var/folders/0d/tx6_gy7951749z57rjjkkl_m0000gn/T/
* USER : martinnorgaard
* XPC_FLAGS : 0x0
* XPC_SERVICE_NAME : 0
* _ : /Users/martinnorgaard/anaconda3/envs/petprep_extract_tacs/bin/python3
* _CE_CONDA : 
* _CE_M : 
* __CFBundleIdentifier : com.apple.Terminal
* __CF_USER_TEXT_ENCODING : 0x1F5:0x0:0x9

