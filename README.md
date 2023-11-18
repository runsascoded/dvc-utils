# dvc-utils
CLI for diffing [DVC] files at two commits (or one commit vs. current worktree), optionally passing both through another command first

## Installation
```bash
pip install dvc-utils
```

## Usage
```bash
dvc-utils --help
# Usage: dvc-utils [OPTIONS] COMMAND [ARGS]...
#
# Options:
#   --help  Show this message and exit.
#
# Commands:
#   diff  Diff a DVC-tracked file at two commits (or one commit vs. current
#         worktree), optionally passing both through another command first
```

### `dvc-utils diff`
```bash
dvc-utils diff --help
# Usage: dvc-utils diff [OPTIONS] [cmd...] <path>
#
#   Diff a file at two commits (or one commit vs. current worktree), optionally
#   passing both through `cmd` first
#
#   Examples:
#
#   dvc-utils diff -r HEAD^..HEAD wc -l foo.dvc  # Compare the number of lines
#   (`wc -l`) in `foo` (the file referenced by `foo.dvc`) at the previous vs.
#   current commit (`HEAD^..HEAD`).
#
#   dvc-utils diff md5sum foo  # Diff the `md5sum` of `foo` (".dvc" extension is
#   optional) at HEAD (last committed value) vs. the current worktree content.
#
# Options:
#   -r, --refspec TEXT  <commit 1>..<commit 2> (compare two commits) or <commit>
#                       (compare <commit> to the worktree)
#   -S, --no-shell      Don't pass `shell=True` to Python `subprocess`es
#   -v, --verbose       Log intermediate commands to stderr
#   --help              Show this message and exit.
```

## Examples
Use [`parquet2json`] to observe schema changes to a Parquet file, in a given commit from [neighbor-ryan/nj-crashes](https://github.com/neighbor-ryan/nj-crashes):
```bash
parquet_schema() {
    parquet2json "$1" schema
}
export -f parquet_schema
commit=7fa6a07
path=njdot/data/2001/NewJersey2001Accidents.pqt.dvc
dvc-utils diff -r $commit^..$commit parquet_schema $path
```
<details><summary>Output</summary>

```diff
2d1
<   OPTIONAL BYTE_ARRAY Year (STRING);
8,10d6
<   OPTIONAL BYTE_ARRAY Crash Date (STRING);
<   OPTIONAL BYTE_ARRAY Crash Day Of Week (STRING);
<   OPTIONAL BYTE_ARRAY Crash Time (STRING);
14,17c10,13
<   OPTIONAL BYTE_ARRAY Total Killed (STRING);
<   OPTIONAL BYTE_ARRAY Total Injured (STRING);
<   OPTIONAL BYTE_ARRAY Pedestrians Killed (STRING);
<   OPTIONAL BYTE_ARRAY Pedestrians Injured (STRING);
---
>   OPTIONAL INT64 Total Killed;
>   OPTIONAL INT64 Total Injured;
>   OPTIONAL INT64 Pedestrians Killed;
>   OPTIONAL INT64 Pedestrians Injured;
20,21c16,17
<   OPTIONAL BYTE_ARRAY Alcohol Involved (STRING);
<   OPTIONAL BYTE_ARRAY HazMat Involved (STRING);
---
>   OPTIONAL BOOLEAN Alcohol Involved;
>   OPTIONAL BOOLEAN HazMat Involved;
23c19
<   OPTIONAL BYTE_ARRAY Total Vehicles Involved (STRING);
---
>   OPTIONAL INT64 Total Vehicles Involved;
29c25
<   OPTIONAL BYTE_ARRAY Mile Post (STRING);
---
>   OPTIONAL DOUBLE Mile Post;
47,48c43,44
<   OPTIONAL BYTE_ARRAY Latitude (STRING);
<   OPTIONAL BYTE_ARRAY Longitude (STRING);
---
>   OPTIONAL DOUBLE Latitude;
>   OPTIONAL DOUBLE Longitude;
51a48
>   OPTIONAL INT64 Date (TIMESTAMP(MICROS,false));
```
</details>

Diff the first row of the Parquet file above (pretty-printed as JSON), before and after the given commit:

```bash
pretty_print_first_row() {
    parquet2json "$1" cat -l 1 | jq .
}
export -f pretty_print_first_row
dvc-utils diff -r $commit^..$commit pretty_print_first_row $path
```

<details><summary>Output</summary>

```diff
2d1
<   "Year": "2001",
8,10d6
<   "Crash Date": "12/21/2001",
<   "Crash Day Of Week": "F",
<   "Crash Time": "1834",
14,17c10,13
<   "Total Killed": "0",
<   "Total Injured": "0",
<   "Pedestrians Killed": "0",
<   "Pedestrians Injured": "0",
---
>   "Total Killed": 0,
>   "Total Injured": 0,
>   "Pedestrians Killed": 0,
>   "Pedestrians Injured": 0,
20,21c16,17
<   "Alcohol Involved": "N",
<   "HazMat Involved": "N",
---
>   "Alcohol Involved": false,
>   "HazMat Involved": false,
23c19
<   "Total Vehicles Involved": "2",
---
>   "Total Vehicles Involved": 2,
29c25
<   "Mile Post": "",
---
>   "Mile Post": null,
47,48c43,44
<   "Latitude": "",
<   "Longitude": "",
---
>   "Latitude": null,
>   "Longitude": null,
51c47,48
<   "Reporting Badge No.": "830"
---
>   "Reporting Badge No.": "830",
>   "Date": "2001-12-21 18:34:00 +00:00"
```
</details>



[DVC]: https://dvc.org/
[`parquet2json`]: https://github.com/jupiter/parquet2json
[neighbor-ryan/nj-crashes]: https://github.com/neighbor-ryan/nj-crashes
