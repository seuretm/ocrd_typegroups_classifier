Change Log
==========
Versioned according to [Semantic Versioning](http://semver.org/).

## Unreleased

# [0.3.0] - 2021-01-28

Changed:

  * Use `self.resolve_resource` to resolve `network` parameter, #8

# [0.2.0] - 2020-12-22

Changed:

  * default model is now bundled with the processor, #7

# [0.1.4] - 2020-12-21

Fixed:

  * imports in simple CLI, #5
  * `--help`/`-h` for simple CLI, #6

# [0.1.3] - 2020-12-10

Fixed:

  * pass on pageID, ht @mikegerber
  * use core's image API (`image_from_page`), ht @bertsky
  * annotate `pcGtsId`, `Metadata`, document processor, ht @bertsky

# [0.1.2] - 2020-10-14

Fixed:

  * `getLogger` mustn't be called in constructor, #3

# [0.1.1] - 2020-08-21

Fixed:

  * missing `import json` from setup.py

# [0.1.0] - 2020-08-21

Changed:

  * merge upstream, #2
  * use `make_file_id` and `assert_file_grp_cardinality`, #2


<!-- link-labels -->
[0.3.0]: ../../compare/v0.3.0...v0.2.0
[0.2.0]: ../../compare/v0.2.0...v0.1.4
[0.1.4]: ../../compare/v0.1.4...v0.1.3
[0.1.3]: ../../compare/v0.1.3...v0.1.2
[0.1.2]: ../../compare/v0.1.2...v0.1.1
[0.1.1]: ../../compare/v0.1.1...v0.1.0
[0.1.0]: ../../compare/v0.1.0...v0.0.2
[0.0.2]: ../../compare/v0.0.1...v0.0.2
[0.0.2]: ../../compare/HEAD...v0.0.1
