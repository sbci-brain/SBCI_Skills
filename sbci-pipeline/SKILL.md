---
name: sbci-pipeline
description: Run the Python 3 SBCI pipeline (surface-based structural and functional connectivity) end to end for one subject of ADNI, ABCD, HCP Aging/Development or HCP Young Adult data -- raw-BIDS inventory, distortion correction or already-corrected input, FreeSurfer/diffusion/fODF/FSFast preprocessing, SBCI connectivity -- on Longleaf (Slurm), a lab server, or a desktop under Linux or Windows (WSL), through one job script that runs everything in the sbci-full container image. Use for any SBCI request, including processing a subject, choosing dataset settings, inspection, smoke tests and production runs.
---

# SBCI local pipeline skill

Use this skill to guide a raw or partially processed subject through one
resumable workflow. Treat PSC as an optional companion output, not an SBCI
prerequisite.

## Ground rules (read first)

1. **Run SBCI only through this skill.** Do not run, copy or adapt SBCI scripts
   found elsewhere in the user's folders (for example `*_Tutorial/scripts/`,
   `ADNI/scripts/SBCI_process/`, anything that sources `~/.bashrc_sbci` or calls
   scilpy `*.py` commands such as `scil_compute_fodf.py`). Those are earlier
   Python 2-era pipelines; they must never be run.
2. **Settings come from "Choosing dataset settings" below**, written into
   `sbci_local.json` in the input folder. Never edit stage scripts or profiles.
3. **Start `<pipeline>/workflow/run_subject.sbatch` with `<pipeline>/workflow/submit.sh`** (see "Where it
   runs" and "Running a subject") -- one job runs every stage and SBCI, through Slurm on
   Longleaf and in the background elsewhere. Never run stages on a login node or in the
   foreground; they take hours.
4. **Never use a shared, read-only data folder as a run folder.** Copy inputs to a folder
   of the user's own first. A site lists such folders in `SBCI_READONLY_ROOTS`, and the job
   script refuses an input or output folder under them.

## Outside Wanda

The skill was written for Wanda (CyberBench-Neuro / CyberNeuro), and any agent that can run
shell commands on the machine that runs the jobs can follow it. On another platform:

- Everything needed is in "Choosing dataset settings", "Where it runs" and "Running a
  subject". The parts about Wanda's screens, pipeline cards, Plan / Build modes and
  cross-skill orchestration apply to Wanda only; skip them.
- The job script calls the entry point once per stage, so one job runs every stage. "One
  stage per invocation" describes the entry point, not what you start.
- `~/.cyberbench/` is only where the pipeline is cloned; the folder needs nothing of Wanda.

## First response and dummy mode

Use a short guided intake before displaying advanced parameters:

1. Establish whether the data are infant. ADNI (adults), ABCD (children, 9-10 y),
   HCP Aging / Development and HCP Young Adult have profiles. If the data are infant,
   stop before execution and route the user to an infant-specific MRI pipeline; never
   apply these SBCI defaults.
2. Ask what the user has: raw BIDS, prepared Python-3 SBCI inputs, or completed
   connectivity matrices. Detect the answer from the selected folder when
   possible instead of requiring the user to understand those terms.
3. Work out which machine the commands run on (Longleaf, a lab server, or the user's
   own computer; see "Where it runs") from the session rather than by asking, and say
   what that machine can run. Inspection and execution are separate actions.
4. Summarize the selected route, the first blocker, expected outputs, and the
   next safe action in plain language. Put command lines and scheduler settings
   behind an Advanced section.

Start with `mode: self_test` when no patient data is available. For a raw BIDS,
partially processed, or SBCI-ready subject, use `mode: inspect`. Read
`manifest.workflow.inventory` and `manifest.workflow.plan`; explain the first
blocked stage in plain language. Never start hours-long preprocessing during
inspection.

For a no-code local check, copy
`<pipeline>/workflow/sbci_self_test.example.json` to the selected input folder as
`sbci_local.json` and run the entry point once inside the image, as
[references/container_execution.md](references/container_execution.md) shows. The expected
result is `completed_local_runtime_self_test` with `scientificAlgorithmRan: false`.

Use the route table and preflight contract in
[references/guided_execution.md](references/guided_execution.md). Its UI flow
is informed by Wanda CyberBench's public, plain-language entry experience and
the read-only Longleaf brain-MRI skill, but this skill's SBCI scientific input
contract remains authoritative.

For multi-pipeline workflows, read
[references/orchestration.md](references/orchestration.md). Use isolated
producer environments plus a durable shared artifact directory and
`<pipeline>/workflow/contracts/sbci.handoff.schema.json`. Inspection writes an orchestration plan
and handoff template. Candidate skills are suggestions only until their actual
files pass the SBCI handoff and scientific input contracts. Do not claim or
attempt automatic cross-skill invocation until Wanda provides a documented API.
After a producer run, an approved `preprocess` invocation may consume exactly
one validated handoff by copying its declared artifacts into the isolated SBCI
work tree. The consumer verifies SHA-256 hashes, records producer provenance,
refuses conflicting destinations, never edits producer artifacts, replans the
workflow, and stops before executing the next stage.

The entry point, which the job script calls once per stage inside the image, is:

```text
python3 run_pipeline.py --input <input folder> --output <output folder>
```

It writes `files/sbci_local.template.json`, `local_adapter_manifest.json`, and
`reports/sbci_local_report.html` even when inputs or runtime components are
missing.

Read `manifest.workflow.runtime.components` as the source of truth for what the
run can use. A pipeline card in CyberNeuro's list only proves that an adapter
or description exists; it does not prove that its native commands are
available. Report the four states plainly: `installed`, `installable`,
`user_action`, and `optional_not_selected`.

Every tool the pipeline runs is in the `sbci-full` container image; nothing is
installed on the machine. Read
[references/container_execution.md](references/container_execution.md) before
fetching or running it. The image holds FSL, ANTs, MRtrix3, FreeSurfer,
Synb0-DISCO and the two Python environments, and no pipeline code: the job
scripts bind the pipeline's folder into the container. MATLAB (for FSFast) and
the FreeSurfer licence come from the machine. Starting the container never
counts as approval for a scientific run.
The pipeline ships `c3_main` as exactly three upload-safe chunks listed
in `<pipeline>/data/c3_main.parts.json`. `<pipeline>/workflow/c3_asset.py` must verify every chunk
and the combined SHA-256 before reconstructing an executable in the run's
writable `files/runtime_assets/` directory. Never execute a
chunk, trust an unverified concatenation, or reconstruct into patient input.
For Wanda's Longleaf operating page, set the pipeline up in a user-owned folder as
"Where it runs" says; never upload or overwrite the read-only lab reference skill. Do not
ask Wanda to recreate source code that already passed locally.
No AI service or API key is required to execute the pipeline after the run
configuration has been written.

## Modes

- `self_test`: patient-free runtime, ico4 asset, scilpy CLI, and converter
  integrity test. It does not run a scientific algorithm or create matrices.
- `inspect`: deterministic local readiness check; no scientific stage runs.
- `preprocess`: run the next raw-BIDS, preprocessing, optional PSC, or SBCI stage in a copied,
  output-side work tree. It requires `approved: true`, executes one stage per
  invocation, validates outputs, and then writes a durable resume marker.
- `quick_test`: one run, 1,000 seeds, and five surface-flow steps. This checks
  plumbing only and must never be interpreted as a scientific result.
- `production`: uses the displayed parameters and requires `approved: true`.

Never silently replace production parameters with quick-test values.

## Safety and scientific boundary

- Preserve source inputs. The runner builds a separate working tree inside the
  output folder.
- Never report success from a zero exit code alone; require expected, non-empty,
  parseable SC and FC artifacts.
- Display `n_runs`, `n_seed`, `steps`, `rng`, `bandwidth`, `resolution`, and ROI
  labels before production execution.
- Accept only the bundled and validated `ico4` resolution.
- Before any scientific stage, validate NIfTI grids and affines, tissue-map
  ranges, requested atlas labels, FreeSurfer surface/annotation vertex counts,
  and FSFast residual dimensions/timepoints.
- If upstream FreeSurfer, diffusion/fODF, or FSFast products are missing, show
  the resumable preprocessing plan and its runtime/license blockers.
- Keep `workflow.run_psc: false` unless the user explicitly wants the separate
  PSC atlas connectome. SBCI never consumes `psc_connectome/`. PSC is not part
  of the validated release.
- Label reduced quick-test outputs as non-scientific.
- The entry point itself uses no SSH, passwords or cluster paths; the job
  scripts add Slurm where there is one.
- Never relabel XCP-D or QSIRecon atlas connectomes as SBCI output. Those
  parcellated matrices are scientifically different from SBCI's dense ico4
  products. Import upstream derivatives only after validating every file
  required by the accepted-input contract below.

Before any approved submission, show the resolved input and output folders;
the FreeSurfer license; the container runtime (Apptainer or Docker) and the
image; the Slurm resources where there is Slurm; and the folders bound into
the container. Keep inspection non-mutating. Submission requires a separate
explicit confirmation and must be idempotent and resumable.

## Workflow configuration

Use this default in `sbci_local.json`:

```json
"workflow": {
  "input_profile": "auto",
  "run_psc": false,
  "resume": true,
  "require_distortion_correction": true,
  "freesurfer_license": "",
  "preprocessing_config": "",
  "orchestration": {
    "mode": "manual_shared_artifacts",
    "shared_work_dir": "",
    "handoff_manifest": "",
    "verify_hashes": false,
    "consume_handoff": false
  }
}
```

Preserve `resume: true`. Require a readable FreeSurfer license; raw
single-direction DWI (ADNI) also needs Synb0-DISCO, which the image holds. Do
not silently fall back to uncorrected BOLD when `require_distortion_correction`
is true. `<pipeline>/workflow/contracts/sbci.local.schema.json` lists every setting.

## Preprocessing runtime

Wanda/CyberNeuro may run the skill controller on the host while every
scientific stage runs in the container. A command discovered on the host, in a
module/conda environment, or through another installed pipeline skill is not
therefore available to the stages: they use the image's tools only. Treat
pipeline skills as orchestration interfaces, not as automatic dependency
injection: reuse another skill only through an exposed CyberNeuro runner or a
validated handoff.

The preflight (`run_subject.sbatch --inspect`, see "Running a subject") reports
each stage's missing commands from inside the image; trust it over probing the
host. Nothing is installed or downloaded by the stages. The image is fetched
once by `<pipeline>/workflow/get_image.sbatch`, only after the user agrees to
the download (about 11 GB). The FreeSurfer licence is the user's own and is
never fabricated or bundled. PSC stays off.

The stage scripts are the pipeline's own, in `<pipeline>/preprocessing/`
(registration, FreeSurfer, fODF, FSFast) and `<pipeline>/pipeline/` (SBCI).
They call scilpy 2.x commands (ported from the historical `.py` names; see each
script's header); do not substitute commands with different arguments, and
leave `workflow.reference_scripts_dir` unset so that these scripts are used.

Read [references/end_to_end_adni.md](references/end_to_end_adni.md) before
changing or executing upstream preprocessing.

Read [references/preprocessing_execution.md](references/preprocessing_execution.md)
before running or extending `preprocess` mode. Implemented dispatch covers all
nine planned stages. DWI and fMRI correction use native bounded argv builders
(`<pipeline>/corrections/`); `prepare_data` uses the native Python 3 adapter;
the middle preprocessing/PSC stages call only allowlisted scripts; the final
SBCI stage uses the image's SBCI Python. Never skip an earlier incomplete stage.

## Choosing dataset settings

Make these choices yourself from the data; the user should not edit any file.
Set `workflow.preprocessing_config` to the profile below, by its name inside
the pipeline (the job resolves it against `<pipeline>`):

| Data | `preprocessing_config` | Also set |
|---|---|---|
| ADNI raw BIDS | `datasets/adni/profile.conf` | nothing (Synb0-DISCO is in the image) |
| ABCD BIDS data already distortion-corrected | `datasets/abcd/profile.conf` | `workflow.distortion_corrected_input: true` |
| HCP Aging / Development BIDS data already distortion-corrected | `datasets/hcp-lifespan/profile.conf` | `workflow.distortion_corrected_input: true` |
| HCP Young Adult: HCP's preprocessed DWI, the unprocessed rest run, and its spin-echo fieldmap pair in `fmap/` | `datasets/hcp-ya/profile.conf` | `workflow.distortion_corrected_input: true` and `workflow.bold_topup_fieldmaps: true` |

Each dataset folder's `README.md` in the pipeline (`<pipeline>/datasets/<name>/README.md`)
lists the files the subject folder must hold and the JSON fields that are read; read it
before the preflight.

`bold_topup_fieldmaps: true` corrects a raw BOLD with the two `fmap/*_epi` images of
opposite phase encoding (topup, then applytopup). Set it only when the BOLD itself is
uncorrected and such a pair exists; never for BOLD corrected upstream.

The data can live anywhere the user can read. ABCD or HCP
data that still needs distortion correction is not supported: tell the user so and
stop.

Data from any other dataset has no profile. Do not run it with the nearest one: the
preflight refuses a profile whose `FMRI_TR` or `INPUT_ROUTE` does not fit, and a profile
that happens to pass is still another acquisition's recipe. Tell the user that the dataset
is not supported as shipped, and that the way in is a profile of their own
([references/running_one_subject_on_wanda.md](references/running_one_subject_on_wanda.md),
"Adapting to another dataset"), whose results are unvalidated. Writing that profile is the
user's decision and needs their acquisition's facts; do not start it unasked.

The `raw` route corrects DWI with Synb0-DISCO only. A reverse phase-encoded b0 or a
fieldmap acquired for the DWI is not used by it; say so when the subject has one, since
the user may prefer to correct the DWI with it upstream and enter as corrected data.

Each shipped profile has been run end to end on one subject on this release. Say that at
intake, not only when asked.

Whether the data are already corrected is a fact to establish, not to infer from the
dataset's name. The images and sidecars can't show it, and nothing stops uncorrected data
declared as corrected: the run finishes normally with wrong results. Assume correction only
when the user says so, or the data's own documentation does. Otherwise ask one plain
question: "Has this data already been distortion corrected, for example by the HCP or ABCD
pipelines?" If nobody knows, stop and say so; do not guess.

When you ask the user to start the job, say in plain language which dataset you identified,
whether its data are already corrected and how you know, and which profile you chose.

The preflight blocks a profile that doesn't fit: its `INPUT_ROUTE` must match
`distortion_corrected_input` and `bold_topup_fieldmaps`, and its `FMRI_TR` must match the
subject's TR. Fix that by choosing the right profile or settings, not by editing the profile.

For ABCD and HCP Aging / Development, ask one plain question: should the results be
comparable with the lab's existing SBCI database for that dataset? If yes, use the
historical profile beside the recommended one (`datasets/abcd/profile.historical.conf`,
`datasets/hcp-lifespan/profile.historical.conf`), which reproduces that database's
single-shell fODF fit; otherwise use `profile.conf` (multi-shell multi-tissue
fit). Single-shell data such as ADNI is unaffected by this choice.

Use `distortion_corrected_input: true` only for data corrected before it reached
this skill (it copies instead of running Synb0/topup/eddy, and keeps every
resting-state run). Validation: each dataset's `<pipeline>/datasets/<name>/validation.md`
records the subject, date, image and numbers of its last end-to-end run. Against the lab's
databases (2026-10), the historical profiles reproduce them (ABCD, 3 subjects: cortical SC
r 0.976-0.978, FC r 0.91-0.99; HCP Aging, 1 subject: SC r 0.974, FC r 0.959); the
recommended multi-shell profiles are not compared with any database, so say that when you
use them. When a stage blocks, its manifest issue names
the setting that resolves it (`SHELL_POLICY`, `SH_ORDER` / `parameters.sh_order`,
`FMRI_TR`): change that value in `sbci_local.json` or pick the matching profile,
then rerun. Never edit stage scripts.

## Where it runs

Wanda works on Longleaf, on its Lab Server, or, through CyberNeuro Desktop, on the user's own
computer (Linux, or Windows through WSL). The scripts are not in this
skill: they are the public `SBCI_Pipeline_Py3` repository, at the release this skill was
tested with.

**Pipeline release: SBCI_Pipeline_Py3 `20261123` (commit `85d1765`).**

In the commands below `<pipeline>` is its folder on the machine that runs them, as an absolute
path: `~/.cyberbench/SBCI_Pipeline_Py3-20261123`. If `ls <pipeline>/workflow/submit.sh` fails, set it up once on that
machine (on Longleaf, from the login node):

```bash
git clone https://github.com/sbci-brain/SBCI_Pipeline_Py3.git ~/.cyberbench/SBCI_Pipeline_Py3-20261123
git -C ~/.cyberbench/SBCI_Pipeline_Py3-20261123 checkout --detach 85d1765447c2a9f3200b0752142c8b4e47173d50
git -C ~/.cyberbench/SBCI_Pipeline_Py3-20261123 rev-parse HEAD    # must start with 85d1765
```

Never pull, update or edit that folder; a newer pipeline release comes with a newer version
of this skill. Start every job with `bash <pipeline>/workflow/submit.sh`: with Slurm it calls
`sbatch`; without, it runs the job in the background on that machine and prints the process
id and the log path.

Every stage runs inside the `sbci-full` image (`sdszhauk/sbci-image:20261123`, pinned by
digest in `<pipeline>/workflow/image_pin.sh`). If the preflight says there is no image,
ask the user once whether to fetch it (about 11 GB to download; with Apptainer, 2-3 hours
packing it and room for about 35 GB while it builds), then:

```bash
bash <pipeline>/workflow/submit.sh --output=<pipeline>/get-image-%j.out <pipeline>/workflow/get_image.sbatch
```

and wait for it to finish (its log ends with `sbci-full ready`). With Apptainer the image
becomes `<pipeline>/sbci-full.sif` (`SBCI_FULL_IMAGE` names a copy elsewhere); with Docker it
is pulled into Docker.

| Machine | What it needs |
|---|---|
| Longleaf | `module load apptainer matlab` in the shell that runs the preflight and `submit.sh`; nothing to install |
| Another Slurm cluster | Apptainer and MATLAB in the shell that runs the preflight and `submit.sh`, under that site's module names (`module avail`). Ask the user for the account and partition if the site requires them, and pass them to `submit.sh` before the job script (`--account=... --partition=...`): it hands every option to Slurm. The job asks for 16 CPUs, 64 GB and 48 h |
| Linux server or desktop; Windows (WSL 2) | Apptainer or Docker (Apptainer is used where it is on PATH; `SBCI_CONTAINER=docker` chooses Docker), a Linux MATLAB on PATH for FSFast, and 16 cores and 64 GB |
| macOS | no subject can finish: FSFast needs a Linux MATLAB inside the container. Run it on Longleaf or a Linux machine |

A whole subject has been run with Apptainer under Slurm only. With Docker, fetching the
image, the self-test and the preflight have been run, and no whole subject: say so before a
Docker run starts.

On Windows the commands must run in WSL, not in Windows itself: from a Windows shell, through
`wsl.exe`; on Wanda, ask the user to turn on WSL integration in CyberNeuro Desktop's settings.
Docker there is Docker Desktop with WSL integration on for that distribution (`docker info`
answers inside WSL).

### MATLAB

MATLAB is the one program taken from the machine, and the usual reason no subject finishes.

- It must be a Linux MATLAB whose `matlab` is on PATH in the shell that starts the job. Its
  install folder is bound into the container at the same path. A MATLAB installed in Windows
  does not serve WSL.
- Its licence has to be visible from inside the container. `MLM_LICENSE_FILE` and
  `LM_LICENSE_FILE` are passed in, so a network licence (`port@server`) works that way. A
  licence file is seen only if it is inside the MATLAB install folder: other folders of the
  machine are not bound. Under Docker the job runs as the user's numeric id with `/tmp` as
  home, so an activation kept in the user's home folder is not seen.
- Validated: R2018b on Longleaf. Other releases and other licence types are untested; say so.
- Before a long job, check that MATLAB starts at all in that shell (`matlab -batch "disp(version)"`;
  before R2019a, `matlab -nodisplay -r "disp(version); exit"`). This does not prove it starts
  inside the container. The preflight only looks for the command, so a licence that fails in
  the container shows up at `fsfast`, the seventh stage, hours in. Nothing is lost: fix the
  licence and start the job again on the same output folder, and it resumes at `fsfast`.

### Memory and cores

16 cores and 64 GB is what the validation runs had. Less is untested: there is no known
minimum.

- With Slurm the job requests them. Without, nothing reserves or limits anything: FreeSurfer,
  the fODF fit and eddy use every core the job can see.
- Check what the job will get in the shell that starts it (`nproc`, `free -g`). Under WSL and
  Docker Desktop that is the virtual machine's share, not the computer's: `.wslconfig`, or
  Docker Desktop's resource settings.
- If the machine has less, tell the user both numbers, that the run is untested there, takes
  longer and may be stopped for memory, and let them choose between it and a larger machine.
  Do not change their machine's settings yourself.

### Folders

- No spaces in the path of the pipeline, the input folder, the output folder or any file
  `sbci_local.json` names: the job script splits the list of folders it binds on spaces.
- Under WSL, keep the pipeline, input and output in the Linux filesystem (the home folder).
  A Windows drive under `/mnt/` is slow, and a whole run there is untested; the preflight
  alone has been run with the subject on one.
- Without Slurm the job is a background process of that machine. It ends if the machine
  sleeps or restarts or WSL is shut down; start it again on the same output folder to resume.
  Tell the user to keep the machine awake.

On any machine:
- The preflight says which of these is missing; tell the user in plain words. FSFast is a
  preprocessing stage every route runs, so without MATLAB no subject runs, SC included:
  suggest Longleaf.
- The FreeSurfer licence is the user's own `license.txt` (free from
  https://surfer.nmr.mgh.harvard.edu/registration.html); the image has none.
- Off Slurm, check a job with `ps -p <process id>` and the end of its log: the last line is
  `finished=<time> rc=<code>`.

## Running a subject

1. Make sure the input folder holds exactly one subject (`anat/`, `dwi/`, `func/`, and
   `fmap/` for HCP Young Adult; copy `*_motion.tsv` too when present) and an empty output
   folder exists.
2. Write `sbci_local.json` in the input folder (start from
   `<pipeline>/datasets/sbci_local.example.json`):

   ```json
   {"schema_version": "1.0", "mode": "preprocess", "approved": true,
    "workflow": {"distortion_corrected_input": true,
                 "bold_topup_fieldmaps": false,
                 "freesurfer_license": "/path/to/your/freesurfer/license.txt",
                 "preprocessing_config": "<profile from the table>",
                 "stages": "all"}}
   ```

   `freesurfer_license` is the user's own licence file. Use
   `distortion_corrected_input` and `bold_topup_fieldmaps` only as the table says; for raw
   ADNI both are false. Leave out `parameters` unless the user asks for a change:
   the profile carries the dataset's recipe (the lab's ABCD database used 3 SET runs,
   HCP and ADNI 4), and a `parameters.n_runs` that disagrees with it stops the job.
   `N_RUNS` / `n_runs` counts SET tractography repetitions, not fMRI runs: any number
   of resting-state runs (one is fine) works with every profile.
3. Preflight (seconds; on Longleaf, the login node, after `module load apptainer matlab`),
   with the same script:

   ```bash
   bash -l <pipeline>/workflow/run_subject.sbatch --inspect <INPUT_DIR> <OUTPUT_DIR>
   ```

   It runs inside the image, plans every stage in `mode: inspect`,
   and prints `readyToRun`, each stage's state and missing commands and any blocker; exit 0
   means ready. Trust it over probing tool names yourself: the stages call scilpy 2.x and
   MRtrix 3 commands, not the Python 2-era names (`scil_compute_fodf`, ...).
   If it reports no image, fetch it as "Where it runs" says, then rerun the preflight. If it
   lists `matlab` as missing for `fsfast`, MATLAB is not on PATH in that shell.
4. Submit, after you have stated the dataset, correction status and profile and the user
   agrees to start a long job:

   ```bash
   bash <pipeline>/workflow/submit.sh --output=<OUTPUT_DIR>/slurm-%j.out \
     <pipeline>/workflow/run_subject.sbatch <INPUT_DIR> <OUTPUT_DIR>
   ```

   Expect about 6-18 h on 16 cores (the job asks for 16 CPUs, 64 GB and 48 h). Measured in
   the validation runs of November 2026: 6.6-8.8 h per subject; raw ADNI took 10-18 h on an earlier
   version with a slower SBCI stage. A machine with fewer cores takes longer. Report the job
   id; check progress with `squeue -u $USER` (off Slurm, `ps -p <process id>`) and
   `<OUTPUT_DIR>/slurm-<id>.out`, which prints each stage's
   status and any issue. A stage that stops prints the issue that names its fix; a rerun on
   the same output folder resumes after the last completed stage.
5. Results: the pipeline's matrices in
   `<OUTPUT_DIR>/sbci_output/files/work/<subject>/dwi_pipeline/sbci_connectome/`
   (`smoothed_sc_avg_0.005_ico4.mat`, `sub_sc_avg_0.005_ico4.mat`, `fc_avg_ico4.mat`). The
   settings used, the profile and the pipeline and image versions are saved in
   `<OUTPUT_DIR>/config/`.
6. Check them before reporting success; the log's `rc=0` is not enough.
   - `<OUTPUT_DIR>/sbci_output/local_adapter_manifest.json` must have
     `status: completed_official_runtime`, `scientificAlgorithmRan: true` and
     `validation.ready: true`.
   - All three `.mat` files exist and are not empty. If you open them (with the image's
     Python, which has what reads them; the machine's may not), read by variable name, never
     by position: `sc` and `fc` are 5,124 by 5,124, `sub_sub_sc` 19 by 19, `sub_surf_sc` 19
     by 5,124, all finite, none all zero.
   - Report what you checked and what you did not. For a shipped dataset,
     [references/running_one_subject_on_wanda.md](references/running_one_subject_on_wanda.md)
     section 6 compares the run with the dataset's validation record.

`workflow.stages` runs part of this workflow with the same script: `preprocess` stops before
the SBCI stage, `tractography` runs tractography and SC, `fc` runs FC (default `all`).
Earlier stages that are missing always run first.

## Accepted input levels

The selected batch may itself be a subject/session, contain one subject folder,
or be a data root such as `preprocessed/<subject>/<session>`. Directory names
do not select the SBCI implementation. Leave `workflow.input_profile` at `auto`
for normal use; choose `preprocessed` or `sbci_ready` only to make the input
state explicit. The deprecated `py3_preprocessed` value is accepted as an alias
for `preprocessed` so saved requests continue to work. The skill always runs
the validated Python 3 SBCI implementation. For an already prepared data tree,
the plan marks FSL, ANTs, MRtrix3, FreeSurfer and Synb0 as not
required for the selected route, while still validating their existing output
products before SBCI. The subject must include at least:

```text
dwi_pipeline/diffusion/dti/fa.nii.gz
dwi_pipeline/diffusion/fodf/fodf.nii.gz
dwi_pipeline/structure/t1_freesurfer/{surf,label,mri}/...
dwi_pipeline/structure/{aparc.a2009s+aseg,map_wm,map_gm,map_csf}.nii.gz
fmri/bold/<numeric-run>/{fc.surface.lh,fc.surface.rh,fc.mni}.nii.gz
```

Accept raw BIDS subject folders containing `anat/`, `dwi/`, and `func/` for
inventory, planning, and approval-gated staged execution. Accept
already-preprocessed folders for direct SBCI.
Raw DICOM still requires BIDS conversion before this skill.

Recognize the cleaned ADNI terminal layout
`sub-*/ses-*/psc_sbci_final_files/`. When non-empty ico4 SC and FC matrices are
present there, report `completed_connectivity` and never rerun preprocessing or
SBCI from that directory. It is an analysis/validation input, not an SBCI-ready
source tree.

For raw BIDS, require matching DWI `.bval`, `.bvec`, and `.json` sidecars plus
a BOLD `.json` sidecar. Read `workflow.inventory.rawMetadata` and
`workflow.inventory.inputIssues`. Normalize BIDS `PhaseEncodingDirection` or
Philips `PhaseEncodingAxis`, official or estimated readout/echo-spacing fields,
and BOLD `RepetitionTime`. Never substitute a cohort-wide TR or readout time
when subject metadata is absent.

Before DWI preprocessing, compare the DWI NIfTI volume count with both the
`.bval` entry count and the `.bvec` column count. A pipeline card, sidecar
presence, submitted job, or zero exit code is never sufficient evidence of a
valid run.

## Validation

For production completion, validate structural kernel outputs including
`subject_coords.npz`, `snapped_fibers.npz`, the non-empty concon `.raw` kernel,
SC `.mat/.npz` files, and functional `fc_ts.npz` plus `fc_avg_*.mat`. A quick
test can prove execution compatibility but is not scientific completion.
Final validation also requires 5,124-by-5,124 ico4 cortical matrices, matching
subcortical dimensions, finite values, and non-empty connectivity.

## Safety Notes

The host must require confirmation before any local execution. Production mode
additionally requires `approved: true` in `sbci_local.json`. Keep all generated
files inside the selected output directory.
