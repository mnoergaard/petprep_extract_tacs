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
from nipype.interfaces.freesurfer import MRICoreg, ApplyVolTransform, MRIConvert, Concatenate
from petprep_extract_tacs.interfaces.petsurfer import GTMSeg, GTMPVC
from petprep_extract_tacs.interfaces.segment import SegmentBS, SegmentHA_T1, SegmentThalamicNuclei, MRISclimbicSeg
from petprep_extract_tacs.interfaces.fs_model import SegStats
from petprep_extract_tacs.utils.utils import ctab_to_dsegtsv, avgwf_to_tacs, summary_to_stats, gtm_to_tacs, gtm_stats_to_stats, gtm_to_dsegtsv, limbic_to_dsegtsv, limbic_to_stats, plot_reg

__version__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'version')).read()

def main(args): 
    """Main function for the PETPrep extract time activity curves workflow."""

    if os.path.exists(args.bids_dir):
        if not args.skip_bids_validator:
            layout = BIDSLayout(args.bids_dir, validate=True)
        else:
            layout = BIDSLayout(args.bids_dir, validate=False)
    else:
        raise Exception('BIDS directory does not exist')
    
    if check_valid_fs_license() is not True:
        raise Exception('You need a valid FreeSurfer license to proceed!')
    
    # Get all PET files
    if args.participant_label is None:
        args.participant_label = layout.get(suffix='pet', target='subject', return_type='id')

    infosource = Node(IdentityInterface(
                        fields = ['subject_id','session_id']),
                        name = "infosource")
    
    sessions = layout.get_sessions()
    if sessions:
        infosource.iterables = [('subject_id', args.participant_label),
                                ('session_id', sessions)]
    else:
        infosource.iterables = [('subject_id', args.participant_label)]


    if args.petprep_hmc is True:
        templates = {'orig_file': 'derivatives/freesurfer/sub-{subject_id}/mri/orig.mgz',
                    'wm_file': 'derivatives/freesurfer/sub-{subject_id}/mri/wmparc.mgz',
                    'brainmask_file': 'derivatives/freesurfer/sub-{subject_id}/mri/brainmask.mgz',
                    'fs_subject_dir': 'derivatives/freesurfer',
                    'pet_file': 'derivatives/petprep_hmc/sub-{subject_id}/*_pet.[n]*' if not sessions else 'derivatives/petprep_hmc/sub-{subject_id}/ses-{session_id}/*_pet.[n]*',
                    'json_file': 'sub-{subject_id}/pet/*_pet.json' if not sessions else 'sub-{subject_id}/ses-{session_id}/pet/*_pet.json'} 
    else:
        templates = {'orig_file': 'derivatives/freesurfer/sub-{subject_id}/mri/orig.mgz',
                    'wm_file': 'derivatives/freesurfer/sub-{subject_id}/mri/wmparc.mgz',
                    'brainmask_file': 'derivatives/freesurfer/sub-{subject_id}/mri/brainmask.mgz',
                    'fs_subject_dir': 'derivatives/freesurfer',
                    'pet_file': 'sub-{subject_id}/pet/*_pet.[n]*' if not sessions else 'sub-{subject_id}/ses-{session_id}/pet/*_pet.[n]*',
                    'json_file': 'sub-{subject_id}/pet/*_pet.json' if not sessions else 'sub-{subject_id}/ses-{session_id}/pet/*_pet.json'}
        
           
    selectfiles = Node(SelectFiles(templates, 
                               base_directory = args.bids_dir), 
                               name = "select_files")

    substitutions = [('_subject_id', 'sub'), ('_session_id_', 'ses')]
    subjFolders = [('sub-%s' % (sub), 'sub-%s' % (sub))
               for sub in layout.get_subjects()] if not sessions else [('sub-%s_ses-%s' % (sub, ses), 'sub-%s/ses-%s' % (sub, ses))
               for ses in layout.get_sessions()
               for sub in layout.get_subjects()]

    substitutions.extend(subjFolders)

    # clean up and create derivatives directories
    if args.output_dir is None:
        output_dir = os.path.join(args.bids_dir,'derivatives','petprep_extract_tacs')
    else:
        output_dir = args.output_dir
    
    os.makedirs(output_dir, exist_ok=True)

    # Define nodes for hmc workflow
    
    coreg_pet_to_t1w = Node(MRICoreg(out_lta_file = 'from-pet_to-t1w_reg.lta'),
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
                                container = os.path.join(args.bids_dir,'extract_tacs_pet_wf')),
                    name = 'datasink')
    
    # Define workflow
    workflow = Workflow(name='extract_tacs_pet_wf', base_dir=args.bids_dir)
    workflow.config['execution']['remove_unnecessary_outputs'] = 'false'
    workflow.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),('session_id', 'session_id')]), 
                        (selectfiles, create_time_weighted_average, [('pet_file', 'pet_file')]),
                        (selectfiles, create_time_weighted_average, [('json_file', 'json_file')]),
                        (selectfiles, coreg_pet_to_t1w, [('brainmask_file', 'reference_file')]),
                        (create_time_weighted_average, coreg_pet_to_t1w, [('out_file', 'source_file')]),
                        (coreg_pet_to_t1w, move_pet_to_anat, [('out_lta_file', 'lta_file')]),
                        (selectfiles, move_pet_to_anat, [('brainmask_file', 'target_file')]),
                        (selectfiles, move_pet_to_anat, [('pet_file', 'source_file')]),
                        (move_pet_to_anat, datasink, [('transformed_file', 'datasink.@transformed_file')]),
                        (coreg_pet_to_t1w, datasink, [('out_lta_file', 'datasink.@out_lta_file')]),
                        (create_time_weighted_average, move_twa_to_anat, [('out_file', 'source_file')]),
                        (selectfiles, move_twa_to_anat, [('brainmask_file', 'target_file')]),
                        (coreg_pet_to_t1w, move_twa_to_anat, [('out_lta_file', 'lta_file')]),
                        (move_twa_to_anat, datasink, [('transformed_file', 'datasink.@transformed_twa_file')]),
                        (selectfiles, convert_brainmask, [('brainmask_file', 'in_file')]),
                        (convert_brainmask, datasink, [('out_file', 'datasink.@brainmask_file')]),
                        (convert_brainmask, plot_registration, [('out_file', 'fixed_image')]),
                        (move_twa_to_anat, plot_registration, [('transformed_file', 'moving_image')]),
                        (plot_registration, datasink, [('out_file', 'datasink.@plot_reg')])
                        ])
    
    if args.gtm is True:

        gtmseg = Node(GTMSeg(out_file = 'space-T1w_desc-gtmseg_dseg.nii.gz',
                         xcerseg = True),
                  name = 'gtmseg')
    
        gtmpvc = Node(GTMPVC(default_seg_merge = True,
                            auto_mask = (1,0.1),
                            no_pvc = True,
                            pvc_dir = 'nopvc'),
                    name = 'gtmpvc')
        
        create_gtmseg_tacs = Node(Function(input_names = ['in_file', 'json_file', 'gtm_stats'],
                                            output_names = ['out_file'],
                                            function = gtm_to_tacs),
                                name = 'create_gtmseg_tacs')
        
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
        
        workflow.connect([(infosource, gtmseg, [(('subject_id', add_sub), 'subject_id')]),
                        (selectfiles, gtmseg, [('fs_subject_dir', 'subjects_dir')]),
                        (selectfiles, gtmpvc, [('pet_file', 'in_file')]),
                        (gtmseg, gtmpvc, [('out_file', 'segmentation')]),
                        (coreg_pet_to_t1w, gtmpvc, [('out_lta_file', 'reg_file')]),
                        (gtmpvc, create_gtmseg_tacs, [('nopvc_file', 'in_file')]),
                        (gtmpvc, create_gtmseg_tacs, [('gtm_stats', 'gtm_stats')]),
                        (selectfiles, create_gtmseg_tacs, [('json_file', 'json_file')]),
                        (create_gtmseg_tacs, datasink, [('out_file', 'datasink.@gtmseg_tacs')]),
                        (gtmpvc, create_gtmseg_stats, [('gtm_stats', 'gtm_stats')]),
                        (create_gtmseg_stats, datasink, [('out_file', 'datasink.@gtmseg_stats')]),
                        (gtmseg, convert_gtmseg_file, [('out_file', 'in_file')]),
                        (convert_gtmseg_file, datasink, [('out_file', 'datasink.@gtmseg_file')]),
                        (gtmpvc, create_gtmseg_dsegtsv, [('gtm_stats', 'gtm_stats')]),
                        (create_gtmseg_dsegtsv, datasink, [('out_file', 'datasink.@gtmseg_dsegtsv')])
                        ])

    
    if args.brainstem is True:
        segment_bs = Node(SegmentBS(),
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
        
        workflow.connect([(infosource, segment_bs, [(('subject_id', add_sub), 'subject_id')]),
                        (selectfiles, segment_bs, [('fs_subject_dir', 'subjects_dir')]),
                        (segment_bs, segstats_bs, [('bs_labels_voxel', 'segmentation_file')]),
                        (move_pet_to_anat, segstats_bs, [('transformed_file', 'in_file')]),
                        (segstats_bs, create_bs_tacs, [('avgwf_txt_file', 'avgwf_file'),
                                                        ('ctab_out_file', 'ctab_file')]),
                        (selectfiles, create_bs_tacs, [('json_file', 'json_file')]),
                        (segstats_bs, create_bs_stats, [('summary_file', 'summary_file')]),
                        (segstats_bs, create_bs_dsegtsv, [('ctab_out_file', 'ctab_file')]),
                        (segment_bs, convert_bs_seg_file, [('bs_labels_voxel', 'in_file')]),
                        (create_bs_tacs, datasink, [('out_file', 'datasink')]),
                        (create_bs_stats, datasink, [('out_file', 'datasink.@bs_stats')]),
                        (create_bs_dsegtsv, datasink, [('out_file', 'datasink.@bs_dseg')]),
                        (convert_bs_seg_file, datasink, [('out_file', 'datasink.@bs_segmentation_file')])
                        ])
        
    if args.thalamicNuclei is True:
        segment_th = Node(SegmentThalamicNuclei(),
                        name = 'segment_th')
        
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
        
        workflow.connect([(infosource, segment_th, [(('subject_id', add_sub), 'subject_id')]),
                        (selectfiles, segment_th, [('fs_subject_dir', 'subjects_dir')]),
                        (segment_th, segstats_th, [('thalamic_labels_voxel', 'segmentation_file')]),
                        (move_pet_to_anat, segstats_th, [('transformed_file', 'in_file')]),
                        (segstats_th, create_th_tacs, [('avgwf_txt_file', 'avgwf_file'),
                                                        ('ctab_out_file', 'ctab_file')]),
                        (selectfiles, create_th_tacs, [('json_file', 'json_file')]),
                        (segstats_th, create_th_stats, [('summary_file', 'summary_file')]),
                        (segstats_th, create_th_dsegtsv, [('ctab_out_file', 'ctab_file')]),
                        (segment_th, convert_th_seg_file, [('thalamic_labels_voxel', 'in_file')]),
                        (create_th_tacs, datasink, [('out_file', 'datasink.@th_tacs')]),
                        (create_th_stats, datasink, [('out_file', 'datasink.@th_stats')]),
                        (create_th_dsegtsv, datasink, [('out_file', 'datasink.@th_dseg')]),
                        (convert_th_seg_file, datasink, [('out_file', 'datasink.@th_segmentation_file')])
                        ])
    
    if args.hippocampusAmygdala is True:
        segment_ha = Node(SegmentHA_T1(),
                        name = 'segment_ha')
        
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
        
        workflow.connect([(infosource, segment_ha, [(('subject_id', add_sub), 'subject_id')]),
                        (selectfiles, segment_ha, [('fs_subject_dir', 'subjects_dir')]),
                        (segment_ha, segstats_ha_lh, [('lh_hippoAmygLabels', 'segmentation_file')]),
                        (move_pet_to_anat, segstats_ha_lh, [('transformed_file', 'in_file')]),
                        (segstats_ha_lh, create_ha_tacs_lh, [('avgwf_txt_file', 'avgwf_file'),
                                                        ('ctab_out_file', 'ctab_file')]),
                        (selectfiles, create_ha_tacs_lh, [('json_file', 'json_file')]),
                        (segstats_ha_lh, create_ha_stats_lh, [('summary_file', 'summary_file')]),
                        (segstats_ha_lh, create_ha_dsegtsv_lh, [('ctab_out_file', 'ctab_file')]),
                        (segment_ha, convert_ha_seg_file_lh, [('lh_hippoAmygLabels', 'in_file')]),
                        (create_ha_tacs_lh, datasink, [('out_file', 'datasink.@ha_tacs_lh')]),
                        (create_ha_stats_lh, datasink, [('out_file', 'datasink.@ha_stats_lh')]),
                        (create_ha_dsegtsv_lh, datasink, [('out_file', 'datasink.@ha_dseg_lh')]),
                        (convert_ha_seg_file_lh, datasink, [('out_file', 'datasink.@ha_segmentation_file_lh')]),
                        (segment_ha, segstats_ha_rh, [('rh_hippoAmygLabels', 'segmentation_file')]),
                        (move_pet_to_anat, segstats_ha_rh, [('transformed_file', 'in_file')]),
                        (segstats_ha_rh, create_ha_tacs_rh, [('avgwf_txt_file', 'avgwf_file'),
                                                        ('ctab_out_file', 'ctab_file')]),
                        (selectfiles, create_ha_tacs_rh, [('json_file', 'json_file')]),
                        (segstats_ha_rh, create_ha_stats_rh, [('summary_file', 'summary_file')]),
                        (segstats_ha_rh, create_ha_dsegtsv_rh, [('ctab_out_file', 'ctab_file')]),
                        (segment_ha, convert_ha_seg_file_rh, [('rh_hippoAmygLabels', 'in_file')]),
                        (create_ha_tacs_rh, datasink, [('out_file', 'datasink.@ha_tacs_rh')]),
                        (create_ha_stats_rh, datasink, [('out_file', 'datasink.@ha_stats_rh')]),
                        (create_ha_dsegtsv_rh, datasink, [('out_file', 'datasink.@ha_dseg_rh')]),
                        (convert_ha_seg_file_rh, datasink, [('out_file', 'datasink.@ha_segmentation_file_rh')]),
                        (segment_ha, merge_seg_files, [('lh_hippoAmygLabels', 'in1')]),
                        (segment_ha, merge_seg_files, [('rh_hippoAmygLabels', 'in2')]),
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
        
        workflow.connect([(selectfiles, segstats_wm, [('wm_file', 'segmentation_file')]),
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
            
            workflow.connect([(selectfiles, segment_raphe, [('orig_file', 'in_file')]),
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
    
            workflow.connect([(selectfiles, segment_limbic, [('orig_file', 'in_file')]),
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

    wf = workflow.run(plugin='MultiProc', plugin_args={'n_procs' : int(args.n_procs)})

    # clean up and create derivatives directories
    if args.output_dir is None:
        output_dir = os.path.join(args.bids_dir,'derivatives','petprep_extract_tacs')
    else:
        output_dir = args.output_dir
        
     # remove temp outputs
    #shutil.rmtree(os.path.join(args.bids_dir, 'petprep_hmc_wf'))

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
    parser.add_argument('--petprep_hmc', help='Use outputs from petprep_hmc as input to workflow', action='store_true')
    parser.add_argument('--skip_bids_validator', help='Whether or not to perform BIDS dataset validation',
                   action='store_true')
    parser.add_argument('-v', '--version', action='version',
                    version='PETPrep extract time activity curves BIDS-App version {}'.format(__version__))
    
    args = parser.parse_args() 
    
    main(args)
