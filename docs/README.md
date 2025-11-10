# Wflo Documentation

Documentation for the Wflo secure runtime for AI agents.

## Structure

```
wflo/
├── index.md                 # Homepage
├── docs/
│   ├── ARCHITECTURE.md      # Technical architecture
│   ├── README.md           # This file
│   └── pages/              # Documentation pages
│       ├── features.md     # Features documentation
│       ├── getting-started.md  # Getting started guide
│       ├── use-cases.md    # Real-world use cases
│       ├── examples.md     # Code examples
│       ├── architecture.md # Architecture overview
│       └── contributing.md # Contributing guide
```

## Writing Documentation

### Page Format

All pages should include front matter:

```markdown
---
layout: default
title: Page Title
description: "Page description"
---

# Page Title

Content here...
```

### Code Blocks

Use fenced code blocks:

\```python
from wflo import Workflow

workflow = Workflow("example")
\```

### Styling

- Use `##` for main sections
- Use `###` for subsections
- Keep content focused and concise
- Include code examples where relevant

## Contributing

To update documentation:

1. Edit markdown files in `docs/pages/`
2. Test changes locally
3. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full guidelines.

## Questions?

- Open an issue: [github.com/wflo-ai/wflo/issues](https://github.com/wflo-ai/wflo/issues)
- Start a discussion: [github.com/wflo-ai/wflo/discussions](https://github.com/wflo-ai/wflo/discussions)
