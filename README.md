# dvc-utils
CLI for diffing [DVC] files, optionally passing both through another command first

<!-- toc -->
- [Installation](#installation)
- [Usage](#usage)
    - [`dvc-utils diff`](#dvc-utils-diff)
- [Examples](#examples)
    - [Parquet file](#parquet-diff)
        - [Schema diff](#parquet-schema-diff)
        - [Row diff](#parquet-row-diff)
        - [Row count diff](#parquet-row-count-diff)
<!-- /toc -->

## Installation <a id="installation"></a>
```bash
pip install dvc-utils
```

## Usage <a id="usage"></a>
<!-- `bmdf -- dvc-utils --help` -->
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

### `dvc-utils diff` <a id="dvc-utils-diff"></a>
<!-- `bmdf -- dvc-utils diff --help` -->
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
#   -c, --color              Colorize the output
#   -r, --refspec TEXT       <commit 1>..<commit 2> (compare two commits) or
#                            <commit> (compare <commit> to the worktree)
#   -S, --no-shell           Don't pass `shell=True` to Python `subprocess`es
#   -U, --unified INTEGER    Number of lines of context to show (passes through
#                            to `diff`)
#   -v, --verbose            Log intermediate commands to stderr
#   -w, --ignore-whitespace  Ignore whitespace differences (pass `-w` to `diff`)
#   --help                   Show this message and exit.
```

## Examples <a id="examples"></a>

### Parquet file <a id="parquet-diff"></a>
See sample commands and output below for inspecting changes to [a DVC-tracked Parquet file][commit path] in [a given commit][commit].

Setup:
```bash
git clone https://github.com/hudcostreets/nj-crashes && cd nj-crashes # Clone + enter example repo
commit=c8ae28e  # Example commit that changed some DVC-tracked Parquet files
path=njdot/data/2001/NewJersey2001Accidents.pqt.dvc  # One of the changed files
```

#### Schema diff <a id="parquet-schema-diff"></a>
Use [`parquet2json`] to observe schema changes to a Parquet file:
```bash
parquet_schema() {
    parquet2json "$1" schema
}
export -f parquet_schema
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

Here we can see that various date/time columns were consolidated, and several stringly-typed columns were converted to ints, floats, and booleans.

</details>

#### Row diff <a id="parquet-row-diff"></a>
Diff the first row of the Parquet file above (pretty-printed as JSON using [`jq`]), before and after the given commit:

```bash
pretty_print_first_row() {
    # Print first row of Parquet file as JSON, pretty-print with jq
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

This reflects the schema changes above.

</details>

#### Row count diff <a id="parquet-row-count-diff"></a>
```bash
parquet_row_count() {
    parquet2json "$1" rowcount
}
export -f parquet_row_count
dvc-utils diff -r $commit^..$commit parquet_row_count $path
```

This time we get no output; [the given `$commit`][commit] didn't change the row count in the DVC-tracked Parquet file [`$path`][commit path].

[DVC]: https://dvc.org/
[`parquet2json`]: https://github.com/jupiter/parquet2json
[hudcostreets/nj-crashes]: https://github.com/hudcostreets/nj-crashes
[Parquet]: https://parquet.apache.org/
[commit]: https://github.com/hudcostreets/nj-crashes/commit/c8ae28e64f4917895d84074913f48e0a7afbc3d7
[commit path]: https://github.com/hudcostreets/nj-crashes/commit/c8ae28e64f4917895d84074913f48e0a7afbc3d7#diff-7f812dce61e0996354f4af414203e0933ccdfe9613cb406c40c1c41a14b9769c
[hudcostreets/nj-crashes]: https://github.com/hudcostreets/nj-crashes
[`jq`]: https://jqlang.github.io/jq/
