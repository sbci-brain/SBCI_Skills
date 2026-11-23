# SBCI container execution

Every stage of the pipeline runs inside one container image, `sbci-full`. Nothing is
installed on the machine that runs the job. Its recipe and its description are in the public
`SBCI_Images` repository (https://github.com/sbci-brain/SBCI_Images).

## Scope

The image holds every tool a subject needs, from raw BIDS to connectivity: FreeSurfer 6.0.0,
FSL 6.0.7.18, ANTs 2.6.0, MRtrix3 3.0.8, Synb0-DISCO v3.1, the preprocessing Python
environment and the SBCI-stage Python (both with scilpy 2.3.0), and the MNI template used
for brain extraction. It contains no patient data and needs no network at run time.

It does not hold:

- **the pipeline's code.** The job scripts bind the pipeline's folder (`<pipeline>`) into the
  container and name it in `SBCI_PIPELINE`, so one set of scripts runs: the clone's.
- **MATLAB.** FSFast needs it; the job binds this machine's Linux MATLAB (`matlab` on `PATH`)
  into the container.
- **a FreeSurfer licence.** The user's own file is named in `sbci_local.json` and bound in.

The pipeline ships the native x86-64 `c3_main` kernel as three `c3_main.part-*` files in
`<pipeline>/data/concon/` rather than as one 40 MB executable.
`<pipeline>/data/c3_main.parts.json` fixes their order, sizes, individual hashes, combined
size, and combined SHA-256. `<pipeline>/workflow/c3_asset.py` verifies all of those values and
reconstructs the executable atomically under the run's output at
`files/runtime_assets/concon/c3_main`; the input tree stays read-only.

## The pinned image

`<pipeline>/workflow/image_pin.sh` names the image by repository, tag and digest
(`sdszhauk/sbci-image:20261123` for this release). Every clone of a release therefore runs on
the same image. Do not identify the image only by its tag, and do not substitute another
image unless the user asks; `SBCI_FULL_IMAGE` (Apptainer) and `SBCI_DOCKER_IMAGE` (Docker)
exist for that case and the run records which image it used in
`<OUTPUT_DIR>/config/versions.json`.

## Fetching it

Once per machine, after the user agrees to the download (about 11 GB):

```text
bash <pipeline>/workflow/submit.sh --output=<pipeline>/get-image-%j.out <pipeline>/workflow/get_image.sbatch
```

- With Apptainer it builds `<pipeline>/sbci-full.sif`: 2-3 hours on 4 cores, and room for
  about three times the image beside it while it builds.
- With Docker it pulls the image into Docker (about 40 GB unpacked).

It needs internet. It ends by checking that the image sets the variables the pipeline reads
(`SBCI_ENV`, `SBCI_CORE_PY`, `SBCI_TEMPLATE_DIR`, `FSLDIR`, `FREESURFER_HOME`) and has the
tools on `PATH`; its log ends with `sbci-full ready`. A failed check means the image is not
the one this release was tested with.

## Apptainer or Docker

The job scripts use Apptainer where it is on `PATH` (clusters) and Docker otherwise.
`SBCI_CONTAINER=apptainer` or `SBCI_CONTAINER=docker` chooses. On a cluster, load Apptainer
in the shell that submits (`module load apptainer matlab` on Longleaf).

Outside the image, a job script runs itself again inside it, with these folders at their own
paths: the pipeline, the input folder and its subject, the output folder, every path
`sbci_local.json` names (the licence, a profile outside the pipeline), and MATLAB. Nothing
else of the machine is visible to the stages. With Docker the job runs as the user who
started it, so the outputs are that user's.

The Docker route has been run for fetching the image and for the preflight; a whole subject
has so far been run with Apptainer only. Say so when the user's machine has only Docker.

## Checks before any subject data

After fetching, run the image's own check and the patient-free self-test:

```text
apptainer exec <pipeline>/sbci-full.sif /opt/sbci/check_tools.sh        # "check_tools: all present"
```

Then put `<pipeline>/workflow/sbci_self_test.example.json` in an empty input folder as
`sbci_local.json` and run the entry point once inside the image (the preflight script
cannot do this: it always inspects). With Apptainer:

```text
apptainer exec --bind <pipeline>,<input>,<output> <pipeline>/sbci-full.sif \
  bash -c 'cd <pipeline> && PATH=$SBCI_ENV/bin:$PATH python3 run_pipeline.py --input <input> --output <output>'
```

With Docker, the same `bash -c` command after
`docker run --rm -v <pipeline>:<pipeline> -v <input>:<input> -v <output>:<output> <image>`.
Require in `<output>/local_adapter_manifest.json`: `status: completed_local_runtime_self_test`,
`runtime.ready: true`, `selfTest.ready: true`, `selfTest.patientDataUsed: false`,
`scientificAlgorithmRan: false` and `officialScientificPipelineRan: false`.

Keep the FreeSurfer license and other secrets outside any image. Never put subject data into
an image or a build context.

## Success criteria

Container success requires the normal SBCI output validation. Do not infer
success from image health, process exit code, Docker status, or Slurm status.
Validate named cortical and subcortical matrices, ico4 dimensions and ordering,
finite values, and non-empty connectivity as described in
`quality_contract.md`.
