# Cross-skill orchestration

CyberNeuro/Wanda permits a user to finish one pipeline and use its durable
outputs in a later pipeline. Keep each producer in its own environment or
container. Share files, not installed commands or mutable work directories.

## Supported orchestration mode

`manual_shared_artifacts` is the only supported mode. It produces a deterministic
recommendation and validates a handoff manifest. It does not silently launch a
different skill: the current Wanda cross-skill invocation API has not been
documented, and a visible pipeline card is not an executable compatibility
contract.

Use this configuration under `workflow`:

```json
"orchestration": {
  "mode": "manual_shared_artifacts",
  "shared_work_dir": "/path/to/durable/shared/output",
  "handoff_manifest": "/path/to/sbci_handoff.json",
  "verify_hashes": true,
  "consume_handoff": false
}
```

Inspection writes `files/orchestration_plan.json` and
`files/sbci_handoff.template.json`. The plan names the next incomplete SBCI
stage, candidate Wanda producer skills, and exact required artifact roles.
`candidate` never means compatible: validate the files, grids, affines,
surfaces, annotations, and time-series dimensions before SBCI.

## Producer procedure

1. Run the chosen producer skill in its own container/environment.
2. Save durable results under a user-selected shared output directory. Keep its
   temporary work directory separate and disposable.
3. Record a completed handoff using `<pipeline>/workflow/contracts/sbci.handoff.schema.json`.
   Artifact paths must be relative to the declared artifact root; traversal and
   absolute artifact paths are rejected.
4. From the pipeline folder, inside the image, run
   `python3 -m workflow.orchestration <manifest> --pretty`. Add
   `--shared-work-dir <dir>` when the manifest and artifacts are in separate
   durable locations. Use `--verify-hashes` only when hashes were recorded; it
   can be expensive for large NIfTI files.
5. First inspect with `consume_handoff=false`. The validator never copies,
   moves, or modifies producer data.
6. To accept the handoff, set top-level `mode` to `preprocess`, set
   `approved=true`, and set `consume_handoff=true`. One invocation copies only
   the next stage's declared artifacts into
   `files/preprocessing_work/<subject>/`, verifies source and destination
   SHA-256 digests, writes a provenance marker under
   `files/preprocessing_work/state/`, replans, and stops. It never edits the
   producer directory and never overwrites a conflicting work-tree artifact.

`verify_hashes` controls the inspection-time manifest check. Consumption always
verifies the source and destination digests, even when inspection used
`verify_hashes=false`.

### Hashing large artifacts once

Consumption re-validates the manifest with SHA-256 checking enabled before any
copy. The digest computed in that mandatory validation is reused as the source
digest during the copy, so a multi-gigabyte producer file (for example a 2 GB
DWI series) is read for hashing once, not twice. A source digest is recomputed
only when validation did not verify it. The copied destination is always hashed
independently and must match. On a slow filesystem, set `verify_hashes=false`
for the planning inspection to avoid a redundant full read; this never weakens
the checks performed during consumption.

## `prepare_data` handoff contract

A `prepare_data` handoff must declare all four prepared-input roles. Each is
copied as a regular file to a fixed SBCI location inside the work subject:

| Role   | Destination under `files/preprocessing_work/<subject>/` |
|--------|---------------------------------------------------------|
| `t1`   | `dwi_pipeline/t1.nii.gz`                                |
| `dwi`  | `dwi_pipeline/data.nii.gz`                              |
| `bval` | `dwi_pipeline/flip_x.bval`                              |
| `bvec` | `dwi_pipeline/flip_x.bvec`                              |

Artifact paths in the manifest stay relative to the producer's artifact root;
the producer layout does not need to match these destinations (the validated
ADNI producer kept DWI and gradients under `diffusion/`). After copying,
the prepared-input validator checks that all four files are present and that
the b-value count matches the b-vector columns. A manifest that omits `t1`, as
earlier contracts did, is rejected with a missing-role error.

## Current provider candidates

- BIDS validity: BIDS Validator, before the nine SBCI stages.
- DWI/fMRI distortion correction: FSL or Brain MRI Data Preprocessing Pipelines.
- T1/DWI registration: ANTs or Brain MRI Data Preprocessing Pipelines.
- Cortical reconstruction: FreeSurfer or Brain MRI Data Preprocessing Pipelines.
- fODF/tissue preparation: Brain MRI Data Preprocessing Pipelines.
- FSFast residual production: FreeSurfer or Brain MRI Data Preprocessing
  Pipelines, but only if its actual residual outputs match SBCI's contract.
- SBCI connectivity: this SBCI skill's isolated Python-3 environment.

PSC remains optional and is not an SBCI dependency. Do not map QSIRecon/XCP-D
atlas matrices to SBCI dense ico4 artifacts.

## Completed ADNI connectivity

The cleaned production layout
`sub-*/ses-*/psc_sbci_final_files/{sbci_connectome,psc_connectome,diffusion,set,structure}`
is a terminal, read-only `completed_connectivity` route. It may be inspected or
analyzed, but it is not a source tree for rerunning preprocessing or SBCI.
Never infer a missing preprocessing input from a final matrix directory.
Inspection validates the retained SC, subcortical SC, and FC MAT variables and
ico4 dimensions directly. It must not require the cleaned-away sparse NPZ or
raw time-series/intersection artifacts.

The reference skill used for these conventions is read-only. It separates input,
durable output, temporary work, Slurm logs, and a reviewed environment file;
containers and licenses are not bundled with the skill.
