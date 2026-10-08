# nextstrain_dengue

Builds Nextstrain trees of dengue virus that combine public GenBank genomes with
genomes sequenced by the Florida Bureau of Public Health Laboratories and
assembled with [Daytona_dengue](https://github.com/BPHL-Molecular/Daytona_dengue).
The result is one Auspice JSON file per serotype, viewable at
[auspice.us](https://auspice.us).

The `ingest` and `phylogenetic` workflows are built on Nextstrain's
[dengue workflow](https://github.com/nextstrain/dengue).

## Workflows

| Folder | What it does |
|---|---|
| `ingest/` | Downloads dengue genomes from GenBank, curates the metadata and splits them by serotype |
| `local/` | Reads Daytona_dengue runs and a sample table, validates them and writes per-serotype files |
| `phylogenetic/` | Merges both sets, builds the trees and exports them for Auspice |
| `analysis/` | Reads a finished build and writes result tables |

Run them in that order. `local` reads the results of `ingest`, and
`phylogenetic` needs both.

## What to provide

Two files inside `local/input/`: `runs.yaml` and `metadata.txt`.

`runs.yaml` lists the Daytona_dengue output folders, you can list more than one run, but be sure that `metadata` includes all the samples from all runs:

```yaml
daytona_runs:
  - /path/to/daytona_output
sample_metadata: input/metadata.txt
```

Each folder holds `summary_report.txt`, `assemblies_qc_pass/pass/` and
`assemblies_qc_pass/review/`. When a sample is in more than one run, a `PASS`
copy is used over a `REVIEW` one. Between equal flags, the run listed last is
used.

`metadata.txt` is tab-delimited with one row per sample:

| Column | Notes |
|---|---|
| `sample_id` | the laboratory identifier, for example `SAMPLE26000001` |
| `collection_date` | `YYYY-MM-DD`, or `YYYY-MM-XX` when the day is unknown |
| `location` | county, spelled as in `phylogenetic/defaults/lat_longs.tsv` |
| `case_origin` | `local`, `travel-associated` or `undetermined` |
| `travel_country` | where infection likely occurred, for travel-associated cases |

An optional `host` column overrides the default host. Samples whose identifier
matches `vector_pattern` in `local/defaults/config.yaml` are treated as mosquito
pools.

## Running

Everything runs through the
[Nextstrain CLI](https://docs.nextstrain.org/projects/cli/). Confirm the setup
with `nextstrain check-setup`, then from the repository root:

```sh
nextstrain build ingest
nextstrain build local --configfile input/runs.yaml
```

On a HiPerGator, submit the `slurm/run_phylo.sh` job for the phylogenetic build. Set the
email address in it first.

After `local`, read `local/results/input_report.txt` and
`local/results/validation_report.txt` before building the trees. They list the
samples that were left out and why.

## Output

`phylogenetic/auspice/dengue_<serotype>_<gene>.json`, for the serotypes `all`,
`denv1`, `denv2`, `denv3` and `denv4`, these are built using the complete `genome` and `E` gene only.

## Analysis

`analysis/analyze_v2.py` reads one build folder and writes tables to its
`results/` subfolder: every Florida genome, the clusters and clades found, the
nearest relative of each genome, SNP distances and counts by week and county.

A build folder holds:

```
json/                   dengue_denv{1,2,3,4}_genome.json from phylogenetic/auspice/
summary_report.txt      the Daytona_dengue run summaries, concatenated if more than one run
input_report.txt        from local/results/
validation_report.txt   from local/results/
metadata.txt            the sample table given to local/
```

```sh
module load conda
python3 analysis/analyze_v2.py --build-dir /path/to/build
```

It needs only the Python standard library. Nothing else in this repository reads
the tables it writes.
