# dvc-utils
Diff [DVC] files, optionally piping through other commands first.

[![dvc-utils on PyPI](https://img.shields.io/pypi/v/dvc-utils?label=dvc-utils)][PyPI]

<!-- toc -->
- [Installation](#installation)
- [Usage](#usage)
    - [`dvc-diff`](#dvc-diff)
- [Examples](#examples)
    - [Parquet](#parquet-diff)
        - [Schema diff](#parquet-schema-diff)
        - [Row diff](#parquet-row-diff)
        - [Row count diff](#parquet-row-count-diff)
    - [GZipped CSVs](#csv-gz)
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

The single subcommand, `dvc-utils diff`, is also exposed directly as `dvc-dff`:

### `dvc-diff` <a id="dvc-diff"></a>
<!-- `bmdf -- dvc-diff --help` -->
```bash
dvc-diff --help
# Usage: dvc-diff [OPTIONS] [exec_cmd...] <path>
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
#   -c, --color / -C, --no-color  Force or prevent colorized output
#   -r, --refspec TEXT            <commit 1>..<commit 2> (compare two commits)
#                                 or <commit> (compare <commit> to the worktree)
#   -R, --ref TEXT                Shorthand for `-r <ref>^..<ref>`, i.e. inspect
#                                 a specific commit (vs. its parent)
#   -s, --shell-executable TEXT   Shell to use for executing commands; defaults
#                                 to $SHELL
#   -S, --no-shell                Don't pass `shell=True` to Python
#                                 `subprocess`es
#   -U, --unified INTEGER         Number of lines of context to show (passes
#                                 through to `diff`)
#   -v, --verbose                 Log intermediate commands to stderr
#   -w, --ignore-whitespace       Ignore whitespace differences (pass `-w` to
#                                 `diff`)
#   -x, --exec-cmd TEXT           Command(s) to execute before diffing;
#                                 alternate syntax to passing commands as
#                                 positional arguments
#   --help                        Show this message and exit.
```

## Examples <a id="examples"></a>
These examples are verified with [`mdcmd`] and `$BMDF_WORKDIR=test/data`

([`test/data`] is a clone of [ryan-williams/dvc-helpers@test], which contains simple DVC-tracked files used for testing [`git-diff-dvc.sh`])

[`8ec2060`] added a DVC-tracked text file, `test.txt`:

<!-- `bmdf -- dvc-diff -R 8ec2060 test.txt` -->
```bash
dvc-diff -R 8ec2060 test.txt
# 0a1,10
# > 1
# > 2
# > 3
# > 4
# > 5
# > 6
# > 7
# > 8
# > 9
# > 10
```

[`0455b50`] appended some lines to `test.txt`:

<!-- `bmdf -- dvc-diff -R 0455b50 test.txt` -->
```bash
dvc-diff -R 0455b50 test.txt
# 10a11,15
# > 11
# > 12
# > 13
# > 14
# > 15
```

[`f92c1d2`] added `test.parquet`:

<!-- `bmdf -- dvc-diff -R f92c1d2 pqa test.parquet` -->
```bash
dvc-diff -R f92c1d2 pqa test.parquet
# 0a1,27
# > MD5: 4379600b26647a50dfcd0daa824e8219
# > 1635 bytes
# > 5 rows
# > message schema {
# >   OPTIONAL INT64 num;
# >   OPTIONAL BYTE_ARRAY str (STRING);
# > }
# > {
# >   "num": 111,
# >   "str": "aaa"
# > }
# > {
# >   "num": 222,
# >   "str": "bbb"
# > }
# > {
# >   "num": 333,
# >   "str": "ccc"
# > }
# > {
# >   "num": 444,
# >   "str": "ddd"
# > }
# > {
# >   "num": 555,
# >   "str": "eee"
# > }
```

[`f29e52a`] updated `test.parquet`:

<!-- `bmdf -- dvc-diff -R f29e52a pqa test.parquet` -->
```bash
dvc-diff -R f29e52a pqa test.parquet
# 1,3c1,3
# < MD5: 4379600b26647a50dfcd0daa824e8219
# < 1635 bytes
# < 5 rows
# ---
# > MD5: be082c87786f3364ca9efec061a3cc21
# > 1622 bytes
# > 8 rows
# 5c5
# <   OPTIONAL INT64 num;
# ---
# >   OPTIONAL INT32 num;
# 26a27,38
# > }
# > {
# >   "num": 666,
# >   "str": "fff"
# > }
# > {
# >   "num": 777,
# >   "str": "ggg"
# > }
# > {
# >   "num": 888,
# >   "str": "hhh"
```

[`3257258`] added a DVC-tracked directory `data/`, including `test.{txt,parquet}`), and removed the top-level `test.{txt,parquet}`.

<!-- `bmdf -- dvc-diff -R 3257258 data` -->
```bash
dvc-diff -R 3257258 data
# test.parquet: None -> c07bba3fae2b64207aa92f422506e4a2
# test.txt: None -> e20b902b49a98b1a05ed62804c757f94
```

[`ae8638a`] changed values in `data/test.parquet`, and added rows to `data/test.txt`:

<!-- `bmdf -- dvc-diff -R ae8638a data` -->
```bash
dvc-diff -R ae8638a data
# test.parquet: c07bba3fae2b64207aa92f422506e4a2 -> f46dd86f608b1dc00993056c9fc55e6e
# test.txt: e20b902b49a98b1a05ed62804c757f94 -> 9306ec0709cc72558045559ada26573b
```

### Parquet <a id="parquet-diff"></a>
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
dvc-diff -r $commit^..$commit parquet_schema $path
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
dvc-diff -r $commit^..$commit pretty_print_first_row $path
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
dvc-diff -r $commit^..$commit parquet_row_count $path
```

This time we get no output; [the given `$commit`][commit] didn't change the row count in the DVC-tracked Parquet file [`$path`][commit path].

### GZipped CSVs <a id="csv-gz"></a>

Here's a "one-liner" I used in [ctbk.dev][ctbk.dev gh], to normalize and compare headers of `.csv.gz.dvc` files between two commits:

```bash
# Save some `sed` substitution commands to file `seds`:
cat <<EOF >seds
s/station_//
s/latitude/lat/
s/longitude/lng/
s/starttime/started_at/
s/stoptime/ended_at/
s/usertype/member_casual/
EOF
# Commit range to diff; branch `c0` is an initial commit of some `.csv.gz` files, branch `c1` is a later commit after some updates
r=c0..c1
# List files changed in commit range `$r`, in the `s3/ctbk/csvs/` dir, piping through several post-processing commands:
gdno $r s3/ctbk/csvs/ | \
pel "ddcr $r guc h1 spc kq kcr snc 'sdf seds' sort"
```

<details>
<summary>
Explanation of aliases
</summary>

- [`gdno`] (`git diff --name-only`): list files changed in the given commit range and directory
- [`pel`]: [`parallel`] alias that prepends an `echo {}` to the command
- [`ddcr`] (`dvc-diff -cr`): colorized `diff` output, revision range `$r`
- [`guc`] (`gunzip -c`): uncompress the `.csv.gz` files
- [`h1`] (`head -n1`): only examine each file's header line
- [`spc`] (`tr , $'\n'`): **sp**lit the header line by **c**ommas (so each column name will be on one line, for easier `diff`ing below)
- [`kq`] (`tr -d '"'`): **k**ill **q**uote characters (in this case, header-column name quoting changed, but I don't care about that)
- [`kcr`] (`tr -d '\r'`): **k**ill **c**arriage **r**eturns (line endings also changed)
- [`snc`] (`sed -f 'snake_case.sed'`): snake-case column names
- [`sdf`] (`sed -f`): execute the `sed` substitution commands defined in the `seds` file above
- `sort`: sort the column names alphabetically (to identify missing or added columns, ignore rearrangements)

Note:
- Most of these are exported Bash functions, allowing them to be used inside the [`parallel`] command.
- I was able to build this pipeline iteratively, adding steps to normalize out the bits I didn't care about (and accumulating the `seds` commands).
</details>

Example output:
```diff
…
s3/ctbk/csvs/201910-citibike-tripdata.csv.gz.dvc:
s3/ctbk/csvs/201911-citibike-tripdata.csv.gz.dvc:
s3/ctbk/csvs/201912-citibike-tripdata.csv.gz.dvc:
s3/ctbk/csvs/202001-citibike-tripdata.csv.gz.dvc:
1,2d0
< bikeid
< birth_year
8d5
< gender
9a7,8
> ride_id
> rideable_type
15d13
< tripduration
s3/ctbk/csvs/202002-citibike-tripdata.csv.gz.dvc:
1,2d0
< bikeid
< birth_year
8d5
< gender
9a7,8
> ride_id
> rideable_type
15d13
< tripduration
s3/ctbk/csvs/202003-citibike-tripdata.csv.gz.dvc:
1,2d0
< bikeid
< birth_year
8d5
< gender
9a7,8
> ride_id
> rideable_type
15d13
< tripduration
…
```

This helped me see that the data update in question (`c0..c1`) dropped some fields (`bikeid, birth_year`, `gender`, `tripduration`) and added others (`ride_id`, `rideable_type`), for `202001` and later.

[DVC]: https://dvc.org/
[PyPI]: https://pypi.org/project/dvc-utils/
[`parquet2json`]: https://github.com/jupiter/parquet2json
[hudcostreets/nj-crashes]: https://github.com/hudcostreets/nj-crashes
[Parquet]: https://parquet.apache.org/
[commit]: https://github.com/hudcostreets/nj-crashes/commit/c8ae28e64f4917895d84074913f48e0a7afbc3d7
[commit path]: https://github.com/hudcostreets/nj-crashes/commit/c8ae28e64f4917895d84074913f48e0a7afbc3d7#diff-7f812dce61e0996354f4af414203e0933ccdfe9613cb406c40c1c41a14b9769c
[hudcostreets/nj-crashes]: https://github.com/hudcostreets/nj-crashes
[ctbk.dev gh]: https://github.com/neighbor-ryan/ctbk.dev
[`jq`]: https://jqlang.github.io/jq/
[`parallel`]: https://www.gnu.org/software/parallel/

[`gdno`]: https://github.com/ryan-williams/git-helpers/blob/96560df1406f41676f293becefb423895a755faf/diff/.gitconfig#L31
[`pel`]: https://github.com/ryan-williams/parallel-helpers/blob/e7ee109c4085c04036840ea78999cff73fcf9502/.parallel-rc#L6-L17
[`ddcr`]: https://github.com/ryan-williams/aws-helpers/blob/8a314f1e6b336833c772459de6b739f5c06a51a3/.dvc-rc#L84
[`guc`]: https://github.com/ryan-williams/zip-helpers/blob/c67d84fb06c0ab3609dacb68d900344d3b8e8f04/.zip-rc#L16
[`h1`]: https://github.com/ryan-williams/head-tail-helpers/blob/9715690f47ceeff6b6948b2093901f2b0830114b/.head-tail-rc#L3
[`spc`]: https://github.com/ryan-williams/col-helpers/blob/9493d003224249ee240d023f71ab03bdd4174b88/.cols-rc#L8
[`kq`]: https://github.com/ryan-williams/arg-helpers/blob/a8c60809f8878fa38b3c03614778fcf29132538e/.arg-rc#L115
[`kcr`]: https://github.com/ryan-williams/arg-helpers/blob/a8c60809f8878fa38b3c03614778fcf29132538e/.arg-rc#L118
[`snc`]: https://github.com/ryan-williams/case-helpers/blob/c40a62a9656f0d52d68fb3a108ae6bb3eed3c7bd/.case-rc#L9
[`sdf`]: https://github.com/ryan-williams/arg-helpers/blob/a8c60809f8878fa38b3c03614778fcf29132538e/.arg-rc#L138

[`mdcmd`]: https://github.com/runsascoded/bash-markdown-fence?tab=readme-ov-file#bmdf
[`test/data`]: test/data
[ryan-williams/dvc-helpers@test]: https://github.com/ryan-williams/dvc-helpers/tree/test
[`git-diff-dvc.sh`]: https://github.com/ryan-williams/dvc-helpers/blob/main/git-diff-dvc.sh

[`8ec2060`]: https://github.com/ryan-williams/dvc-helpers/commit/8ec2060
[`0455b50`]: https://github.com/ryan-williams/dvc-helpers/commit/0455b50
[`f92c1d2`]: https://github.com/ryan-williams/dvc-helpers/commit/f92c1d2
[`f29e52a`]: https://github.com/ryan-williams/dvc-helpers/commit/f29e52a
[`3257258`]: https://github.com/ryan-williams/dvc-helpers/commit/3257258
[`ae8638a`]: https://github.com/ryan-williams/dvc-helpers/commit/ae8638a
