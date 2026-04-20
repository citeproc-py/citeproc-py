from citeproc import LOCALES, STYLES
from citeproc.frontend import CitationStylesStyle, CitationStylesLocale
from importlib.resources import as_file, files

import pytest

@pytest.mark.parametrize(
    "resource,default",
    [
        (CitationStylesStyle, 'harvard1'),
        (CitationStylesLocale, 'en-US'),
    ],
)
def test_resource(resource, default):
    style = resource(default)

@pytest.mark.parametrize(
    "root,resource,default",
    [
        (STYLES, CitationStylesStyle, 'harvard1'),
        (LOCALES, CitationStylesLocale, 'en-US'),
    ],
)
def test_path(root, resource, default):
    with as_file(files(root)) as resource_root:
        style = resource(default, root=resource_root)
