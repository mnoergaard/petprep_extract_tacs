import argparse
import os
from pathlib import Path
import glob
import re
import shutil
import json
import pkg_resources
from bids import BIDSLayout
from nipype.interfaces.utility import IdentityInterface, Merge
from nipype.pipeline import Workflow
from nipype import Node, Function, DataSink
from nipype.interfaces.io import SelectFiles
from niworkflows.utils.misc import check_valid_fs_license
from petprep_extract_tacs.utils.pet import create_weighted_average_pet
from nipype.interfaces.freesurfer import MRICoreg, ApplyVolTransform, MRIConvert, Concatenate, SampleToSurface, SurfaceSmooth
from petprep_extract_tacs.interfaces.petsurfer import GTMSeg, GTMPVC
from petprep_extract_tacs.interfaces.segment import SegmentBS, SegmentHA_T1, SegmentThalamicNuclei, MRISclimbicSeg
from petprep_extract_tacs.interfaces.fs_model import SegStats
from petprep_extract_tacs.utils.utils import ctab_to_dsegtsv, avgwf_to_tacs, summary_to_stats, gtm_to_tacs, gtm_stats_to_stats, gtm_to_dsegtsv, limbic_to_dsegtsv, limbic_to_stats, plot_reg, get_opt_fwhm

from petprep_extract_tacs.bids import collect_data

__version__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'version')).read()


def main(args):
    # Check whether BIDS directory exists and instantiate BIDSLayout
    if os.path.exists(args.bids_dir):
        if not args.skip_bids_validator:
            layout = BIDSLayout(args.bids_dir, validate=True)
        else:
            layout = BIDSLayout(args.bids_dir, validate=False)
    else:
        raise Exception('BIDS directory does not exist')

    # Check whether FreeSurfer license is valid
    if check_valid_fs_license() is not True:
        raise Exception('You need a valid FreeSurfer license to proceed!')

    # Get all PET files
    if args.participant_label is None:
        args.participant_label = layout.get(suffix='pet', target='subject', return_type='id')

    # Create derivatives directories
    if args.output_dir is None:
        output_dir = os.path.join(args.bids_dir, 'derivatives', 'petprep_extract_tacs')
    else:
        output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    # Run ANAT workflow
    anat_main = init_anat_wf()
    if anat_main._get_all_nodes():
        anat_main.run(plugin='MultiProc', plugin_args={'n_procs': int(args.n_procs)})

    # Run PET workflow
    main = init_petprep_extract_tacs_wf()
    main.run(plugin='MultiProc', plugin_args={'n_procs': int(args.n_procs)})


    # Loop through directories and store according to PET-BIDS specification
    reg_files = glob.glob(os.path.join(Path(args.bids_dir),'petprep_extract_tacs_wf','datasink','*','from-pet_to-t1w_reg.lta'))

    for idx, x in enumerate(reg_files):
        match_sub_id = re.search(r'sub-([A-Za-z0-9]+)_', reg_files[idx])
        sub_id = match_sub_id.group(1)
        
        match_ses_id = re.search(r'ses-([A-Za-z0-9]+)_', reg_files[idx])

        if match_ses_id:
            ses_id = match_ses_id.group(1)
        else:
            ses_id = None

        match_file_prefix = re.search(r'_pet_file_(.*?)_pet', reg_files[idx])
        file_prefix = match_file_prefix.group(1)

        if ses_id is not None:
            sub_out_dir = Path(os.path.join(output_dir, 'sub-' + sub_id, 'ses-' + ses_id))
        else:
            sub_out_dir = Path(os.path.join(output_dir, 'sub-' + sub_id))

        os.makedirs(sub_out_dir, exist_ok=True)

        # copy all files and add prefix
        for root, dirs, files in os.walk(os.path.dirname(reg_files[idx])):
            for file in files:
                if not file.startswith('.'):
                    shutil.copy(os.path.join(root, file), os.path.join(sub_out_dir, file_prefix + '_' + file))  

    # Remove temp outputs
    shutil.rmtree(os.path.join(args.bids_dir, 'petprep_extract_tacs_wf'))
    if os.path.exists(os.path.join(args.bids_dir, 'anat_wf')):
        shutil.rmtree(os.path.join(args.bids_dir, 'anat_wf'))

def init_anat_wf():
    from bids import BIDSLayout

    layout = BIDSLayout(args.bids_dir, validate=False)

    anat_wf = Workflow(name='anat_wf', base_dir=args.bids_dir)
    anat_wf.config['execution']['remove_unnecessary_outputs'] = 'false'

    # Define the subjects to iterate over
    subject_list = layout.get(return_type='id', target='subject', suffix='pet')

    # Set up the main workflow to iterate over subjects
    for subject_id in subject_list:
        # For each subject, create a subject-specific workflow
        subject_wf = init_single_subject_anat_wf(subject_id)
        anat_wf.add_nodes([subject_wf])

    return anat_wf

def init_single_subject_anat_wf(subject_id):
    from bids import BIDSLayout

    layout = BIDSLayout(args.bids_dir, validate=False)

    # Create a new workflow for this specific subject
    subject_wf = Workflow(name=f'subject_{subject_id}_wf', base_dir=args.bids_dir)
    subject_wf.config['execution']['remove_unnecessary_outputs'] = 'false'

    templates = {'fs_subject_dir': 'derivatives/freesurfer'}

    selectfiles = Node(SelectFiles(templates,
                                   base_directory=args.bids_dir),
    
                       name="select_files")
    
    datasink = Node(DataSink(base_directory = args.bids_dir,
                                container = os.path.join(args.bids_dir,'anat_wf')),
                    name = 'datasink')
    
    if args.gtm is True:
        gtmseg = Node(GTMSeg(subject_id = f'sub-{subject_id}', 
                            out_file = 'space-T1w_desc-gtmseg_dseg.nii.gz',
                            xcerseg = True),
                    name = 'gtmseg')
        
        subject_wf.connect([(selectfiles, gtmseg, [('fs_subject_dir', 'subjects_dir')]),
                            (gtmseg, datasink, [('out_file', 'datasink.@gtmseg_file')])
                            ])

    if args.brainstem is True:
        segment_bs = Node(SegmentBS(subject_id = f'sub-{subject_id}'),
                                name = 'segment_bs')
        
        subject_wf.connect([(selectfiles, segment_bs, [('fs_subject_dir', 'subjects_dir')])
                            ])
        
    if args.thalamicNuclei is True:
        segment_th = Node(SegmentThalamicNuclei(subject_id = f'sub-{subject_id}'),
                            name = 'segment_th')
            
        subject_wf.connect([(selectfiles, segment_th, [('fs_subject_dir', 'subjects_dir')])
                            ])
        
    if args.hippocampusAmygdala is True:
        segment_ha = Node(SegmentHA_T1(subject_id = f'sub-{subject_id}'),
                            name = 'segment_ha')
            
        subject_wf.connect([(selectfiles, segment_ha, [('fs_subject_dir', 'subjects_dir')])
                            ])
    
    return subject_wf

def init_petprep_extract_tacs_wf():
    from bids import BIDSLayout

    layout = BIDSLayout(args.bids_dir, validate=False)

    petprep_extract_tacs_wf = Workflow(name='petprep_extract_tacs_wf', base_dir=args.bids_dir)
    petprep_extract_tacs_wf.config['execution']['remove_unnecessary_outputs'] = 'false'

    # Define the subjects to iterate over
    subject_list = layout.get(return_type='id', target='subject', suffix='pet')

    # Set up the main workflow to iterate over subjects
    for subject_id in subject_list:
        # For each subject, create a subject-specific workflow
        subject_wf = init_single_subject_wf(subject_id)
        petprep_extract_tacs_wf.add_nodes([subject_wf])

    return petprep_extract_tacs_wf


def init_single_subject_wf(subject_id):
    from bids import BIDSLayout

    layout = BIDSLayout(args.bids_dir, validate=False)

    # Create a new workflow for this specific subject
    subject_wf = Workflow(name=f'subject_{subject_id}_wf', base_dir=args.bids_dir)
    subject_wf.config['execution']['remove_unnecessary_outputs'] = 'false'

    subject_data = collect_data(layout,
                            participant_label=subject_id)[0]['pet']

    # This function will strip the extension(s) from a filename
    def strip_extensions(filename):
        while os.path.splitext(filename)[1]:
            filename = os.path.splitext(filename)[0]
        return filename

    # Use os.path.basename to get the last part of the path and then remove the extensions
    cleaned_subject_data = [strip_extensions(os.path.basename(path)) for path in subject_data]

    inputs = Node(IdentityInterface(fields=['pet_file']), name='inputs')
    inputs.iterables = ('pet_file', cleaned_subject_data)

    sessions = layout.get_sessions(subject=subject_id)

    templates = {'pet_file': 's*/pet/*{pet_file}.[n]*' if not sessions else 's*/s*/pet/*{pet_file}.[n]*',
                 'json_file': 's*/pet/*{pet_file}.json' if not sessions else 's*/s*/pet/*{pet_file}.json',
                 'brainmask_file': f'derivatives/freesurfer/sub-{subject_id}/mri/brainmask.mgz',
                 'wm_file': f'derivatives/freesurfer/sub-{subject_id}/mri/wmparc.mgz',
                 'orig_file': f'derivatives/freesurfer/sub-{subject_id}/mri/orig.mgz',
                 'fs_subject_dir': 'derivatives/freesurfer'
                 }

    selectfiles = Node(SelectFiles(templates,
                                   base_directory=args.bids_dir),
                       name="select_files")

    # Define nodes for extraction of tacs

    coreg_pet_to_t1w = Node(MRICoreg(out_lta_file = 'from-pet_to-t1w_reg.lta',
                                     subject_id = f'sub-{subject_id}'),
                       name = 'coreg_pet_to_t1w')
    
    create_time_weighted_average = Node(Function(input_names = ['pet_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = create_weighted_average_pet),
                                   name = 'create_weighted_average_pet')

    move_pet_to_anat = Node(ApplyVolTransform(transformed_file = 'space-T1w_pet.nii.gz'),
                            name = 'move_pet_to_anat')
    
    move_twa_to_anat = Node(ApplyVolTransform(transformed_file = 'space-T1w_desc-twa_pet.nii.gz'),
                            name = 'move_twa_to_anat')
    
    convert_brainmask = Node(MRIConvert(out_file = 'space-T1w_desc-brain_mask.nii.gz'),
                             name = 'convert_brainmask')
    
    plot_registration = Node(Function(input_names = ['fixed_image', 'moving_image'],
                             output_names = ['out_file'],
                             function = plot_reg),
                        name = 'plot_reg')
    
    datasink = Node(DataSink(base_directory = args.bids_dir,
                                container = os.path.join(args.bids_dir,'petprep_extract_tacs_wf')),
                    name = 'datasink')

    subject_wf.connect([(inputs, selectfiles, [('pet_file', 'pet_file')]),
                        (selectfiles, create_time_weighted_average, [('pet_file', 'pet_file')]),
                        (selectfiles, create_time_weighted_average, [('json_file', 'json_file')]),
                        (selectfiles, coreg_pet_to_t1w, [('brainmask_file', 'reference_file')]),
                        (selectfiles, coreg_pet_to_t1w, [('fs_subject_dir', 'subjects_dir')]),
                        (create_time_weighted_average, coreg_pet_to_t1w, [('out_file', 'source_file')]),
                        (coreg_pet_to_t1w, move_pet_to_anat, [('out_lta_file', 'lta_file')]),
                        (selectfiles, move_pet_to_anat, [('brainmask_file', 'target_file')]),
                        (selectfiles, move_pet_to_anat, [('pet_file', 'source_file')]),
                        #(move_pet_to_anat, datasink, [('transformed_file', 'datasink.@transformed_file')]),
                        (coreg_pet_to_t1w, datasink, [('out_lta_file', 'datasink.@out_lta_file')]),
                        (create_time_weighted_average, move_twa_to_anat, [('out_file', 'source_file')]),
                        (selectfiles, move_twa_to_anat, [('brainmask_file', 'target_file')]),
                        (coreg_pet_to_t1w, move_twa_to_anat, [('out_lta_file', 'lta_file')]),
                        #(move_twa_to_anat, datasink, [('transformed_file', 'datasink.@transformed_twa_file')]),
                        (selectfiles, convert_brainmask, [('brainmask_file', 'in_file')]),
                        (convert_brainmask, datasink, [('out_file', 'datasink.@brainmask_file')]),
                        (convert_brainmask, plot_registration, [('out_file', 'fixed_image')]),
                        (move_twa_to_anat, plot_registration, [('transformed_file', 'moving_image')]),
                        (plot_registration, datasink, [('out_file', 'datasink.@plot_reg')])
                        ])
    
    if args.surface is True:
        vol2surf_lh = Node(SampleToSurface(hemi = 'lh',
                                    sampling_method = 'point',
                                    sampling_range = 0.5,
                                    sampling_units = 'frac',
                                    cortex_mask = True,
                                    target_subject = 'fsaverage',
                                    out_file = 'space-fsaverage_hemi-lh_pet.nii.gz'
                                    ),
                        name = 'vol2surf_lh')
                     
        vol2surf_rh = Node(SampleToSurface(hemi = 'rh',
                                    sampling_method = 'point',
                                    sampling_range = 0.5,
                                    sampling_units = 'frac',
                                    cortex_mask = True,
                                    target_subject = 'fsaverage',
                                    out_file = 'space-fsaverage_hemi-rh_pet.nii.gz'
                                    ),
                        name = 'vol2surf_rh')
        
        if args.surface_smooth is not None:
            vol2surf_lh.inputs.smooth_surf = args.surface_smooth
            vol2surf_lh.inputs.out_file = f'space-fsaverage_hemi-lh_desc-sm{args.surface_smooth}_pet.nii.gz'
            vol2surf_rh.inputs.smooth_surf = args.surface_smooth
            vol2surf_rh.inputs.out_file = f'space-fsaverage_hemi-rh_desc-sm{args.surface_smooth}_pet.nii.gz'
            
         
        subject_wf.connect([(selectfiles, vol2surf_lh, [('pet_file', 'source_file')]),
                            (selectfiles, vol2surf_lh, [('fs_subject_dir', 'subjects_dir')]),
                            (coreg_pet_to_t1w, vol2surf_lh, [('out_lta_file', 'reg_file')]),
                            (vol2surf_lh, datasink, [('out_file', 'datasink.@lh_pet')]),
                            (selectfiles, vol2surf_rh, [('pet_file', 'source_file')]),
                            (selectfiles, vol2surf_rh, [('fs_subject_dir', 'subjects_dir')]),
                            (coreg_pet_to_t1w, vol2surf_rh, [('out_lta_file', 'reg_file')]),
                            (vol2surf_rh, datasink, [('out_file', 'datasink.@rh_pet')])
                            ])
        
    if args.volume is True:
        vol2vol = Node(ApplyVolTransform(transformed_file = 'space-mni305_pet.nii.gz',
                                          tal = True,
                                          tal_resolution = 2),
                            name = 'vol2vol')
         
        subject_wf.connect([(selectfiles, vol2vol, [('pet_file', 'source_file')]),
                            (selectfiles, vol2vol, [('fs_subject_dir', 'subjects_dir')]),
                            (coreg_pet_to_t1w, vol2vol, [('out_lta_file', 'lta_file')]),
                            (vol2vol, datasink, [('transformed_file', 'datasink.@mni305_pet')])
                            ])
        
        if args.volume_smooth is not None:
            smooth_vol = Node(MRIConvert(out_file = f'space-mni305_desc-sm{args.volume_smooth}_pet.nii.gz',
                                         fwhm = args.volume_smooth),
                                         name = 'smooth_vol')
            
            subject_wf.connect([(vol2vol, smooth_vol, [('transformed_file', 'in_file')]),
                                (smooth_vol, datasink, [('out_file', 'datasink.@mni305_sm_pet')])
                                ])

    
    if args.gtm is True:
            
            templates.update({'gtm_file': f'derivatives/freesurfer/sub-{subject_id}/mri/gtmseg.mgz'})
        
            gtmpvc = Node(GTMPVC(default_seg_merge = True,
                                auto_mask = (1,0.1),
                                no_pvc = True,
                                pvc_dir = 'nopvc',
                                no_rescale = True),
                        name = 'gtmpvc')
            
            create_gtmseg_tacs = Node(Function(input_names = ['in_file', 'json_file', 'gtm_stats', 'pvc_dir'],
                                                output_names = ['out_file'],
                                                function = gtm_to_tacs),
                                    name = 'create_gtmseg_tacs')
            
            create_gtmseg_tacs.inputs.pvc_dir = gtmpvc.inputs.pvc_dir
            
            create_gtmseg_stats = Node(Function(input_names = ['gtm_stats'],
                                                output_names = ['out_file'],
                                                function = gtm_stats_to_stats),
                                    name = 'create_gtmseg_stats')
            
            create_gtmseg_dsegtsv = Node(Function(input_names = ['gtm_stats'],
                                                    output_names = ['out_file'],
                                                    function = gtm_to_dsegtsv),
                                            name = 'create_gtmseg_dsegtsv')
            
            convert_gtmseg_file = Node(MRIConvert(out_file = 'desc-gtmseg_dseg.nii.gz'),
                                    name = 'convert_gtmseg_file')
            
            subject_wf.connect([(selectfiles, gtmpvc, [('pet_file', 'in_file')]),
                            (selectfiles, gtmpvc, [('gtm_file', 'segmentation')]),
                            (coreg_pet_to_t1w, gtmpvc, [('out_lta_file', 'reg_file')]),
                            (gtmpvc, create_gtmseg_tacs, [('nopvc_file', 'in_file')]),
                            (gtmpvc, create_gtmseg_tacs, [('gtm_stats', 'gtm_stats')]),
                            (selectfiles, create_gtmseg_tacs, [('json_file', 'json_file')]),
                            (create_gtmseg_tacs, datasink, [('out_file', 'datasink.@gtmseg_tacs')]),
                            (gtmpvc, create_gtmseg_stats, [('gtm_stats', 'gtm_stats')]),
                            (create_gtmseg_stats, datasink, [('out_file', 'datasink.@gtmseg_stats')]),
                            (selectfiles, convert_gtmseg_file, [('gtm_file', 'in_file')]),
                            (convert_gtmseg_file, datasink, [('out_file', 'datasink.@gtmseg_file')]),
                            (gtmpvc, create_gtmseg_dsegtsv, [('gtm_stats', 'gtm_stats')]),
                            (create_gtmseg_dsegtsv, datasink, [('out_file', 'datasink.@gtmseg_dsegtsv')])
                            ])
            
    if args.agtm is True and args.psf is not None:
                
                templates.update({'gtm_file': f'derivatives/freesurfer/sub-{subject_id}/mri/gtmseg.mgz'})
                
                agtmpvc_init = Node(GTMPVC(auto_mask = (1,0.1),
                                        num_threads = 1,
                                        opt_seg_merge = True,
                                        optimization_schema = '3D_MB',
                                        psf = args.psf,
                                        opt_tol = (4, 10e-6, .02),
                                        opt_brain = True,
                                        pvc_dir = 'agtm',
                                        no_rescale = True),
                                name = 'agtmpvc_init')
                
                agtmpvc = Node(GTMPVC(default_seg_merge = True,
                                        auto_mask = (1,0.1),
                                        pvc_dir = 'agtm',
                                        no_rescale = True),
                                name = 'agtmpvc')
                
                opt_fwhm = Node(Function(input_names=['opt_params'],
                                        output_names=['fwhm_x', 'fwhm_y', 'fwhm_z'],
                                        function=get_opt_fwhm),
                                name="opt_fwhm")
                
                create_agtmseg_tacs = Node(Function(input_names = ['in_file', 'json_file', 'gtm_stats', 'pvc_dir'],
                                                        output_names = ['out_file'],
                                                        function = gtm_to_tacs),
                                            name = 'create_agtmseg_tacs')
                
                create_agtmseg_tacs.inputs.pvc_dir = agtmpvc.inputs.pvc_dir
                    
                subject_wf.connect([(create_time_weighted_average, agtmpvc_init, [('out_file', 'in_file')]),
                                    (selectfiles, agtmpvc_init, [('gtm_file', 'segmentation')]),
                                    (coreg_pet_to_t1w, agtmpvc_init, [('out_lta_file', 'reg_file')]),
                                    (agtmpvc_init, opt_fwhm, [('opt_params', 'opt_params')]),
                                    (opt_fwhm, agtmpvc, [('fwhm_x', 'psf_col'),
                                                            ('fwhm_y', 'psf_row'),
                                                            ('fwhm_z', 'psf_slice')]),
                                    (selectfiles, agtmpvc, [('pet_file', 'in_file')]),
                                    (selectfiles, agtmpvc, [('gtm_file', 'segmentation')]),
                                    (coreg_pet_to_t1w, agtmpvc, [('out_lta_file', 'reg_file')]),
                                    (agtmpvc, create_agtmseg_tacs, [('gtm_file', 'in_file')]),
                                    (agtmpvc, create_agtmseg_tacs, [('gtm_stats', 'gtm_stats')]),
                                    (selectfiles, create_agtmseg_tacs, [('json_file', 'json_file')]),
                                    (create_agtmseg_tacs, datasink, [('out_file', 'datasink.@agtmseg_tacs')])
                                    ])
            
    if args.brainstem is True:
            
            templates.update({'bs_labels_voxel': f'derivatives/freesurfer/sub-{subject_id}/mri/brainstemSsLabels.v13.FSvoxelSpace.mgz'})

            segment_bs = Node(SegmentBS(subject_id = f'sub-{subject_id}'),
                                name = 'segment_bs')
            
            segstats_bs = Node(SegStats(exclude_id = 0,
                                        default_color_table = True,
                                        avgwf_txt_file = 'desc-brainstem_tacs.txt',
                                        ctab_out_file = 'desc-brainstem_dseg.ctab',
                                        summary_file = 'desc-brainstem_stats.txt'),
                                name = 'segstats_bs')
            
            create_bs_tacs = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = avgwf_to_tacs),
                                    name = 'create_bs_tacs')
            
            create_bs_stats = Node(Function(input_names = ['summary_file'],
                                            output_names = ['out_file'],
                                            function = summary_to_stats),
                                    name = 'create_bs_stats')
            
            create_bs_dsegtsv = Node(Function(input_names = ['ctab_file'],
                                            output_names = ['out_file'],
                                            function = ctab_to_dsegtsv),
                                        name = 'create_bs_dsegtsv')
            
            convert_bs_seg_file = Node(MRIConvert(out_file = 'desc-brainstem_dseg.nii.gz'),
                                    name = 'convert_bs_seg_file')
            
            subject_wf.connect([(selectfiles, segstats_bs, [('bs_labels_voxel', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_bs, [('transformed_file', 'in_file')]),
                            (segstats_bs, create_bs_tacs, [('avgwf_txt_file', 'avgwf_file'),
                                                            ('ctab_out_file', 'ctab_file')]),
                            (selectfiles, create_bs_tacs, [('json_file', 'json_file')]),
                            (segstats_bs, create_bs_stats, [('summary_file', 'summary_file')]),
                            (segstats_bs, create_bs_dsegtsv, [('ctab_out_file', 'ctab_file')]),
                            (selectfiles, convert_bs_seg_file, [('bs_labels_voxel', 'in_file')]),
                            (create_bs_tacs, datasink, [('out_file', 'datasink')]),
                            (create_bs_stats, datasink, [('out_file', 'datasink.@bs_stats')]),
                            (create_bs_dsegtsv, datasink, [('out_file', 'datasink.@bs_dseg')]),
                            (convert_bs_seg_file, datasink, [('out_file', 'datasink.@bs_segmentation_file')])
                            ])
            
    if args.thalamicNuclei is True:       

            templates.update({'thalamic_labels_voxel': f'derivatives/freesurfer/sub-{subject_id}/mri/ThalamicNuclei.v13.T1.FSvoxelSpace.mgz'})
     
            segstats_th = Node(SegStats(exclude_id = 0,
                                        default_color_table = True,
                                        avgwf_txt_file = 'desc-thalamus_tacs.txt',
                                        ctab_out_file = 'desc-thalamus_dseg.ctab',
                                        summary_file = 'desc-thalamus_stats.txt'),
                                name = 'segstats_th')
            
            create_th_tacs = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = avgwf_to_tacs),
                                    name = 'create_th_tacs')
            
            create_th_stats = Node(Function(input_names = ['summary_file'],
                                            output_names = ['out_file'],
                                            function = summary_to_stats),
                                    name = 'create_th_stats')
            
            create_th_dsegtsv = Node(Function(input_names = ['ctab_file'],
                                            output_names = ['out_file'],
                                            function = ctab_to_dsegtsv),
                                        name = 'create_th_dsegtsv')
            
            convert_th_seg_file = Node(MRIConvert(out_file = 'desc-thalamus_dseg.nii.gz'),
                                    name = 'convert_th_seg_file')
            
            subject_wf.connect([(selectfiles, segstats_th, [('thalamic_labels_voxel', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_th, [('transformed_file', 'in_file')]),
                            (segstats_th, create_th_tacs, [('avgwf_txt_file', 'avgwf_file'),
                                                            ('ctab_out_file', 'ctab_file')]),
                            (selectfiles, create_th_tacs, [('json_file', 'json_file')]),
                            (segstats_th, create_th_stats, [('summary_file', 'summary_file')]),
                            (segstats_th, create_th_dsegtsv, [('ctab_out_file', 'ctab_file')]),
                            (selectfiles, convert_th_seg_file, [('thalamic_labels_voxel', 'in_file')]),
                            (create_th_tacs, datasink, [('out_file', 'datasink.@th_tacs')]),
                            (create_th_stats, datasink, [('out_file', 'datasink.@th_stats')]),
                            (create_th_dsegtsv, datasink, [('out_file', 'datasink.@th_dseg')]),
                            (convert_th_seg_file, datasink, [('out_file', 'datasink.@th_segmentation_file')])
                            ])
            
    if args.hippocampusAmygdala is True:   
            
            templates.update({'lh_hippoAmygLabels': f'derivatives/freesurfer/sub-{subject_id}/mri/lh.hippoAmygLabels-T1.v22.FSvoxelSpace.mgz',
                 'rh_hippoAmygLabels': f'derivatives/freesurfer/sub-{subject_id}/mri/rh.hippoAmygLabels-T1.v22.FSvoxelSpace.mgz'})
    
            segstats_ha_lh = Node(SegStats(exclude_id = 0,
                                        default_color_table = True,
                                        avgwf_txt_file = 'hemi-L_desc-hippocampusAmygdala_tacs.txt',
                                        ctab_out_file = 'hemi-L_desc-hippocampusAmygdala_dseg.ctab',
                                        summary_file = 'hemi-L_desc-hippocampusAmygdala_stats.txt'),
                                name = 'segstats_ha_lh')
            
            create_ha_tacs_lh = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = avgwf_to_tacs),
                                    name = 'create_ha_tacs_lh')
            
            create_ha_stats_lh = Node(Function(input_names = ['summary_file'],
                                            output_names = ['out_file'],
                                            function = summary_to_stats),
                                    name = 'create_ha_stats_lh')
            
            create_ha_dsegtsv_lh = Node(Function(input_names = ['ctab_file'],
                                            output_names = ['out_file'],
                                            function = ctab_to_dsegtsv),
                                        name = 'create_ha_dsegtsv_lh')
            
            convert_ha_seg_file_lh = Node(MRIConvert(out_file = 'hemi-L_desc-hippocampusAmygdala_dseg.nii.gz'),
                                    name = 'convert_ha_seg_file_lh')
            
            
            segstats_ha_rh = Node(SegStats(exclude_id = 0,
                                        default_color_table = True,
                                        avgwf_txt_file = 'hemi-R_desc-hippocampusAmygdala_tacs.txt',
                                        ctab_out_file = 'hemi-R_desc-hippocampusAmygdala_dseg.ctab',
                                        summary_file = 'hemi-R_desc-hippocampusAmygdala_stats.txt'),
                                name = 'segstats_ha_rh')
            
            create_ha_tacs_rh = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = avgwf_to_tacs),
                                    name = 'create_ha_tacs_rh')
            
            create_ha_stats_rh = Node(Function(input_names = ['summary_file'],
                                            output_names = ['out_file'],
                                            function = summary_to_stats),
                                    name = 'create_ha_stats_rh')
            
            create_ha_dsegtsv_rh = Node(Function(input_names = ['ctab_file'],
                                            output_names = ['out_file'],
                                            function = ctab_to_dsegtsv),
                                        name = 'create_ha_dsegtsv_rh')
            
            convert_ha_seg_file_rh = Node(MRIConvert(out_file = 'hemi-R_desc-hippocampusAmygdala_dseg.nii.gz'),
                                    name = 'convert_ha_seg_file_rh')
            
            merge_seg_files = Node(Merge(2), 
                                name='merge')

            combine_ha_lr_dseg = Node(Concatenate(concatenated_file = 'desc-hippocampusAmygdala_dseg.nii.gz',
                                                combine = True),
                                    name = 'combine_ha_lr_dseg')
            
            segstats_ha = Node(SegStats(exclude_id = 0,
                                        default_color_table = True,
                                        avgwf_txt_file = 'desc-hippocampusAmygdala_tacs.txt',
                                        ctab_out_file = 'desc-hippocampusAmygdala_dseg.ctab',
                                        summary_file = 'desc-hippocampusAmygdala_stats.txt'),
                                name = 'segstats_ha')
            
            create_ha_tacs = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = avgwf_to_tacs),
                                    name = 'create_ha_tacs')
            
            create_ha_stats = Node(Function(input_names = ['summary_file'],
                                            output_names = ['out_file'],
                                            function = summary_to_stats),
                                    name = 'create_ha_stats')
            
            create_ha_dsegtsv = Node(Function(input_names = ['ctab_file'],
                                            output_names = ['out_file'],
                                            function = ctab_to_dsegtsv),
                                        name = 'create_ha_dsegtsv')
            
            subject_wf.connect([(selectfiles, segstats_ha_lh, [('lh_hippoAmygLabels', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_ha_lh, [('transformed_file', 'in_file')]),
                            (segstats_ha_lh, create_ha_tacs_lh, [('avgwf_txt_file', 'avgwf_file'),
                                                            ('ctab_out_file', 'ctab_file')]),
                            (selectfiles, create_ha_tacs_lh, [('json_file', 'json_file')]),
                            (segstats_ha_lh, create_ha_stats_lh, [('summary_file', 'summary_file')]),
                            (segstats_ha_lh, create_ha_dsegtsv_lh, [('ctab_out_file', 'ctab_file')]),
                            (selectfiles, convert_ha_seg_file_lh, [('lh_hippoAmygLabels', 'in_file')]),
                            (create_ha_tacs_lh, datasink, [('out_file', 'datasink.@ha_tacs_lh')]),
                            (create_ha_stats_lh, datasink, [('out_file', 'datasink.@ha_stats_lh')]),
                            (create_ha_dsegtsv_lh, datasink, [('out_file', 'datasink.@ha_dseg_lh')]),
                            (convert_ha_seg_file_lh, datasink, [('out_file', 'datasink.@ha_segmentation_file_lh')]),
                            (selectfiles, segstats_ha_rh, [('rh_hippoAmygLabels', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_ha_rh, [('transformed_file', 'in_file')]),
                            (segstats_ha_rh, create_ha_tacs_rh, [('avgwf_txt_file', 'avgwf_file'),
                                                            ('ctab_out_file', 'ctab_file')]),
                            (selectfiles, create_ha_tacs_rh, [('json_file', 'json_file')]),
                            (segstats_ha_rh, create_ha_stats_rh, [('summary_file', 'summary_file')]),
                            (segstats_ha_rh, create_ha_dsegtsv_rh, [('ctab_out_file', 'ctab_file')]),
                            (selectfiles, convert_ha_seg_file_rh, [('rh_hippoAmygLabels', 'in_file')]),
                            (create_ha_tacs_rh, datasink, [('out_file', 'datasink.@ha_tacs_rh')]),
                            (create_ha_stats_rh, datasink, [('out_file', 'datasink.@ha_stats_rh')]),
                            (create_ha_dsegtsv_rh, datasink, [('out_file', 'datasink.@ha_dseg_rh')]),
                            (convert_ha_seg_file_rh, datasink, [('out_file', 'datasink.@ha_segmentation_file_rh')]),
                            (selectfiles, merge_seg_files, [('lh_hippoAmygLabels', 'in1')]),
                            (selectfiles, merge_seg_files, [('rh_hippoAmygLabels', 'in2')]),
                            (merge_seg_files, combine_ha_lr_dseg, [('out', 'in_files')]),
                            (combine_ha_lr_dseg, datasink, [('concatenated_file', 'datasink.@ha_segmentation_file')]),
                            (combine_ha_lr_dseg, segstats_ha, [('concatenated_file', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_ha, [('transformed_file', 'in_file')]),
                            (segstats_ha, create_ha_tacs, [('avgwf_txt_file', 'avgwf_file'),
                                                            ('ctab_out_file', 'ctab_file')]),
                            (selectfiles, create_ha_tacs, [('json_file', 'json_file')]),
                            (segstats_ha, create_ha_stats, [('summary_file', 'summary_file')]),
                            (segstats_ha, create_ha_dsegtsv, [('ctab_out_file', 'ctab_file')]),
                            (create_ha_tacs, datasink, [('out_file', 'datasink.@ha_tacs')]),
                            (create_ha_stats, datasink, [('out_file', 'datasink.@ha_stats')]),
                            (create_ha_dsegtsv, datasink, [('out_file', 'datasink.@ha_dseg')])
                            ])
            
    if args.wm is True:        
            segstats_wm = Node(SegStats(exclude_id = 0,
                                        default_color_table = True,
                                        avgwf_txt_file = 'desc-whiteMatter_tacs.txt',
                                        ctab_out_file = 'desc-whiteMatter_dseg.ctab',
                                        summary_file = 'desc-whiteMatter_stats.txt'),
                                name = 'segstats_wm')
            
            create_wm_tacs = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                            output_names = ['out_file'],
                                            function = avgwf_to_tacs),
                                    name = 'create_wm_tacs')
            
            create_wm_stats = Node(Function(input_names = ['summary_file'],
                                            output_names = ['out_file'],
                                            function = summary_to_stats),
                                    name = 'create_wm_stats')
            
            create_wm_dsegtsv = Node(Function(input_names = ['ctab_file'],
                                            output_names = ['out_file'],
                                            function = ctab_to_dsegtsv),
                                        name = 'create_wm_dsegtsv')
            
            convert_wm_seg_file = Node(MRIConvert(out_file = 'desc-whiteMatter_dseg.nii.gz'),
                                    name = 'convert_wm_seg_file')
            
            subject_wf.connect([(selectfiles, segstats_wm, [('wm_file', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_wm, [('transformed_file', 'in_file')]),
                            (segstats_wm, create_wm_tacs, [('avgwf_txt_file', 'avgwf_file'),
                                                            ('ctab_out_file', 'ctab_file')]),
                            (selectfiles, create_wm_tacs, [('json_file', 'json_file')]),
                            (segstats_wm, create_wm_stats, [('summary_file', 'summary_file')]),
                            (segstats_wm, create_wm_dsegtsv, [('ctab_out_file', 'ctab_file')]),
                            (create_wm_tacs, datasink, [('out_file', 'datasink.@wm_tacs')]),
                            (create_wm_stats, datasink, [('out_file', 'datasink.@wm_stats')]),
                            (create_wm_dsegtsv, datasink, [('out_file', 'datasink.@wm_dseg')]),
                            (selectfiles, convert_wm_seg_file, [('wm_file', 'in_file')]),
                            (convert_wm_seg_file, datasink, [('out_file', 'datasink.@wm_segmentation_file')])
                            ])
            
    if args.raphe is True:
                segment_raphe = Node(MRISclimbicSeg(keep_ac = True,
                                            percentile = 99.9,
                                            vmp = True,
                                            write_volumes = True,
                                            out_file = 'desc-raphe_dseg.nii.gz'),
                            name = 'segment_raphe')
        
                segment_raphe.inputs.model = pkg_resources.resource_filename('petprep_extract_tacs', 'utils/raphe+pons.n21.d114.h5')
                segment_raphe.inputs.ctab = pkg_resources.resource_filename('petprep_extract_tacs', 'utils/raphe+pons.ctab')

                segstats_raphe = Node(SegStats(exclude_id = 0,
                                            avgwf_txt_file = 'desc-raphe_tacs.txt',
                                            ctab_out_file = 'desc-raphe_dseg.ctab',
                                            summary_file = 'desc-raphe_stats.txt'),
                                    name = 'segstats_raphe')
                
                segstats_raphe.inputs.color_table_file = pkg_resources.resource_filename('petprep_extract_tacs', 'utils/raphe+pons_cleaned.ctab')
                
                create_raphe_tacs = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                                output_names = ['out_file'],
                                                function = avgwf_to_tacs),
                                        name = 'create_raphe_tacs')
                
                create_raphe_tacs.inputs.ctab_file = pkg_resources.resource_filename('petprep_extract_tacs', 'utils/raphe+pons_cleaned.ctab')
                
                create_raphe_stats = Node(Function(input_names = ['out_stats'],
                                            output_names = ['out_file'],
                                            function = limbic_to_stats),
                                    name = 'create_raphe_stats')

                create_raphe_dsegtsv = Node(Function(input_names = ['out_stats'],
                                                output_names = ['out_file'],
                                                function = limbic_to_dsegtsv),
                                            name = 'create_raphe_dsegtsv')
                
                subject_wf.connect([(selectfiles, segment_raphe, [('orig_file', 'in_file')]),
                            (segment_raphe, segstats_raphe, [('out_file', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_raphe, [('transformed_file', 'in_file')]),
                            (segstats_raphe, create_raphe_tacs, [('avgwf_txt_file', 'avgwf_file')]),
                            (selectfiles, create_raphe_tacs, [('json_file', 'json_file')]),
                            (create_raphe_tacs, datasink, [('out_file', 'datasink.@raphe_tacs')]),
                            (segment_raphe, datasink, [('out_file', 'datasink.@raphe_segmentation_file')]),
                            (segment_raphe,create_raphe_stats, [('out_stats', 'out_stats')]),
                            (create_raphe_stats, datasink, [('out_file', 'datasink.@raphe_stats')]),
                            (segment_raphe, create_raphe_dsegtsv, [('out_stats', 'out_stats')]),
                            (create_raphe_dsegtsv, datasink, [('out_file', 'datasink.@raphe_dseg')])
                            ])
                
    if args.limbic is True:
                segment_limbic = Node(MRISclimbicSeg(write_volumes = True,
                                                    out_file = 'desc-limbic_dseg.nii.gz'),
                            name = 'segment_limbic')
                segment_limbic.inputs.ctab = pkg_resources.resource_filename('petprep_extract_tacs', 'utils/sclimbic.ctab')
            
                segstats_limbic = Node(SegStats(exclude_id = 0,
                                            avgwf_txt_file = 'desc-limbic_tacs.txt',
                                            ctab_out_file = 'desc-limbic_dseg.ctab',
                                            summary_file = 'desc-limbic_stats.txt'),
                                    name = 'segstats_limbic')
                
                segstats_limbic.inputs.color_table_file = pkg_resources.resource_filename('petprep_extract_tacs', 'utils/sclimbic_cleaned.ctab')
                
                create_limbic_tacs = Node(Function(input_names = ['avgwf_file', 'ctab_file', 'json_file'],
                                                output_names = ['out_file'],
                                                function = avgwf_to_tacs),
                                        name = 'create_limbic_tacs')
                
                create_limbic_tacs.inputs.ctab_file = pkg_resources.resource_filename('petprep_extract_tacs', 'utils/sclimbic_cleaned.ctab')

                            
                create_limbic_stats = Node(Function(input_names = ['out_stats'],
                                            output_names = ['out_file'],
                                            function = limbic_to_stats),
                                    name = 'create_limbic_stats')

                create_limbic_dsegtsv = Node(Function(input_names = ['out_stats'],
                                                output_names = ['out_file'],
                                                function = limbic_to_dsegtsv),
                                            name = 'create_limbic_dsegtsv')
        
                subject_wf.connect([(selectfiles, segment_limbic, [('orig_file', 'in_file')]),
                            (segment_limbic, segstats_limbic, [('out_file', 'segmentation_file')]),
                            (move_pet_to_anat, segstats_limbic, [('transformed_file', 'in_file')]),
                            (segstats_limbic, create_limbic_tacs, [('avgwf_txt_file', 'avgwf_file')]),
                            (selectfiles, create_limbic_tacs, [('json_file', 'json_file')]),
                            (create_limbic_tacs, datasink, [('out_file', 'datasink.@limbic_tacs')]),
                            (segment_limbic, datasink, [('out_file', 'datasink.@limbic_segmentation_file')]),
                            (segment_limbic,create_limbic_stats, [('out_stats', 'out_stats')]),
                            (create_limbic_stats, datasink, [('out_file', 'datasink.@limbic_stats')]),
                            (segment_limbic, create_limbic_dsegtsv, [('out_stats', 'out_stats')]),
                            (create_limbic_dsegtsv, datasink, [('out_file', 'datasink.@limbic_dseg')])
                            ])
            
    return subject_wf

def add_sub(subject_id):
    return 'sub-' + subject_id

if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='BIDS App for PETPrep extract time activity curves (TACs) workflow')
    parser.add_argument('--bids_dir', required=True,  help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
    parser.add_argument('--output_dir', required=False, help='The directory where the output files '
                    'should be stored. If you are running group level analysis '
                    'this folder should be prepopulated with the results of the'
                    'participant level analysis.')
    parser.add_argument('--analysis_level', default='participant', help='Level of the analysis that will be performed. '
                    'Multiple participant level analyses can be run independently '
                    '(in parallel) using the same output_dir.',
                    choices=['participant', 'group'])
    parser.add_argument('--participant_label', help='The label(s) of the participant(s) that should be analyzed. The label '
                   'corresponds to sub-<participant_label> from the BIDS spec '
                   '(so it does not include "sub-"). If this parameter is not '
                   'provided all subjects should be analyzed. Multiple '
                   'participants can be specified with a space separated list.',
                   nargs="+", default=None)
    parser.add_argument('--n_procs', help='Number of processors to use when running the workflow', default=2)
    parser.add_argument('--gtm', help='Extract time activity curves from the geometric transfer matrix segmentation (gtmseg)', action='store_true')
    parser.add_argument('--brainstem', help='Extract time activity curves from the brainstem', action='store_true')
    parser.add_argument('--thalamicNuclei', help='Extract time activity curves from the thalamic nuclei', action='store_true')
    parser.add_argument('--hippocampusAmygdala', help='Extract time activity curves from the hippocampus and amygdala', action='store_true')
    parser.add_argument('--wm', help='Extract time activity curves from the white matter', action='store_true')
    parser.add_argument('--raphe', help='Extract time activity curves from the raphe nuclei', action='store_true')
    parser.add_argument('--limbic', help='Extract time activity curves from the limbic system', action='store_true')
    parser.add_argument('--surface', help='Extract surface-based time activity curves in fsaverage', action='store_true')
    parser.add_argument('--surface_smooth', help='Smooth surface-based time activity curves in fsaverage', type=int)
    parser.add_argument('--volume', help='Extract volume-based time activity curves in mni305', action='store_true')
    parser.add_argument('--volume_smooth', help='Smooth volume-based time activity curves in mni305', type=int)
    parser.add_argument('--agtm', help='Extract time activity curves from the adaptive gtm PVC', action='store_true')
    parser.add_argument('--psf', help='Initial guess of point spread function of PET scanner for agtm', type=float)
    parser.add_argument('--petprep_hmc', help='Use outputs from petprep_hmc as input to workflow', action='store_true')
    parser.add_argument('--skip_bids_validator', help='Whether or not to perform BIDS dataset validation',
                   action='store_true')
    parser.add_argument('-v', '--version', action='version',
                    version='PETPrep extract time activity curves BIDS-App version {}'.format(__version__))
    
    args = parser.parse_args() 
    
    main(args)
