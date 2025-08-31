# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------
project = 'Catzilla'
copyright = '2025, Catzilla'
author = 'Rezwan Ahmed Sami'
release = '0.2.0'
version = '0.2.0'

# SEO and Meta Information
html_title = 'Catzilla - The FastAPI Killer | Lightning Fast Python Web Framework Documentation'
html_short_title = 'Catzilla  Documentation'

# Enhanced meta tags for better SEO
html_meta = {
    'description': 'Catzilla - High-performance Python web framework with C-accelerated routing, significantly faster than FastAPI. Features async/sync hybrid, dependency injection, streaming, caching, and more.',
    'keywords': 'python web framework, fast python framework, fastapi alternative, async python, c accelerated routing, high performance python, web development, api development, async sync hybrid, dependency injection',
    'author': 'Rezwan Ahmed Sami',
    'viewport': 'width=device-width, initial-scale=1.0',
    'robots': 'index, follow',
    'language': 'en',
    'og:type': 'website',
    'og:title': 'Catzilla - The FastAPI Killer | Lightning Fast Python Web Framework',
    'og:description': 'High-performance Python web framework with C-accelerated routing, significantly faster than FastAPI. Modern async/sync hybrid architecture.',
    'og:url': 'https://catzilla.rezwanahmedsami.com/',
    'og:site_name': 'Catzilla Documentation',
    'og:image': 'https://catzilla.rezwanahmedsami.com/_static/logo.png',
    'og:image:width': '1200',
    'og:image:height': '630',
    'og:locale': 'en_US',
    'twitter:card': 'summary_large_image',
    'twitter:site': '@rezwanahmedsami',
    'twitter:creator': '@rezwanahmedsami',
    'twitter:title': 'Catzilla - The FastAPI Killer | Lightning Fast Python Web Framework',
    'twitter:description': 'High-performance Python web framework with C-accelerated routing, significantly faster than FastAPI. Modern async/sync hybrid architecture.',
    'twitter:image': 'https://catzilla.rezwanahmedsami.com/_static/logo.png',
    'theme-color': '#2980B9',
}

# -- General configuration ---------------------------------------------------
extensions = [
    # 'sphinx.ext.autodoc',  # Disabled - not needed for static documentation
    # 'sphinx.ext.viewcode',  # Disabled - not needed for static documentation
    # 'sphinx.ext.napoleon',  # Disabled - not needed for static documentation
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    # 'sphinx.ext.coverage',  # Disabled - not needed for static documentation
    'myst_parser',
    'sphinx_sitemap',
    # 'sphinx.ext.autosectionlabel',  # Disabled to avoid duplicate label warnings
    'sphinx_copybutton',  # Add copy button to code blocks
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README.md']

# The master toctree document
master_doc = 'index'

# -- SEO and Meta Tags Configuration -----------------------------------------
sitemap_url_scheme = "{link}"
sitemap_locales = [None]
sitemap_filename = "sitemap.xml"

# Canonical URL configuration
html_baseurl = "https://catzilla.rezwanahmedsami.com/"

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = 'Catzilla - The FastAPI Killer'
html_short_title = 'Catzilla '

# Custom CSS for enhanced styling and SEO
html_css_files = [
    'custom.css',
]

# Custom JavaScript files (optional)
html_js_files = [
    # Add any custom JS files here
]

# Enhanced HTML theme options with SEO optimization
html_theme_options = {
    'canonical_url': 'https://catzilla.rezwanahmedsami.com/',
    'analytics_id': '',
    'analytics_anonymize_ip': False,
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    # Remove unsupported options for the RTD theme
    'globaltoc_collapse': False,
    'globaltoc_includehidden': True,
}

# Force canonical URL for homepage to root domain
html_context = {
    "display_github": True,
    "github_user": "rezwanahmedsami",
    "github_repo": "catzilla",
    "github_version": "main",
    "conf_py_path": "/docs_new/",
    "source_suffix": source_suffix,
    "page_source_suffix": ".rst",
    "versions": [("v0.2.0", "/")],
    "downloads": [
        ("PDF", "https://github.com/rezwanahmedsami/catzilla/releases/latest/download/catzilla-docs.pdf"),
        ("HTML", "https://github.com/rezwanahmedsami/catzilla/archive/main.zip"),
    ],
    "social_links": {
        "github": "https://github.com/rezwanahmedsami/catzilla",
        "twitter": "https://twitter.com/rezwanahmedsami",
        "website": "https://catzilla.rezwanahmedsami.com/",
    },
    # SEO structured data
    "project_name": "Catzilla",
    "project_description": "High-performance Python web framework with C-accelerated routing",
    "project_version": "0.2.0",
    "project_url": "https://catzilla.rezwanahmedsami.com/",
    "project_repository": "https://github.com/rezwanahmedsami/catzilla",
    "project_license": "MIT",
    "project_author": "Rezwan Ahmed Sami",
    "project_keywords": ["python", "web framework", "fastapi", "async", "performance", "c accelerated"],
}

# Enhanced SEO settings
html_use_opensearch = 'https://catzilla.rezwanahmedsami.com/'
html_search_language = 'en'

# Enable search engine optimization features
html_copy_source = False
html_show_sourcelink = False
html_show_sphinx = False

# Performance and SEO optimization
html_minify_css = True
html_use_index = True
html_split_index = True
html_compact_lists = True

# Additional meta configuration for better SEO
html_last_updated_fmt = None
html_use_smartypants = True
html_permalinks_icon = '¶'

# Breadcrumb navigation for better UX and SEO
html_show_copyright = True
html_show_sphinx = False

# Custom domain and CNAME configuration (removed since _extra doesn't exist)
# html_extra_path = ['_extra']

# MyST parser configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

# Copy button configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
