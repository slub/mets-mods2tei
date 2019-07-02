# mets-mods2teiHeader
Convert bibliographic meta data in METS/MODS format to TEI headers

## Background

[MODS](http://www.loc.gov/standards/mods/) is the de-facto standard for encoding bibliographic
meta data in libraries. It is usually included as a separate section into
[METS](http://www.loc.gov/standards/mets/) XML files.

[TEI](https://tei-c.org/) is the de-facto standard for representing digital text for research
purposes. It usually includes detailed bibliographic meta data in its
[header](https://tei-c.org/release/doc/tei-p5-doc/de/html/ref-teiHeader.html).

Converting bibliographic meta data from METS/MODS to `teiHeader` is thus an important step in
converting digital texts as delivered by libraries into TEI formatted text.

Since these standards contain a considerable amount of degrees of freedom, the conversion uses
well-defined subsets. For MODS, this is the
[*MODS Anwendungsprofil für digitalisierte Medien*](https://dfg-viewer.de/fileadmin/groups/dfgviewer/MODS-Anwendungsprofil_2.3.1.pdf).
For METS, the [METS Anwendungsprofil für digitalisierte Medien 2.1](https://www.zvdd.de/fileadmin/AGSDD-Redaktion/METS_Anwendungsprofil_2.1.pdf) is consulted.
For the TEI Header, the conversion is roughly based on the [*DTA base format*](https://github.com/deutschestextarchiv/dtabf).

## Installation
`mets-mods2teiHeader` is implemented in Python 3. In the following, we assume a working Python 3
(tested versions 3.5 and 3.6) installation.

### Clone the repository
The first installation step is the cloning of the repository:
```console
$ git clone https://github.com/wrznr/mets-mods2teiHeader.git
$ cd mets-mods2teiHeader
```

### virtualenv
Using [`virtualenv`](https://virtualenv.pypa.io/en/stable/) is highly recommended, although not strictly
necessary for installing `mets-mods2teiHeader`. It may be installed via:
```console
$ [sudo] pip install virtualenv
```
Create a virtual environement in a subdirectory of your choice (e.g. `env`) using
```console
$ virtualenv -p python3 env
```
and activate it.
```console
$ . env/bin/activate
```

### Python requirements
`mets-mods2teiHeader` uses various 3rd party Python packages which may best be installed using `pip`:
```console
(env) $ pip install -r requirements.txt
```
Finally, `mets-mods2teiHeader` itself can be installed via `pip`:
```console
(env) $ pip install .
```

## Invocation
Installing `mets-mods2teiHeader` makes the command line tool `mods2teiHeader` available:
```console
(env) $ mods2teiHeader --help
Usage: mods2teiHeader [OPTIONS] METS

  METS: File containing or URL pointing to the METS/MODS XML to be converted

Options:
  --help  Show this message and exit.
```
It reads METS XML via URL or file argument and prints the resulting TEI including the extracted information from the MODS part of the METS.
```console
(env) $ mods2teiHeader "https://digital.slub-dresden.de/oai/?verb=GetRecord&metadataPrefix=mets&identifier=oai:de:slub-dresden:db:id-453779263"
```
