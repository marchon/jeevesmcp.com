#!/usr/bin/env python3
"""
Sphinx configuration for Jeeves documentation
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for autodoc
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'Jeeves'
copyright = f'{datetime.now().year}, Jeeves Contributors'
author = 'Jeeves Team'
release = '0.1.0'
version = '0.1.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
    'sphinx_tabs.tabs',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output options
html_theme = 'furo'
html_static_path = ['_static']
html_title = 'Jeeves 🎩'
html_short_title = 'Jeeves'

# Theme options
html_theme_options = {
    'announcement': '<strong>New:</strong> Try Jeeves with <code>curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash</code>',
    'sidebar_hide_name': False,
    'navigation_with_keys': True,
}

# Custom CSS
html_css_files = [
    'custom.css',
]

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# Copy button settings
copybutton_prompt_text = r'>>> |\\$ |\\.\\.\\.\\. '
copybutton_prompt_is_regexp = True
