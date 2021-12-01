# mets-mods2tei

[![CircleCI](https://circleci.com/gh/slub/mets-mods2tei.svg?style=svg)](https://circleci.com/gh/slub/mets-mods2tei) [![codecov](https://codecov.io/gh/slub/mets-mods2tei/branch/master/graph/badge.svg)](https://codecov.io/gh/slub/mets-mods2tei)

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

## Invocation

Installing `mets-mods2tei` makes the command-line tool `mm2tei` available:

    mm2tei --help

```
Usage: mm2tei [OPTIONS] METS

  METS: File containing or URL pointing to the METS/MODS XML to be converted

Options:
  -o, --ocr                       Serialize OCR into resulting TEI
  -T, --text-group TEXT           File group which contains the full text
  -l, --log-level [DEBUG|INFO|WARN|ERROR|OFF]
  --help                          Show this message and exit.
```

It reads METS XML via URL or file argument and prints the resulting TEI,
including the extracted information from the MODS part of the METS.

Example:

    mm2tei "https://digital.slub-dresden.de/oai/?verb=GetRecord&metadataPrefix=mets&identifier=oai:de:slub-dresden:db:id-453779263"

