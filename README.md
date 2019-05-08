# mets-mods2teiHeader
Convert bibliographic meta data in MODS format to TEI headers

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
Using [`virtualenv`](https://virtualenv.pypa.io/en/stable/) is highly recommended, although not strictly necessary for installing `mets-mods2teiHeader`. It may be installed via:
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
