# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------
project = 'Catzilla'
copyright = '2025, Rezwan Ahmed Sami'
author = 'Rezwan Ahmed Sami'
release = '0.1.0'
version = '0.1.0'

# SEO and Meta Information
html_title = 'Catzilla - The FastAPI Killer | Lightning Fast Python Web Framework Documentation'
html_short_title = 'Catzilla - The FastAPI Killer'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'myst_parser',
    'sphinx_sitemap',       # Add sitemap generation
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The master toctree document
master_doc = 'index'

# -- SEO and Meta Tags Configuration -----------------------------------------
# All SEO meta tags, OpenGraph, and Twitter Cards are now handled in layout.html template

# Sitemap Configuration
sitemap_url_scheme = "{link}"
sitemap_locales = [None]
sitemap_filename = "sitemap.xml"

# Canonical URL configuration
html_baseurl = "http://catzilla.rezwanahmedsami.com/"

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = 'Catzilla - The FastAPI Killer'
html_short_title = 'Catzilla'

# Enhanced HTML theme options with SEO improvements
html_theme_options = {
    'canonical_url': 'http://catzilla.rezwanahmedsami.com/',
    'analytics_id': '',  # Add Google Analytics ID if you have one
    'analytics_anonymize_ip': False,
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options optimized for SEO
    'collapse_navigation': False,  # Better for SEO crawling
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Global meta tags for all pages
html_meta = {
    'description': 'The FastAPI killer is here! Lightning fast Python web framework with C-accelerated routing that outperforms FastAPI. Build blazing-fast APIs with minimal overhead and maximum speed.',
    'keywords': 'python, web framework, fast, performance, C accelerated, routing, API, REST, microframework, high performance, catzilla, python web development, asynchronous, HTTP server, web development, fastapi killer, fastapi alternative, faster than fastapi',
    'author': 'Rezwan Ahmed Sami',
    'viewport': 'width=device-width, initial-scale=1.0, maximum-scale=5.0',
    'robots': 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1',
    'googlebot': 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1',
    'bingbot': 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1',
    'google-site-verification': '',  # Add your Google Search Console verification code here
    'msvalidate.01': '',  # Add your Bing Webmaster verification code here
    'yandex-verification': '',  # Add your Yandex verification code here
    'format-detection': 'telephone=no',
    'referrer': 'origin-when-cross-origin',
}

# Language and locale
language = 'en'
locale_dirs = ['locale/']

# Favicon configuration
html_favicon = '_static/favicon.ico'

# -- Options for intersphinx extension ---------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Options for autodoc extension -------------------------------------------
autodoc_typehints = 'description'
autodoc_member_order = 'bysource'

# Enhanced social media and repository links with SEO context
html_context = {
    "display_github": True,
    "github_user": "rezwanahmedsami",
    "github_repo": "catzilla",
    "github_version": "main",
    "conf_py_path": "/docs/",
    "source_suffix": source_suffix,
    "page_source_suffix": ".rst",
    "last_updated": "May 28, 2025",
    "commit": "main",
    "versions": [("latest", "/")],
    "downloads": [
        ("PDF", "https://github.com/rezwanahmedsami/catzilla/releases/latest/download/catzilla-docs.pdf"),
        ("HTML", "https://github.com/rezwanahmedsami/catzilla/archive/main.zip"),
    ],
    "social_links": {
        "github": "https://github.com/rezwanahmedsami/catzilla",
        "twitter": "https://twitter.com/rezwanahmedsami",
        "website": "http://catzilla.rezwanahmedsami.com/",
    }
}

# Additional SEO settings
html_use_opensearch = 'http://catzilla.rezwanahmedsami.com/'
html_search_language = 'en'

# Enable search engine optimization features
html_copy_source = False  # Don't copy .rst source files to output
html_show_sourcelink = False  # Don't show "View page source" links
html_show_sphinx = False  # Don't show "Created using Sphinx" in the footer

# Custom domain and CNAME configuration
html_extra_path = ['_extra']  # For robots.txt, sitemap.xml, etc.
