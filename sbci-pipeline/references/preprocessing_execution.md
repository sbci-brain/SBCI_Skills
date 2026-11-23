# Local preprocessing execution

## GUI contract

Inspection reports `workflow.executor.nextStage` and
`workflow.executor.eligible`. Keep the primary control disabled unless the next
stage is `pending`. Starting it requires changing the configuration to
`mode: preprocess` and `approved: true`; one invocation runs at most one stage.
The same control advances raw correction, shared preprocessing, optional PSC,
and final SBCI in order.

## Work tree and provenance

`<pipeline>/workflow/preprocessing_executor.py` copies `anat/`, `dwi/`, `func/`, `fmri/`,
and any partial `dwi_pipeline/` into:

```text
<run-output>/files/preprocessing_work/<subject>/
```

It hashes every copied source file into `source_provenance.json`. Reusing the
same output directory after any source change is rejected. Commands receive
only work-tree paths as writable outputs. Never replace the copy with writable
symlinks or hard links to patient inputs.

An exclusive `.execution.lock` prevents concurrent stage writers. Do not add a
force-unlock GUI action; stale locks require inspection of the owning process.

## Stage markers

Write `state/<stage>.json` atomically only after all commands exit successfully,
the source fingerprint remains unchanged, and the stage-specific output
validator passes. On resume, revalidate the outputs and fingerprint before
skipping the stage. A zero exit code alone is never completion.

Raw DWI correction derives phase encoding and readout time from the subject's
BIDS JSON, uses the image's Synb0-DISCO and the selected FreeSurfer license, then
runs CPU FSL `topup` and `eddy`. No cohort default or uncorrected fallback is
allowed. Raw fMRI correction reuses the validated DWI field map and requires
subject-specific effective echo spacing.

`prepare_data` uses MRtrix3 plus the Python 3 scilpy adapter. Registration,
FreeSurfer, fODF, FSFast, and optional PSC execute only the exact allowlisted
script name from the pipeline's `preprocessing/` folder (or from
`reference_scripts_dir` when one is set), with `SBCI_CONFIG` set to the selected
non-empty `preprocessing_config`, the dataset profile.
All script working directories are constrained to the copied subject tree.

The final `sbci` stage uses the image's SBCI Python (`SBCI_CORE_PY`), the scripts in
`<pipeline>/pipeline/`, and the existing SC/FC matrix validators. `workflow.run_psc` remains false by default because
PSC is an optional companion branch rather than an SBCI prerequisite.

## Stage order

1. `dwi_correction`
2. `fmri_correction`
3. `prepare_data`
4. `t1_dwi_registration`
5. `freesurfer`
6. `fodf_tissue`
7. `fsfast`
8. `psc` when explicitly selected
9. `sbci`
