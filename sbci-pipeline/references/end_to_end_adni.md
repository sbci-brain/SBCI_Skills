# End-to-end ADNI workflow

## Branching model

Use one shared preprocessing trunk:

1. Detect one BIDS subject with T1w, DWI plus gradients/JSON, and resting BOLD plus JSON.
2. Correct single-direction ADNI DWI with Synb0-DISCO, FSL topup, and eddy.
3. Register the DWI-derived field map to BOLD space and apply FSL fugue.
4. Reorient images/gradients, register T1 to DWI, and calculate DTI metrics.
5. Run FreeSurfer and warp Desikan/Destrieux labels into DWI space.
6. Segment WM/GM/CSF and estimate an order-6 fODF for ADNI's limited directions.
7. Run FSFast nuisance regression and export LH, RH, and MNI residuals.

After the trunk, run either or both outputs:

- SBCI: surface-enhanced tractography, cortical grid mapping, SC, and FC.
- PSC (optional): whole-brain PFT plus atlas-based structural connectomes.

PSC output is not an input to SBCI.

## Runtime boundary

Every tool runs inside the `sbci-full` image: FSL, MRtrix3, ANTs, FreeSurfer/FSFast,
Synb0-DISCO and the two Python environments with scilpy 2.3. Nothing is installed on the
machine, and the stages see only the image's commands. Two things come from the machine:
a Linux MATLAB for FSFast, and the user's own FreeSurfer license. Do not bundle or
fabricate a license, and do not create shell aliases that hide changed CLI arguments.

The native `prepare_data` adapter uses scilpy's Python 3 commands, including
`scil_gradients_convert` and `scil_gradients_modify_axes`. The stage scripts in the
pipeline's `preprocessing/` folder call scilpy 2.x names throughout.

Keep raw inputs read-only. Copy them into a dedicated output-side work
tree, write a durable marker only after validating each stage's outputs, and
resume from the first incomplete marker. Never infer completion from an exit
code alone.

## ADNI-specific invariants

- Read phase-encoding direction and readout/echo spacing from BIDS JSON.
- Do not assume that all ADNI scanners use the same JSON keys.
- Accept Philips estimated readout/echo-spacing fields only when numeric, and
  record when total readout time was derived from echo spacing and matrix size.
- Reject empty, malformed, or inconsistent b-value and b-vector counts before
  any image is copied into the work tree.
- Require corrected DWI volumes to match b-value and b-vector counts.
- Use rotated b-vectors produced by eddy.
- Use fODF spherical-harmonic order 6 for single-shell data (8 for multi-shell)
  unless configured otherwise; the fODF stage refuses an order the gradient
  table cannot support ((L+1)(L+2)/2 unique directions).
- Read fMRI TR from BIDS metadata. The ADNI profile declares `FMRI_TR=3`, so a
  nonmatching subject is rejected rather than processed with the ADNI FSFast
  profile; a profile without `FMRI_TR` takes each subject's TR from BIDS.
- Keep susceptibility correction mandatory by default. Any uncorrected fallback
  must require explicit approval and be labeled in the manifest.
