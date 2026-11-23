# SBCI Skills

Agent skills for the [SBCI pipeline](https://github.com/sbci-brain/SBCI_Pipeline_Py3): the
instructions an AI agent follows to run one subject from MRI to continuous structural and
functional connectomes. They were written for Wanda (CyberBench-Neuro), can be followed by any
agent that runs shell commands on the machine that runs the jobs, and hold instructions
only, no code.

SBCI, Surface-Based Connectivity Integration (Cole et al., *Human Brain Mapping*, 2021),
represents structural and functional connectivity as functions on the cortical surface
instead of between atlas regions.

| Folder | Skill |
|---|---|
| `sbci-pipeline/` | one subject end to end: intake, dataset settings, setup, preflight, the run, and checking the results (`SKILL.md` plus `references/`) |

## What the skill does

- Works out what the user has (raw BIDS, prepared inputs, or finished matrices) and which
  dataset profile fits: ADNI, ABCD, HCP Aging / Development or HCP Young Adult.
- Sets the pipeline up on the machine that runs the jobs: a clone of
  [SBCI_Pipeline_Py3](https://github.com/sbci-brain/SBCI_Pipeline_Py3) at the commit the
  skill names, and the `sbci-full` container image
  ([SBCI_Images](https://github.com/sbci-brain/SBCI_Images)), with Apptainer or Docker.
- Runs a preflight in seconds, then one job for every stage, through Slurm where there is
  one and in the background elsewhere.
- Refuses to report success from an exit code: it checks the connectomes themselves.


## Using it

Upload `sbci-pipeline/` to the agent platform as one skill. Nothing else is uploaded: the
agent clones the pipeline and fetches the image on the machine that runs the jobs.

`references/running_one_subject_on_wanda.md` is also a walkthrough a person can follow by
hand, and says which parts of the path have been verified on real data and which have not.

## Tests

```bash
python -m unittest discover -s tests
```

They check that the skill names one pipeline release consistently, holds no code, and uses
the pipeline's current layout.

## References

- **SBCI** — Cole, M., Murray, K., St-Onge, E., Risk, B., Zhong, J., Schifitto, G.,
  Descoteaux, M., & Zhang, Z. (2021). Surface-Based Connectivity Integration: An atlas-free
  approach to jointly study functional and structural connectivity. *Human Brain Mapping*,
  42(11), 3481–3499. <https://doi.org/10.1002/hbm.25447>
