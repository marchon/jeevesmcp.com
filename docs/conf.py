#!/usr/bin/env python3
"""
Sphinx configuration for Jeeves documentation

This file is execfile()d with the current directory set to its containing dir.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for autodoc
sys.path.insert(0, os.path.abspath('..'))

# Try to import platform_utils for dynamic documentation
# If it fails (e.g., during CI without deps), use defaults
try:
    from platform_utils import PlatformInfo, OperatingSystem, ShellType
    platform_info = PlatformInfo()
    has_platform_info = True
except ImportError:
    has_platform_info = False
    platform_info = None

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
    'myst_parser',  # Support for Markdown files
]

# MyST parser settings for Markdown support
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "fieldlist",
]

source_suffix = {
    '.rst': None,
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output options
html_theme = 'furo'
html_static_path = ['_static']
html_title = 'Jeeves 🎩'
html_short_title = 'Jeeves'

# Detect current platform for conditional documentation
if has_platform_info:
    current_os = platform_info.os.value
    current_shell = platform_info.shell.value
    is_wsl = platform_info.is_wsl
else:
    current_os = 'unknown'
    current_shell = 'unknown'
    is_wsl = False

# Platform-specific announcement
if current_os == 'windows':
    install_cmd = 'irm https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.ps1 | iex'
    platform_note = 'Windows PowerShell install'
elif current_os == 'macos':
    install_cmd = 'curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash'
    platform_note = 'macOS install'
else:
    install_cmd = 'curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash'
    platform_note = 'Linux install'

if is_wsl:
    platform_note = 'Windows (WSL) install'

# Theme options with platform awareness
html_theme_options = {
    'announcement': f'<strong>New:</strong> Try Jeeves with <code>{install_cmd}</code> ({platform_note})',
    'sidebar_hide_name': False,
    'navigation_with_keys': True,
    'footer_icons': [
        {
            'name': 'GitHub',
            'url': 'https://github.com/marchon/jeevesmcp.com',
            'html': '',
            'class': 'fa-brands fa-github',
        },
    ],
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
napoleon_numpy_docstring = False  # Use Google style
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True

# Copy button settings
copybutton_prompt_text = r'>>> |\$ |\.\.\.\. '
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
copybutton_remove_prompts = True

# Add any paths that contain custom static files (such as style sheets)
html_static_path = ['_static']

# Custom sidebar templates
html_sidebars = {
    '**': [
        'sidebar/scroll-start.html',
        'sidebar/brand.html',
        'sidebar/search.html',
        'sidebar/navigation.html',
        'sidebar/ethical-ads.html',
        'sidebar/scroll-end.html',
    ]
}

# Output file base name for HTML help builder
htmlhelp_basename = 'Jeevesdoc'

# Grouping of document objects
toc_object_entries = True
toc_object_entries_show_parents = 'domain'

# Make these variables available to all templates and docs
rst_prolog = f'''
.. |install_command| replace:: {install_cmd}
.. |current_os| replace:: {current_os}
.. |current_shell| replace:: {current_shell}
.. |is_wsl| replace:: {'true' if is_wsl else 'false'}
'''

# Platform-specific substitutions
if has_platform_info:
    rst_prolog += f'''
.. |config_dir| replace:: {platform_info.config_dir}
.. |shell_config| replace:: {platform_info.shell_config_file or '~/.bashrc'}
.. |install_dir| replace:: {platform_info.get_install_dir()}
.. |bin_dir| replace:: {platform_info.get_bin_dir()}
'''
else:
    rst_prolog += '''
.. |config_dir| replace:: ~/.config/jeeves
.. |shell_config| replace:: ~/.bashrc
.. |install_dir| replace:: ~/.local/share/jeeves
.. |bin_dir| replace:: ~/.local/bin
'''

# Print detected platform during build (for debugging)
if has_platform_info:
    print(f"Building docs for platform: {platform_info.get_os_display_name()}")
    print(f"Shell: {platform_info.shell.value}")
    print(f"Terminal: {platform_info.terminal.value}")
