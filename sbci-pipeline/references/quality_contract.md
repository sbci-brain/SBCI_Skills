# SBCI local GUI quality contract

## Purpose

The entry point (`<pipeline>/run_pipeline.py`) runs the stages one at a time inside the
`sbci-full` image. It does not itself require an SSH account, Slurm, or a cluster; the job
script adds Slurm where there is one. It accepts raw BIDS for inventory, planning and
staged execution, and consumes FreeSurfer, diffusion/fODF/tissue-map, and FSFast products
for SBCI execution. On Windows it runs in WSL.

PSC is a separate optional branch. Its atlas connectome is not read by SBCI.

## Required inputs

- Exactly one raw BIDS, partially processed, or SBCI-ready subject folder.
- The files enumerated by `<pipeline>/workflow/local_pipeline.py::inspect_subject`.
- Optional `sbci_local.json`, conforming to
  `<pipeline>/workflow/contracts/sbci.local.schema.json`. With no config, the adapter performs a
  friendly inspection only and writes a ready-to-edit template.

## Modes

- `self_test`: verifies the local runtime and bundled assets without patient
  data. It produces no connectivity matrices and is never scientific completion.
- `inspect`: checks data and runtime; never runs scientific stages.
- `quick_test`: runs one deliberately reduced smoke-test loop. Its matrices are
  testing artifacts and must not be interpreted scientifically.
- `production`: runs the displayed parameters and requires `approved: true`.

## Expected outputs

- `local_adapter_manifest.json`
- `reports/sbci_local_report.html`
- `files/sbci_local.template.json`
- `files/runtime_self_test.json` and `logs/runtime_self_test.log` in self-test mode
- `files/subject_metadata.json` and `logs/subject_metadata_probe.log` for a
  complete subject preflight
- `workflow.inventory`, `workflow.plan`, and `workflow.runtime` in the manifest
  for end-to-end configuration
- per-stage logs under `logs/`
- validated `.mat`/`.npz` connectivity artifacts under
  `files/connectivity/` after a successful run (through the job script: in
  `<OUTPUT_DIR>/sbci_output/`, with the matrices also in
  `files/work/<subject>/dwi_pipeline/sbci_connectome/`)

## Completion rules

- Passing inspection is not scientific completion.
- Passing the patient-free self-test proves installation integrity only.
- A stage exit code of zero is not sufficient by itself.
- A completed run requires non-empty and parseable cortical SC, subcortical SC,
  and FC artifacts containing finite numeric arrays with validated ico4
  dimensions and non-empty connectivity.
- Only validated `production` runs set `officialScientificPipelineRan: true`.

## Safety

- The source input tree is treated as read-only. Step-2 generated PFT maps are
  written into a real output-side `structure/` container so they cannot travel
  through a directory symlink into the source subject.
- Production requires explicit approval in the config.
- The local path uses neither SSH nor Slurm and never collects credentials.
- Existing output staging paths are never silently replaced.
