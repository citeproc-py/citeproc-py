TODO: add to CONTRIBUTING.rst whenever that gets converted to .md in
https://github.com/citeproc-py/citeproc-py/pull/154 or after

## Releasing with GitHub Actions, auto, and pull requests

New releases of dandi-cli are created via a GitHub Actions workflow built
around [`auto`](https://github.com/intuit/auto).  Whenever a pull request is
merged that has the "`release`" label, `auto` updates the changelog based on
the pull requests since the last release, commits the results, tags the new
commit with the next version number, and creates a GitHub release for the tag.
This in turn triggers a job for building an sdist & wheel for the project and
uploading them to PyPI.

### Labelling pull requests

The section that `auto` adds to the changelog on a new release consists of the
titles of all pull requests merged into master since the previous release,
organized by label.  `auto` recognizes the following PR labels:

- `major` — for changes corresponding to an increase in the major version
  component
- `minor` — for changes corresponding to an increase in the minor version
  component
- `patch` — for changes corresponding to an increase in the patch/micro version
  component; this is the default label for unlabelled PRs
- `internal` — for changes only affecting the internal API
- `documentation` — for changes only affecting the documentation
- `tests` — for changes to tests
- `dependencies` — for updates to dependency versions
- `performance` — for performance improvements

