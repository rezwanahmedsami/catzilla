# Development Files Directory

This directory demonstrates Catzilla's development-friendly features:

## Configuration
- Path: `/files`
- Hot cache: Disabled (for development)
- Cache TTL: 10 seconds (very short)
- Directory listing: Enabled
- Hidden files: Disabled (security)

## Features
- Browse directories in your browser
- Short cache TTL for rapid development
- Security: hidden files are blocked
- Perfect for development and debugging

## Usage
Visit http://localhost:8002/files/ to browse this directory.

## Security Notes
- Hidden files (starting with .) are blocked
- Path traversal protection is always enabled
- Only files within the mount path are accessible
