from citeproc.version import __version__

def test_version():
    assert len(__version__.split(".")) >= 3, f"__version__ should have MAJOR.MINOR.PATCH, got {__version__}"
