# Wflo Documentation

This directory contains the source files for the Wflo GitHub Pages website.

## Website Structure

The website is built using Jekyll and the Just the Docs theme.

```
wflo/
├── _config.yml              # Jekyll configuration
├── index.md                 # Homepage
├── docs/
│   ├── ARCHITECTURE.md      # Technical architecture (original)
│   ├── README.md           # This file
│   └── pages/              # Documentation pages
│       ├── features.md     # Features documentation
│       ├── getting-started.md  # Getting started guide
│       ├── use-cases.md    # Real-world use cases
│       ├── examples.md     # Code examples
│       ├── architecture.md # Architecture overview
│       └── contributing.md # Contributing guide
```

## Local Development

### Prerequisites

- Ruby 2.7 or higher
- Bundler

### Setup

```bash
# Install dependencies
bundle install

# Run local server
bundle exec jekyll serve

# Open browser to http://localhost:4000/wflo
```

### Live Reload

Jekyll supports live reload - changes to markdown files will automatically refresh in your browser.

## GitHub Pages Deployment

### Automatic Deployment

GitHub Pages automatically builds and deploys the site when changes are pushed to the main branch.

The site will be available at: `https://wflo-ai.github.io/wflo`

### Manual Configuration

1. Go to your repository settings on GitHub
2. Navigate to "Pages" section
3. Under "Source", select:
   - Branch: `main`
   - Folder: `/ (root)`
4. Click "Save"

GitHub will automatically detect the `_config.yml` file and build the site using Jekyll.

### Build Status

You can check the build status in the "Actions" tab of your GitHub repository.

## Writing Documentation

### Page Format

All documentation pages should include front matter:

```markdown
---
layout: default
title: Page Title
nav_order: 1
description: "Page description for SEO"
permalink: /docs/page-name
---

# Page Title
{: .no_toc }

Brief description.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Section 1

Content here...
```

### Navigation Order

Pages are ordered using the `nav_order` field in the front matter:

1. Home
2. Features
3. Getting Started
4. Use Cases
5. Examples
6. Architecture
7. Contributing

### Styling

Just the Docs provides several utility classes:

- `.fs-1` to `.fs-9` - Font sizes
- `.fw-300`, `.fw-400`, `.fw-700` - Font weights
- `.text-delta` - Delta text style
- `.no_toc` - Exclude from table of contents

### Code Blocks

Use fenced code blocks with language specification:

\```python
from wflo import Workflow

workflow = Workflow("example")
\```

### Callouts

Use blockquotes for callouts:

```markdown
> **Note**: This is an important note.

> **Warning**: This is a warning.
```

## Theme Customization

The site uses the Just the Docs theme with custom configuration in `_config.yml`:

- **Color scheme**: Dark mode
- **Search**: Enabled
- **Navigation**: Enabled with case-insensitive sorting
- **GitHub links**: Edit links enabled

To change the theme or color scheme, edit `_config.yml`.

## Assets

### Images

Place images in `/assets/images/`:

```markdown
![Alt text](/assets/images/diagram.png)
```

### Custom CSS

Add custom CSS in `/_sass/custom/custom.scss` (create if doesn't exist).

### Custom JavaScript

Add custom JavaScript in `/assets/js/` and reference in `_config.yml`.

## Search

The site includes full-text search powered by lunr.js. All markdown content is automatically indexed.

## Testing Locally

Before pushing changes, test locally:

```bash
# Install dependencies
bundle install

# Build and serve
bundle exec jekyll serve --livereload

# Test for broken links (optional)
bundle exec htmlproofer ./_site --disable-external
```

## Troubleshooting

### Build Failures

If the GitHub Pages build fails:

1. Check the Actions tab for error messages
2. Test locally with `bundle exec jekyll build`
3. Verify all markdown syntax is valid
4. Check that all links are valid

### Missing Dependencies

If you see dependency errors:

```bash
# Update bundle
bundle update

# Clean and rebuild
bundle exec jekyll clean
bundle exec jekyll build
```

### Theme Issues

If the theme doesn't load correctly:

1. Verify `_config.yml` has correct theme settings
2. Check that `Gemfile` includes the theme
3. Try forcing a rebuild in GitHub Pages settings

## Contributing to Documentation

We welcome documentation contributions! To contribute:

1. Fork the repository
2. Create a branch for your changes
3. Edit markdown files in `docs/pages/`
4. Test locally with Jekyll
5. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full guidelines.

## Resources

- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Just the Docs Theme](https://just-the-docs.github.io/just-the-docs/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Markdown Guide](https://www.markdownguide.org/)

## Support

If you have questions about the documentation:

- Open an issue: [github.com/wflo-ai/wflo/issues](https://github.com/wflo-ai/wflo/issues)
- Start a discussion: [github.com/wflo-ai/wflo/discussions](https://github.com/wflo-ai/wflo/discussions)

---

**Last Updated**: 2025-11-10
