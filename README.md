# mets-mods2tei

[![CircleCI](https://circleci.com/gh/slub/mets-mods2tei.svg?style=svg)](https://circleci.com/gh/slub/mets-mods2tei)
[![codecov](https://codecov.io/gh/slub/mets-mods2tei/branch/master/graph/badge.svg)](https://codecov.io/gh/slub/mets-mods2tei)
[![PyPI version](https://badge.fury.io/py/mets-mods2tei.svg)](https://badge.fury.io/py/mets-mods2tei)

Convert bibliographic meta data in METS/MODS format to TEI headers and optionally serialize linked ALTO-encoded OCR to TEI text.

## Background

[MODS](http://www.loc.gov/standards/mods/) is the de-facto standard for encoding bibliographic
meta data in libraries. It is usually included as a separate section into
[METS](http://www.loc.gov/standards/mets/) XML files. Physical and logical structure of a document
are expressed in terms of structural mappings (`structMap` elements).

[TEI](https://tei-c.org/) is the de-facto standard for representing digital text for research
purposes. It usually includes detailed bibliographic meta data in its
[header](https://tei-c.org/release/doc/tei-p5-doc/de/html/ref-teiHeader.html).

Since these standards contain a considerable amount of degrees of freedom, the conversion uses
well-defined subsets. For MODS, this is the
[*MODS Anwendungsprofil für digitalisierte Medien*](https://dfg-viewer.de/fileadmin/groups/dfgviewer/MODS-Anwendungsprofil_2.3.1.pdf).
For METS, the [METS Anwendungsprofil für digitalisierte Medien 2.1](https://www.zvdd.de/fileadmin/AGSDD-Redaktion/METS_Anwendungsprofil_2.1.pdf) is consulted.
For the TEI Header, the conversion is roughly based on the [*DTA base format*](https://github.com/deutschestextarchiv/dtabf).

`mets-mods2tei` is developed at the [Saxon State and University Library in Dresden](https://www.slub-dresden.de).

## Installation

`mets-mods2tei` is implemented in Python 3. In the following, we assume a working Python 3
(tested versions 3.5, 3.6 and 3.7) installation.

### Setup Python

Using [virtual environments](https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments) is highly recommended,
although not strictly necessary for installing `mets-mods2tei`.

To create a virtual environement in a subdirectory of your choice (e.g. `env`), run

    python3 -m venv env

(once) and then activate it (each time you open the shell) via

    . env/bin/activate

Depending on how old the packages are which your base system provides,
you might have to update pip first:

    pip install -U pip setuptools

### Get Python package

`mets-mods2tei` can be installed via `pip3` directly.
You can install from either the repository sources or the
prebuilt distribution on PyPI:

#### From repository

If you have an active virtual environment, do

    pip install mets-mods2tei

Otherwise, try

    pip3 install --user mets-mods2tei

#### From source

Get the repository:

    git clone https://github.com/slub/mets-mods2tei.git
    cd mets-mods2tei

If you have an active virtual environment, do

    pip install .

Otherwise, try

    pip3 install --user .

## Testing

`mets-mods2tei` uses `pytest`-based testing.

To install the prerequisites for testing, (in your venv), do

    pip install -r requirements-test.txt

(once) and then run the tests via:

    pytest

## Code coverage

Determine code coverage by running

    make coverage

## Usage

### mm2tei

Installing `mets-mods2tei` makes the command-line tool `mm2tei` available:

<details><summary>mm2tei --help</summary>
<p>

```
Usage: mm2tei [OPTIONS] METS

  METS: File containing or URL pointing to the METS/MODS XML to be converted

  Parse given METS and its meta-data, and convert it to TEI.

  If `--ocr` is given, then also read the ALTO full-text files from the
  fileGrp in `--text-group`, and convert page contents accordingly (in
  physical order).

  Decorate page boundaries with image and page numbers. Moreover, if `--add-
  refs` contains `page`, then reference the corresponding base image files (by
  file name) from `--img-group`. Likewise, if `--add-refs` contains `line`,
  then reference the corresponding textline segments (by XML ID) from `--text-
  group`.

  Output XML to `--output (use '-' for stdout), log to stderr.`

Options:
  -O, --output FILENAME           File path to write TEI output to
  -o, --ocr                       Serialize OCR into resulting TEI
  -T, --text-group TEXT           File group which contains the full-text
  -I, --img-group TEXT            File group which contains the images
  -r, --add-refs [page|line]
  -l, --log-level [DEBUG|INFO|WARN|ERROR|OFF]
  -h, --help                      Show this message and exit.
```

</p></details>

It reads METS XML via URL or file argument and prints the resulting TEI,
including the extracted information from the MODS part of the METS.


Example:

    mm2tei -O tei.xml "https://digital.slub-dresden.de/oai/?verb=GetRecord&metadataPrefix=mets&identifier=oai:de:slub-dresden:db:id-453779263"


### mm-update

Installing `mets-mods2tei` also provides the command-line multi-cmd tool `mm-update`:

<details><summary>mm-update --help</summary>
<p>

```
Usage: mm-update [OPTIONS] COMMAND [ARGS]...

  Entry-point of multi-purpose CLI for DFG Viewer compliant METS updates

Options:
  --version                       Show the version and exit.
  -l, --log-level [OFF|ERROR|WARN|INFO|DEBUG|TRACE]
                                  Log level
  -d, --directory WORKSPACE_DIR   Changes the workspace folder location
                                  [default: METS_URL directory or .]"
  -m, --mets METS_URL             The path/URL of the METS file [default:
                                  WORKSPACE_DIR/mets.xml]
  --backup                        Backup METS whenever it is saved.
  --help                          Show this message and exit.

Commands:
  add-agent     add agent headers, optionally from external METS
  add-file      add a file reference, optionally as URL
  download      download files into subdirectories, as path or URL
  remove-file   remove all file references for a specific location,...
  remove-files  remove all file references for a specific fileGrp / MIME...
  validate      custom OcrdWorkspaceValidator
```

</p></details>

<details><summary>mm-update add-agent --help</summary>
<p>

```
Usage: mm-update add-agent [OPTIONS]

  add agent headers, optionally from external METS

Options:
  -m, --mets TEXT  copy metsHdr/agent from this file, too
  --help           Show this message and exit.
```

</p></details>

<details><summary>mm-update add-file --help</summary>
<p>

```
Usage: mm-update add-file [OPTIONS] PATH

  add a file reference, optionally as URL

Options:
  -G, --file-grp FILE_GRP  fileGrp to add to  [required]
  -m, --mimetype TYPE      Media type of the file. Guessed from extension if
                           not provided
  -g, --page-id PAGE_ID    ID of the physical page (or empty if document-
                           global)
  -u, --url-prefix TEXT    URL prefix to add to path before storing references
                           (or else keep local file refs)
  --help                   Show this message and exit.


```

</p></details>

<details><summary>mm-update remove-file --help</summary>
<p>

```
Usage: mm-update remove-file [OPTIONS] PATH

  remove all file references for a specific location, optionally as URL

Options:
  -u, --url-prefix TEXT  URL prefix to add to path before removing references
                         (or else search verbatim file refs)
  --help                 Show this message and exit.
```

</p></details>

<details><summary>mm-update remove-files --help</summary>
<p>

```
Usage: mm-update remove-files [OPTIONS]

  remove all file references for a specific fileGrp / MIME type / page ID
  combination

Options:
  -G, --file-grp FILE_GRP  fileGrp to add to  [required]
  -m, --mimetype TYPE      Media type of the file. Guessed from extension if
                           not provided
  -g, --page-id PAGE_ID    ID of the physical page (or empty if document-
                           global)
  --help                   Show this message and exit.
```

</p></details>

<details><summary>mm-update validate --help</summary>
<p>

```
Usage: mm-update validate [OPTIONS]

  custom OcrdWorkspaceValidator

Options:
  -u, --url-prefix TEXT  validate each file has this URL prefix
  --help                 Show this message and exit.
```

</p></details>

<details><summary>mm-update download --help</summary>
<p>

```
Usage: mm-update download [OPTIONS]

  download files into subdirectories, as path or URL

Options:
  -G, --file-grp FILE_GRP         fileGrp USE (or empty if all fileGrps)
  -g, --page-id PAGE_ID           ID of the physical page (or empty if all
                                  pages)
  -p, --path-names [URL|GRP/ID.SUF]
                                  how to generate local path names (from URL
                                  or from fileGrp, file ID and suffix)
                                  [default: URL]
  -u, --url-prefix TEXT           URL prefix to remove from path before
                                  storing downloaded files (to avoid creating
                                  host directories)
  -r, --reference [no-change|replace-by-local|insert-local|append-local]
                                  whether and how to update the FLocat
                                  reference in METS  [default: no-change]
  --help                          Show this message and exit.
```

</p></details>

Example:

    # dump files (without changing METS):
    mm-update download -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/
    ...
    # add TEI
    mm-update add-file -G TEI -m application/tei+xml -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/ tei.xml
    ...
    # remove old PDF:
    mm-update remove-files -G DOWNLOAD
    # add new PDF:
    mm-update add-file -G DOWNLOAD -m application/pdf -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/ -g PHYS_0001 pdf/file_0001.pdf
    mm-update add-file -G DOWNLOAD -m application/pdf -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/ -g PHYS_0002 pdf/file_0002.pdf
    mm-update add-file -G DOWNLOAD -m application/pdf -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/ -g PHYS_0003 pdf/file_0003.pdf
    mm-update add-file -G DOWNLOAD -m application/pdf -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/ pdf/all.pdf
    ...
    # remove old ALTO:
    mm-update remove-files -G FULLTEXT -g PHYS_0001
    mm-update remove-files -G FULLTEXT -g PHYS_0002
    mm-update remove-files -G FULLTEXT -g PHYS_0003
    # add new ALTO:
    mm-update add-file -G FULLTEXT -m text/xml -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/ -g PHYS_0001 ocr/alto_0001.xml
    mm-update add-file -G FULLTEXT -m text/xml -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/ -g PHYS_0002 ocr/alto_0002.xml
    mm-update add-file -G FULLTEXT -m text/xml -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/ -g PHYS_0003 ocr/alto_0003.xml
    ...
    # validate:
    mm-update validate -u https://digital.slub-dresden.de/data/kitodo/GottDie_453779263/