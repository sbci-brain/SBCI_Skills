# Guided SBCI execution and backend routing

Use this reference for the user-facing intake, execution-target selection, and
preflight behavior. Keep the primary path understandable without neuroimaging,
Linux, Python, SSH, or Slurm knowledge.

## Public UX model

Wanda CyberBench's public entry page presents CyberBench-Neuro as agentic
neuroimaging across HPC, cloud, and local compute, followed by a single
plain-language **Get Started** action. Preserve that progressive-disclosure
model in CyberNeuro:

- Begin with a guided choice, not a configuration form.
- Explain technical data profiles using examples from the selected folder.
- Show the first actionable blocker rather than a wall of diagnostics.
- Keep exact paths, command lines, container images, and Slurm resources under
  **Advanced** while still recording them in the manifest.
- Never imply access to private Wanda screens or behavior that was not
  independently verified.

## Guided questions and routes

Ask only questions that cannot be answered safely from inventory.

| Question | Choice | Route |
| --- | --- | --- |
| Who is the pipeline for? | Adult/ADNI | Continue. |
| Who is the pipeline for? | Infant | Stop before execution and route to an infant-specific workflow. |
| What data are available? | Raw BIDS with T1w, DWI, and resting BOLD | Run the approval-gated staged workflow (correction, preprocessing, SBCI) with the dataset's profile. |
| What data are available? | Prepared Python-3 SBCI subject tree | Validate required products, then run SBCI directly. Do not rerun completed preprocessing. |
| What data are available? | Completed SBCI matrices | Inspect, validate, or visualize only. Never preprocess or overwrite them. |
| Where should it run? | Local (Linux, or Windows through WSL) | Runs in the `sbci-full` image with Apptainer or Docker, in the background. No SSH or Slurm is required; a Linux MATLAB is. |
| Where should it run? | Longleaf HPC | Perform read-only preflight first. Submit only after separate explicit approval. |
| Where should it run? | Cloud | Report unavailable unless CyberNeuro exposes a configured cloud dispatcher. Never simulate submission. |

For ambiguous folders, run `mode: inspect` and report which signatures were
found. Ask the user to choose only when more than one scientifically valid
route remains.

## Output names are scientific claims

The read-only brain-MRI reference skill on Longleaf is useful for orchestration,
not as a drop-in SBCI backend. Reuse its patterns for population-first routing,
modality inventory, centralized configuration, pinned versions, pre-run and
post-run checkpoints, batch submission, idempotent resume, and output
validation.

Do not reuse its output labels indiscriminately:

- XCP-D and QSIRecon produce parcellated atlas connectivity products.
- SBCI consumes a specific FreeSurfer, fODF, FSFast, and ico4 dense-surface
  contract and produces 5,124-by-5,124 cortical connectivity matrices.
- An atlas matrix is not an SBCI matrix, even if both are called FC or SC.
- Import fMRIPrep, QSIPrep, FreeSurfer, or related derivatives only after the
  adapter verifies exact SBCI-required files, geometry, vertex ordering, and
  dimensions. Otherwise leave the stage blocked.

PSC remains an optional companion atlas connectome. It is never an SBCI input.

## Pre-run checkpoint

Display a concise readiness card containing:

1. Population and detected input profile.
2. Subject and session identifiers without uploading or redistributing ADNI
   data.
3. Required modalities and sidecars.
4. DWI NIfTI volume count, `.bval` count, and `.bvec` column count.
5. Phase-encoding direction, total readout time or justified estimate, and BOLD
   repetition time.
6. First incomplete stage and its dependency or license blocker.
7. Execution target and resolved output location.
8. Whether the action is inspection, quick plumbing test, or scientific run.

On every machine, report the container runtime (Apptainer or Docker), the image, and
whether MATLAB was found. For Longleaf, also show the input, output and log directories;
the FreeSurfer license; the folders bound into the container; partition, time, memory
and CPUs. Treat every site convention (a shared licence file, template folder or bind
mount) as a preflight candidate to verify, not a hardcoded guarantee.

## Confirmation and execution

Inspection must not install packages, copy patient data to a new backend,
submit jobs, or modify Longleaf. Runtime installation, local scientific
execution, and HPC submission are three separate approvals.

When execution is approved:

- Preserve source inputs and work in the output-side copy.
- Run one durable stage per invocation and resume from validated markers.
- Use pinned, displayed runtime/container versions.
- Make submitters idempotent so a repeated click does not create duplicate
  jobs.
- Keep each subject/session attributable in manifests and logs.

## Post-run checkpoint

Success requires more than a process exit code, Slurm state, or log file.
Require expected files to exist, be non-empty, parse successfully, and satisfy
the dimensional and finite-value checks in `quality_contract.md`. For SBCI,
preserve ico4 vertex ordering and validate cortical and subcortical blocks by
explicit variable name. Never use a largest-square-array heuristic because it
can discard valid subcortical matrices.

For prepared ADNI Python-3 data, keep the source tree read-only, process one
session at a time, and avoid loading the whole cohort into memory. Completed
matrices are inspection inputs, not permission to rerun or overwrite upstream
processing.
