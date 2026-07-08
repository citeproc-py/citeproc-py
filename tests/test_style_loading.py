"""
Tests for flexible style loading from citeproc-py-styles package
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from citeproc import CitationStylesStyle, STYLES_PATH

class TestStyleLoading(unittest.TestCase):
    """Test suite for flexible style loading"""

    def test_bundled_style_loads(self):
        """Test that the bundled harvard-cite-them-right style loads correctly"""
        style = CitationStylesStyle('harvard-cite-them-right', validate=False)
        self.assertIsNotNone(style)

    def test_full_path_style_loads(self):
        """Test that a style specified with full path loads correctly"""
        harvard_path = os.path.join(STYLES_PATH, 'harvard-cite-them-right.csl')
        style = CitationStylesStyle(harvard_path, validate=False)
        self.assertIsNotNone(style)

    def test_nonexistent_style_without_citeproc_py_styles(self):
        """Test error message when style not found and citeproc-py-styles not installed"""
        with patch('citeproc.frontend.os.path.exists') as mock_exists:
            # Make sure the style doesn't exist as a file or bundled
            mock_exists.side_effect = lambda path: False

            # Mock the import to fail
            with patch.dict('sys.modules', {'citeproc_styles': None}):
                with self.assertRaises(ValueError) as context:
                    CitationStylesStyle('nonexistent-style', validate=False)

                error_msg = str(context.exception)
                self.assertIn('nonexistent-style', error_msg)
                self.assertIn('not found in bundled styles', error_msg)
                self.assertIn('pip install citeproc-py-styles', error_msg)

    def test_style_from_citeproc_py_styles(self):
        """Test that styles load from citeproc-py-styles when available"""
        # Create a mock module
        mock_module = MagicMock()
        mock_module.get_style_filepath = MagicMock(return_value='/mock/path/to/apa.csl')

        with patch('citeproc.frontend.os.path.exists') as mock_exists:
            # First call checks if 'apa' exists as path (False)
            # Second call checks bundled path (False)
            mock_exists.side_effect = [False, False]

            with patch.dict('sys.modules', {'citeproc_styles': mock_module}):
                # Mock the parent class __init__ to set root properly
                def mock_init(self, path, validate=False):
                    # Create a mock root object 
                    self.root = MagicMock()
                    self.root.get.return_value = 'en-US'
                    self.root.set_locale_list = MagicMock()
                    # Store the path for verification
                    self._test_path = path

                with patch('citeproc.frontend.CitationStylesXML.__init__', mock_init):
                    style = CitationStylesStyle('apa', validate=False)

                    # Verify get_style_filepath was called with correct argument
                    mock_module.get_style_filepath.assert_called_once_with('apa')
                    # Verify parent init was called with the path from citeproc-py-styles
                    self.assertEqual(style._test_path, '/mock/path/to/apa.csl')

    def test_style_not_in_citeproc_py_styles(self):
        """Test error when style not found even in citeproc-py-styles"""
        # Create a mock module that raises KeyError
        mock_module = MagicMock()
        mock_module.get_style_filepath = MagicMock(side_effect=KeyError('Style not found'))

        with patch('citeproc.frontend.os.path.exists') as mock_exists:
            # Style doesn't exist as file or bundled
            mock_exists.return_value = False

            with patch.dict('sys.modules', {'citeproc_styles': mock_module}):
                with self.assertRaises(ValueError) as context:
                    CitationStylesStyle('unknown-style', validate=False)

                error_msg = str(context.exception)
                self.assertIn('unknown-style', error_msg)
                self.assertIn('not found in bundled styles', error_msg)
                self.assertIn('or in citeproc-py-styles package', error_msg)

    def test_style_file_not_found_in_citeproc_py_styles(self):
        """Test error when citeproc-py-styles returns path but file doesn't exist"""
        # Create a mock module that raises FileNotFoundError
        mock_module = MagicMock()
        mock_module.get_style_filepath = MagicMock(side_effect=FileNotFoundError('File not found'))

        with patch('citeproc.frontend.os.path.exists') as mock_exists:
            # Style doesn't exist as file or bundled
            mock_exists.return_value = False

            with patch.dict('sys.modules', {'citeproc_styles': mock_module}):
                with self.assertRaises(ValueError) as context:
                    CitationStylesStyle('missing-style', validate=False)

                error_msg = str(context.exception)
                self.assertIn('missing-style', error_msg)
                self.assertIn('not found in bundled styles', error_msg)
                self.assertIn('or in citeproc-py-styles package', error_msg)

    def test_citeproc_py_styles_load(self):
        """Test loading a real style from citeproc-py-styles if installed"""
        try:
            import citeproc_styles
        except ImportError:
            self.skipTest("citeproc-py-styles (provides citeproc_styles package) not installed")
        from citeproc_styles import get_style_filepath
        # Attempt to load a known style from citeproc-py-styles
        style_name = 'chicago-author-date'
        style_path = get_style_filepath(style_name)
        style = CitationStylesStyle(style_name, validate=False)
        self.assertIsNotNone(style)
        self.assertTrue(hasattr(style, 'root'))
        # And loading with the full path should also work
        style = CitationStylesStyle(style_path, validate=False)
        self.assertIsNotNone(style)
        self.assertTrue(hasattr(style, 'root'))