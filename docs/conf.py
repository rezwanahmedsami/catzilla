# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------
project = 'Catzilla'
copyright = '2025, Rezwan Ahmed Sami'
author = 'Rezwan Ahmed Sami'
release = '0.1.0'
version = '0.1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'myst_parser',
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The master toctree document
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = 'Catzilla Documentation'
html_short_title = 'Catzilla'
# html_logo = '_static/logo.png'  # Commented out to remove sidebar logo

# Theme options for sphinx_rtd_theme
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'analytics_anonymize_ip': False,
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are added to the list of paths to be copied
# to the output directory.
html_static_path = ['_static']

# -- Options for intersphinx extension ---------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Options for autodoc extension -------------------------------------------
autodoc_typehints = 'description'
autodoc_member_order = 'bysource'

# Social media and repository links
html_context = {
    "display_github": True,
    "github_user": "rezwanahmedsami",
    "github_repo": "catzilla",
    "github_version": "main",
    "conf_py_path": "/docs/",
}
