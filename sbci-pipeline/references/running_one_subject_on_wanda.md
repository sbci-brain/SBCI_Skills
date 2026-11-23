# Running one subject through Wanda

A walkthrough for someone who wants to process a single subject end to end. It assumes no
prior contact with the pipeline.

**Read the "What is verified" box before you plan a run.** Parts of this path have been
exercised on real data; other parts have not, and the difference matters.

---

## What is verified, and what is not

| | Status |
|---|---|
| Full preprocessing + SBCI, one Slurm job, inside the `sbci-full` image with Apptainer | **Verified** on one subject each of ADNI (raw), ABCD, HCP Aging and HCP Young Adult. The numbers are in the pipeline, `datasets/<name>/validation.md` |
| The same input twice on the same image | Surfaces, SC and FC identical on the datasets corrected upstream. Raw ADNI differs slightly from run to run (Synb0-DISCO and eddy); `datasets/adni/validation.md` gives the size |
| The Docker route | Fetching the image, the self-test and the preflight only (Docker Desktop under WSL 2). No whole subject yet |
| Inspection / pre-flight through the Wanda GUI in Plan mode | Verified on the earlier layout (2026-09/10); not repeated on this release |
| **Executing** stages from the Wanda GUI (Build mode) | **Not verified.** Every real run so far was submitted with the job script. Use the GUI to inspect and plan; submit the work through `submit.sh` |
| Functional connectivity and cortical structural connectivity | Verified against the historical Python 2 pipeline on an earlier version (FC r = 1.000000 reusing py2's fMRI stage; cortical SC total mass ratio 1.0018 on an independent re-derivation) |
| Subcortical structural connectivity | **Not validated against Python 2.** Before 2026-11-17 it ran 3.4-5.4x the py2 values; the reading of subcortical labels was corrected on that date, and this document has no comparison made since. Do not pool subcortical SC across pipeline versions |
| ABCD and HCP Aging with the historical profiles | Reproduce the lab's databases on an earlier version (2026-10): ABCD, 3 subjects, cortical SC r 0.976-0.978, FC r 0.91-0.99; HCP Aging, 1 subject, SC r 0.974, FC r 0.959 |
| Multi-shell (MSMT) fODF, the recommended ABCD and HCP profiles | **Runs on real data. Connectivity from it is not compared with any database**, and it is not interchangeable with the lab's historical databases |
| PSC (the optional atlas connectome) | Not part of the validated release |
| Other datasets | **Not validated.** See "Adapting to another dataset" |
| More than one subject per dataset | Not run on this release |

---

## 1. Prerequisites

On the machine that runs the job (these instructions use UNC Longleaf as the example):

- **Apptainer** (clusters, Linux, WSL) or **Docker**. Every tool runs inside the `sbci-full`
  image: FreeSurfer, FSL, ANTs, MRtrix3, scilpy and Synb0-DISCO are not needed on the machine.
- **MATLAB**, a Linux install on `PATH` (R2018b validated). FSFast's `selxavg3-sess` needs
  it, and the job binds it into the image. FreeSurfer 6's bundled `MCRv80` does not replace
  it. Without MATLAB no subject finishes, SC included: it is the single most common blocker.
  Its licence must work inside the container: a network licence named in `MLM_LICENSE_FILE`
  or `LM_LICENSE_FILE`, or a licence file inside the MATLAB install folder. Other releases
  and licence types are untested (the skill's "MATLAB" section).
- **A FreeSurfer `license.txt`** of your own.
- **16 cores, 64 GB of memory and about 30 GB of disk per subject.** These are what the
  validation runs had; a smaller machine is untested and there is no known minimum.
- **Paths without spaces**, and under WSL, folders in the Linux filesystem rather than on a
  Windows drive under `/mnt/`.

On another Slurm cluster, load that site's Apptainer and MATLAB modules, and give `submit.sh`
the account and partition the site requires, before the job script's name.

On Longleaf, before the preflight and before submitting:

```bash
module load apptainer matlab
```

---

## 2. Get the pipeline and the image

The skill holds instructions only; the scripts are the public `SBCI_Pipeline_Py3`
repository at the release the skill names (`20261123`, commit `85d1765`). Clone it on a
machine with internet access (on Longleaf, the login node):

```bash
git clone https://github.com/sbci-brain/SBCI_Pipeline_Py3.git ~/.cyberbench/SBCI_Pipeline_Py3-20261123
cd ~/.cyberbench/SBCI_Pipeline_Py3-20261123
git checkout --detach 85d1765447c2a9f3200b0752142c8b4e47173d50
python3 -m unittest discover -s tests
```

Expect `OK`; tests that need VTK or nibabel skip. The suite needs no image and no modules.

Then fetch the image, once (about 11 GB to download; with Apptainer, 2-3 hours packing):

```bash
bash workflow/submit.sh --output=$PWD/get-image-%j.out workflow/get_image.sbatch
```

Its log ends with `sbci-full ready`. See `container_execution.md`.

---

## 3. Lay out the subject

The pipeline reads a BIDS-style directory. One subject:

```
input/
├── sbci_local.json
└── sub-XXXXXXX/
    ├── anat/  sub-XXXXXXX_T1w.nii.gz
    ├── dwi/   sub-XXXXXXX_dwi.nii.gz, .bval, .bvec, .json
    ├── func/  sub-XXXXXXX_task-rest_bold.nii.gz, .json
    └── fmap/  (HCP Young Adult only: the spin-echo pair)
```

Each dataset's `datasets/<name>/README.md` in the pipeline lists exactly which files and
JSON fields it needs. `sbci_local.json` beside the subject folder controls the run:

```json
{
  "schema_version": "1.0",
  "mode": "preprocess",
  "approved": true,
  "workflow": {
    "preprocessing_config": "datasets/adni/profile.conf",
    "freesurfer_license": "/path/to/license.txt",
    "distortion_corrected_input": false,
    "bold_topup_fieldmaps": false,
    "stages": "all"
  }
}
```

Notes that save time:

- `approved: true` is a deliberate gate. Nothing scientific runs without it.
- `preprocessing_config` is the dataset profile: its name inside the pipeline, or a path to
  your own copy. The stage scripts read their settings from it.
- `mode` values: `inspect` (read-only), `preprocess` (run the next stage), `production`
  (full SBCI on prepared input), `quick_test` (tiny non-scientific run), `self_test` (no
  subject needed). The job script uses `preprocess` and calls the entry point once per stage.
- A rerun on the same output folder skips stages whose outputs already exist and validate.

Start from `datasets/sbci_local.example.json` rather than retyping this.

---

## 4. Inspect before you run

Always do this first. It is read-only and takes seconds.

**In Wanda:** open the workspace containing your data, start a session, set the mode
selector to **Plan** (not Build), and ask it to inspect your subject path and report which
stages the planner judges complete plus the pre-flight result.

**Equivalently, on the command line** (on Longleaf, the login node):

```bash
bash -l ~/.cyberbench/SBCI_Pipeline_Py3-20261123/workflow/run_subject.sbatch --inspect /path/to/input /path/to/output
```

It runs inside the image and prints `readyToRun`, each stage's state and missing commands,
and any blocker; it exits 0 when ready. The full report is
`output/inspect/local_adapter_manifest.json`. The fields that matter:

- `status` — `documented_blocked_local_preflight` means something is missing; the `issues`
  array names it.
- `workflow.plan.stages` — each stage's state.

A blocked pre-flight almost always means a missing command (usually `matlab`), a missing
file in the subject folder, or a profile that does not fit the data, and the issue text
names it exactly. Fix that before submitting anything.

> **Expect a consent dialog.** If your data sits outside the Wanda workspace directory, the
> agent will ask permission to read it. That is your decision to make.

---

## 5. Run the stages

The pipeline has seven preprocessing stages, then SBCI:

| Stage | What it does |
|---|---|
| `dwi_correction` | raw input: Synb0-DISCO → topup → eddy; corrected input: a copy |
| `fmri_correction` | distortion correction of the BOLD (FUGUE, or topup on a fieldmap pair), or a copy |
| `prepare_data` | Gradients, reorientation, staging |
| `t1_dwi_registration` | T1↔DWI registration, DTI metrics |
| `freesurfer` | `recon-all` |
| `fodf_tissue` | Tissue maps + fODF |
| `fsfast` | FSFast cleaning, surface/MNI projection (MATLAB) |
| `sbci` | SET tractography ×4, surfaces, SC, FC |

FreeSurfer and the SBCI stage take most of the time. The whole subject took 6.6-8.8 h on 16
cores in the validation runs of November 2026; allow 6-18 h.

Submit the whole subject as one job. It runs every stage inside the image, one
`run_pipeline.py` call per stage:

```bash
bash ~/.cyberbench/SBCI_Pipeline_Py3-20261123/workflow/submit.sh --output=/path/to/output/slurm-%j.out \
  ~/.cyberbench/SBCI_Pipeline_Py3-20261123/workflow/run_subject.sbatch /path/to/input /path/to/output
```

Use `submit.sh`, not `sbatch` directly: Slurm runs a copy of the script from its spool
folder, and `submit.sh` tells it where the pipeline is. Without Slurm, `submit.sh` runs the
job in the background and prints the process id and the log.

The input folder holds one subject and `sbci_local.json` (`"mode": "preprocess"`,
`"approved": true`); the output folder must exist. Rerunning on the same output folder
resumes after the last completed stage. The script refuses input or output paths under a
folder listed in `SBCI_READONLY_ROOTS` (a site sets it for shared, read-only data). Each stage's status and any blocking issue are printed to `slurm-<id>.out`.

---

## 6. Check the results

Connectivity outputs land in
`output/sbci_output/files/work/<subject>/dwi_pipeline/sbci_connectome/`:

| File | Content |
|---|---|
| `fc_avg_ico4.mat` | Functional connectivity, 5124 × 5124 |
| `smoothed_sc_avg_0.005_ico4.mat` | Cortical structural connectivity, 5124 × 5124 |
| `sub_sc_avg_0.005_ico4.mat` | Subcortical SC (19 × 19 and 19 × 5124) — **see the caveat below** |

`output/config/` holds the configuration and profile as used and `versions.json` (the hash
of the pipeline's files and the image's name).

Confirm the run was scientifically complete, not a quick test:

```bash
python3 -c "
import json; m = json.load(open('output/sbci_output/local_adapter_manifest.json'))
print(m['status'], m['scientificAlgorithmRan'], (m.get('validation') or {}).get('ready'))"
```

You want `completed_official_runtime True True`. To compare a finished run with a dataset's
record: `python3 tests/check_validation_record.py output datasets/<name>/validation.md`, from
the pipeline folder.

> **Subcortical SC caveat.** These `.mat` files contain several variables and different
> pipeline versions store them in different orders. When comparing runs, **load by variable
> name** (`fc`, `sc`, `sub_sub_sc`, `sub_surf_sc`) — taking "the first key" silently
> compares different matrices.
>
> Subcortical SC is an unnormalised segment count and is not validated against the Python 2
> pipeline. Never pool subcortical SC across pipeline versions or across different input
> routes. Cortical SC and FC are safe to pool within one profile.

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `no sbci-full image at …`, `Docker has no image …` | The image was not fetched on this machine | Run `get_image.sbatch` once (§2) |
| `needs Apptainer or Docker on PATH` | No container runtime in this shell | `module load apptainer` on a cluster, or install one |
| `cannot find the pipeline folder` | The job was started with `sbatch` directly | Start it with `workflow/submit.sh` |
| The preflight lists `matlab` as missing for `fsfast` | MATLAB is not on `PATH` in the shell that ran it | `module load matlab`, or put a Linux MATLAB on `PATH` |
| `$'\r': command not found` | A shell script carries CRLF line endings | Clone on Linux; never edit these scripts on Windows without converting |
| `fast_selxavg3b.glnxa64: error while loading shared libraries: libmwlaunchermain.so` | FreeSurfer's bundled MCR is incomplete and no MATLAB was found | Put a real `matlab` on `PATH` |
| `t1_dwi_registration ended in state blocked: DWI has N non-zero shells … sets no SHELL_POLICY` | Multi-shell DWI and no declared shell policy | Deliberate stop — use a profile that sets `SHELL_POLICY` (see §8) |
| `fodf_tissue ended in state blocked: SH order L needs at least … unique gradient directions` | `SH_ORDER` too high for the acquisition | Lower `SH_ORDER` (or `parameters.sh_order`) to the order the message names |
| `fsfast ended in state blocked: … RepetitionTime is X s, but … declares FMRI_TR=…` | The profile's fMRI timing is for another protocol | Use the profile for this acquisition (see §8) |
| `fsfast ended in state blocked: fsfast needs the distortion-corrected BOLD` | `fmri_correction` has not produced `fmri/bold_distcorr.nii.gz` | Run the correction stage first; uncorrected BOLD is never used |
| `fsfast` fails with a MATLAB licence error although the preflight passed | The preflight only looks for the `matlab` command; the licence is not visible inside the container | Make the licence reachable (see §1), then submit again on the same output folder: the run resumes at `fsfast` |
| Results, or `__pycache__` folders in the pipeline's folder, belong to root | A `docker run` typed by hand without `--user` | Run it with `--user "$(id -u):$(id -g)" -e HOME=/tmp`, as `container_execution.md` shows |
| The job vanished with no `finished=` line in its log (no Slurm) | The machine slept or restarted, WSL was shut down, or the job was stopped for memory | Submit again on the same output folder; it resumes after the last completed stage |
| `STOPPED: preprocessing call N failed` | A stage failed | The line above names the issue; `output/logs/call_N.err` has the stage's own output. Fix the cause and submit again |

---

## 8. Adapting to another dataset

**Each shipped profile is written for one acquisition**: `datasets/adni`, `datasets/abcd`,
`datasets/hcp-lifespan` and `datasets/hcp-ya`. Other datasets need changes, and they fall
into three tiers of difficulty. `datasets/README.md` in the pipeline explains every profile
setting and how to add a dataset folder.

### Tier 1 — set it in JSON, no code changes

`parameters` in `sbci_local.json`:

| Key | Default | Meaning |
|---|---|---|
| `n_runs` | 4 | SET tractography runs; may not disagree with the profile's `N_RUNS` |
| `n_seed` | 1000 | Seeds per run (× 1000 streamlines) |
| `steps` | 75 | Surface-flow steps |
| `rng` | 1234 | Random seed |
| `bandwidth` | 0.005 | Smoothing kernel for SC |
| `rois` | 19 subcortical labels | FreeSurfer label IDs |
| `resolution` | `ico4` | **`ico4` only** — other values are rejected |
| `sh_order` | *(unset)* | fODF spherical-harmonic order; optional. Unset means `SH_ORDER` from the profile, else 6 (8 for multi-shell). If both are set and differ, the stage blocks rather than pick one |

`workflow.distortion_corrected_input` (default `false`): declare that the DWI and BOLD were
already distortion/eddy corrected before reaching this skill — true of the lab's ABCD and
HCP BIDS trees. The two correction stages then copy the images to where later stages read
them, run no command, and record the declaration in their markers; phase-encoding/readout
metadata and Synb0 are no longer required. Do not set it for raw scanner data. Each shipped
profile names the input it was written for in `INPUT_ROUTE` (`raw`, `corrected` or
`corrected_dwi_raw_bold`); the preflight stops if these settings disagree with it, or if the
subject's TR differs from the profile's `FMRI_TR`.

**Dataset profiles** shipped with the pipeline: ADNI — `datasets/adni/profile.conf`; ABCD —
`datasets/abcd/profile.conf`; HCP Aging/Development — `datasets/hcp-lifespan/profile.conf`;
HCP Young Adult — `datasets/hcp-ya/profile.conf`. ABCD and HCP Aging/Development each have a
`profile.historical.conf` beside it that reproduces the lab's existing database for that
dataset (single-shell fODF fit across the shells it used, `FODF_MODEL=ssst`) — choose it
when new results must be pooled with that database. The ABCD and HCP profiles go with
`distortion_corrected_input: true`, which also keeps every resting-state run (ABCD has
four; SBCI concatenates them, as the historical database did). When a BOLD series has no
JSON sidecar, its TR is read from the NIfTI header, but only if the header declares its
time unit.

### Tier 2 — supply your own profile, still no pipeline edits

Point `workflow.preprocessing_config` at *your* copy of the closest profile. The stage
scripts read it, so you can change:

- `N_RUNS`, `STEPS`, `RNG`, `BANDWIDTH`, `ROIS`
- `SHELL_POLICY` — which b-value shells reach DTI and fODF (below)
- `SH_ORDER`, `FODF_MODEL` — the fODF (below)
- `FMRI_TR`, `FMRI_SKIP_SECONDS`, `FMRI_POLYFIT`, `FMRI_STC`, `FMRI_MOTION_REGRESSORS` — fMRI timing (below)

A profile holds settings only: tool paths come from the image and a run's paths from its
`sbci_local.json`. Keep `INPUT_ROUTE` true to the data.

**`SHELL_POLICY`** (read by `preprocessing/preproc_step2_t1_dwi_registration.sh`):

| Value | DTI uses | fODF uses |
|---|---|---|
| `nearest_1000` | the non-zero shell nearest b = 1000 | the same shell |
| `all` | the non-zero shell nearest b = 1000 | every non-zero shell |
| `explicit` | `DTI_BVALS` as written | `FODF_BVALS` as written |

`DTI_BVALS` / `FODF_BVALS` are read **only** under `explicit`. Shells are b-values rounded
to the nearest 100. Single-shell data needs no policy. **Multi-shell data with no
`SHELL_POLICY` stops the registration stage before it runs**, with the shells it found in
`local_adapter_manifest.json` → `issues` and a non-zero exit.

`FODF_TOLERANCE` (default 20; 50 under `all`) is how far a b-value may sit from a listed
fODF shell and still be kept. scilpy 2.x keeps `|b - shell| <= tolerance`; the legacy
scilpy behind the lab's historical outputs kept `< tolerance`, so at 20 it dropped HCP's
b = 2980 volumes. The historical profiles set 19 to reproduce that selection.

**The fODF model follows the shells.** If one non-zero shell reaches the fODF stage,
`preprocessing/preproc_step4_fodf_estimation.sh` fits single-shell single-tissue CSD
(`scil_fodf_ssst`). If several do — which happens only under `SHELL_POLICY=all` or an
`explicit` multi-shell `FODF_BVALS` — it fits **multi-shell multi-tissue CSD**
(`scil_frf_msmt` + `scil_fodf_msmt`, using the FAST WM/GM/CSF masks) and writes only the WM
fODF, to the same `fodf/fodf.nii.gz`. `FODF_MODEL=ssst` overrides this and fits single-shell
CSD to however many shells are given — the lab's historical ABCD/HCP recipe; the default is
`FODF_MODEL=auto`.

**`SH_ORDER`** (default 6 for one shell, 8 for several). Order `L` needs at least
`(L+1)(L+2)/2` unique gradient directions (order 6 → 28, 8 → 45, 10 → 66). Before the fODF
stage runs, the executor counts the unique directions (antipodal pairs and near-repeats
within 5° count once, across all shells) and **blocks** an order the data cannot support,
naming both numbers and the highest order that would work.

**fMRI timing** (read by `preprocessing/preproc_step5_fmri.sh`):

| Key | ADNI | Meaning |
|---|---|---|
| `FMRI_TR` | `3` | If set, every subject's BIDS `RepetitionTime` must equal it, otherwise the stage blocks. Unset: the TR is taken from each subject's BIDS JSON |
| `FMRI_SKIP_SECONDS` | `12` | Leading time dropped for T1 saturation; frames = round(seconds / TR) — 4 at TR 3 s, 15 at 0.8 s |
| `FMRI_POLYFIT` | `2` | Detrending polynomial order |
| `FMRI_STC` | `siemens` | FSFast slice-timing order (`siemens`, `up`, `down`, `odd`, `even`) or `none` — use `none` for multiband data |
| `FMRI_MOTION_REGRESSORS` | `mcextreg` | `mcextreg`: FSFast's own motion estimates. `tsv`: each run's BIDS `*_motion.tsv` (header and first column dropped, 6 regressors) — the lab's ABCD/HCP recipe |

The fMRI stage uses only the distortion-corrected BOLD (`fmri/bold_distcorr.nii.gz`) and
**stops** if it is absent.

### Tier 3 — requires editing the pipeline

Any stage script that calls a **command the pipeline does not already declare** is refused
before it runs, with `Refusing undeclared <stage> command: <name>`. Declaring a new command
means editing two files:

- `workflow/planner.py` → `STAGE_COMMANDS`
- `workflow/preprocessing_runtime.py` → `COMPONENTS`

and a test (`test_ported_stage_scripts_match_declared_commands`) enforces that the shipped
scripts and the declared list agree. A new tool also has to be in the image. An edited
pipeline is no longer the release this skill names: say so in anything produced with it.

### Worked example: HCP or ABCD

Both are **multi-shell** and have far more diffusion directions than ADNI, so both the
fODF model and its angular resolution change.

| | ADNI | HCP Young Adult | ABCD |
|---|---|---|---|
| Shells | b = 1000 | b = 1000/2000/3000 | b = 500/1000/2000/3000 |
| Directions | ~55 | ~270 | ~96 |
| fMRI TR | 3 s | 0.72 s | 0.8 s |

1. **The shell policy** is set in the shipped profiles: every shell reaches the fODF stage,
   which fits multi-shell multi-tissue CSD. `nearest_1000` would give a single-shell run
   from a fraction of the data — a smoke test, not science.
2. **SH order** follows the profile; the stage refuses an order the directions cannot
   support.
3. **fMRI**: the profiles set the dataset's TR and `FMRI_STC=none` for multiband BOLD. The
   number of skipped frames follows the TR.
4. **Comparability.** The lab's existing ABCD SBCI database was built with single-shell CSD fit
   to b = 1000/2000/3000 together. Multi-shell multi-tissue fODF is a different model, so new
   ABCD results are **not interchangeable** with that database — use
   `datasets/abcd/profile.historical.conf` (or `datasets/hcp-lifespan/profile.historical.conf`)
   when they must be.

**Validation is one subject deep on this release.** Treat further subjects as checks of that
result, not as established, and do not assume one dataset's validation transfers to another.

---

## 9. Getting help

When reporting a problem, include:

- `output/local_adapter_manifest.json` and `output/sbci_output/local_adapter_manifest.json`
  (the `issues` array especially)
- The job's `.out` file
- The stage logs from `output/logs/`
- `output/config/versions.json`

Do not send subject-level imaging data, connectivity matrices or manifests containing
subject identifiers to anyone not covered by your data-use agreement.
