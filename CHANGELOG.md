# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.1.4] - 2023-12-12
### Changed
- mm-update: adapt to OCR-D API changes

## [0.1.3] - 2023-02-11
### Added
- mm2tei CLI param controlling page and line refs via @corresp
- mm-update CLI

## [0.1.2] - 2022-01-10
### Added
- tests for TEI API
- tests for insertion index identification
- more logging
- CLI param for output file
- CLI param for image fileGrp

### Changed
- Add `front`, `body` and `back` per default
- Log to stderr instead of stdout
- Differentiate between (physical) image nr and (logical) page nr

### Fixed
- Evaluate texts from all struct types but `binding` and `colour_checker`, #43
- Handle errors during language code expansion, and fallback to `Unbekannt`, #47
- Add ALTO `HYP` text content if available, #52
- Allow empty logical structMap and structLink, fallback to physical, or empty, #57
- Allow partial dmdSec (MODS) or amdSec, fallback to empty, #46, #51
- Pass all `mods:identifier`s to `msIdentifier/idno` (not just VD and URN)
- Parse full `titleInfo` (main/sub/part/volume), and re-use in `biblFull`
- Prefer `titleInfo/title` over `div/@LABEL` if available
- Map top logical `div/@TYPE` into allowed `biblFull/title/@level` only
- Map top logical `div/@TYPE` into appropriate `bibl/@type` if possible

## [0.1.1] - 2020-05-11
### Added
- Make full text file group selectable by user
- Add poor man's namespace versioning handling

### Changed
- Make extraction of subtitles conditional on their presence
- Use "licence" for all types of licences (even unknown ones), #39

### Fixed
- Handle nested `@ADMID="AMD"` divs in logical `structMap` (i.e. newspaper case), #43
- Allow for local path entries (in addition to URLs) in METS, #41
- Add special treatment for URNs and VD IDs, #37

## [0.1.0] - 2019-12-04
### Added
- Correctly place structures which are not on top of a page
- Set `corresp` and `facs` attributes of `pb` elements
- Store links to `DEFAULT` images in METS
- Tests for new functionality
- Add Changelog file, #28

### Changed
- Retrieve ALTO files via a dedicated struct link member of the class `Mets`
- Move text retrieval to `Alto` class

### Removed
- Get rid of code artifacts carried over from `tocrify`

<!-- link-labels -->
[unreleased]: ../../compare/v0.1.4...master
[0.1.4]: ../../compare/v0.1.3...v0.1.4
[0.1.3]: ../../compare/v0.1.2...v0.1.3
[0.1.2]: ../../compare/v0.1.1...v0.1.2
[0.1.1]: ../../compare/v0.1.0...v0.1.1
[0.1.0]: ../../compare/v1.0...v0.1.0
