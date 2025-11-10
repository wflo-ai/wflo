# Deploying the Wflo Documentation Site

The Wflo documentation site is built with **Docusaurus 3** and automatically deploys to GitHub Pages.

## Prerequisites

- Merge this PR to the `main` branch
- GitHub Pages enabled for the repository
- GitHub Actions enabled

## Setup Instructions

### 1. Configure GitHub Pages

Once this PR is merged to `main`:

1. Go to your repository **Settings** → **Pages**
2. Under **Source**, select: **Deploy from a branch**
3. Select branch: `gh-pages`
4. Select folder: `/ (root)`
5. Click **Save**

### 2. Wait for GitHub Action

The GitHub Action will automatically:
1. Install Node.js dependencies
2. Build the Docusaurus site
3. Deploy to the `gh-pages` branch
4. GitHub Pages will serve from there

### 3. Access the Site

After the action completes (2-3 minutes), your site will be live at:

**https://wflo-ai.github.io/wflo**

## Local Development

To work on the documentation site locally:

```bash
cd website
npm install
npm start
```

This will start a local development server at http://localhost:3000

### Make Changes

- Edit docs in `website/docs/`
- Edit homepage in `website/src/pages/index.tsx`
- Edit styles in `website/src/css/custom.css`
- Edit config in `website/docusaurus.config.js`

Changes will hot-reload automatically!

## Build Locally

To test the production build locally:

```bash
cd website
npm run build
npm run serve
```

This builds the site and serves it at http://localhost:3000

## Troubleshooting

### GitHub Action Fails

1. Check the **Actions** tab for error details
2. Ensure `website/package.json` is valid
3. Ensure Node.js 18+ is being used

### Page Not Found (404)

1. Verify GitHub Pages is configured to use `gh-pages` branch
2. Wait 2-3 minutes for GitHub to propagate changes
3. Check the GitHub Action completed successfully

### Styles Not Loading

1. Check `baseUrl` in `docusaurus.config.js` matches your repo name
2. Currently set to `/wflo/` which matches the repository name
3. Clear browser cache and hard refresh (Ctrl+Shift+R / Cmd+Shift+R)

## Manual Deployment

If needed, you can deploy manually:

```bash
cd website

# Set your GitHub username
export GIT_USER=<your-github-username>

# Deploy
npm run deploy
```

This will build and push directly to the `gh-pages` branch.

## Site Structure

```
website/
├── docs/                    # Documentation markdown files
│   ├── intro.md            # Introduction page
│   ├── getting-started.md  # Getting started guide
│   ├── features.md         # Features overview
│   ├── use-cases.md        # Use cases
│   ├── examples.md         # Code examples
│   ├── architecture.md     # Architecture details
│   └── contributing.md     # Contributing guide
├── src/
│   ├── pages/
│   │   ├── index.tsx       # Homepage (React component)
│   │   └── index.module.css
│   └── css/
│       └── custom.css      # Global styles & Midjourney theme
├── static/
│   └── img/                # Images and static assets
├── docusaurus.config.js    # Site configuration
├── sidebars.js             # Sidebar navigation
└── package.json            # Dependencies
```

## Customization

### Update Colors

Edit `website/src/css/custom.css`:

```css
:root {
  --ifm-color-primary: #00d4aa;  /* Change accent color */
  --ifm-background-color: #0a0a0a;  /* Change background */
  /* ... */
}
```

### Update Homepage

Edit `website/src/pages/index.tsx` to change homepage content.

### Add New Docs

1. Create new `.md` file in `website/docs/`
2. Add to `website/sidebars.js` for navigation
3. Commit and push

Changes will auto-deploy on push to `main`.

## Performance

Docusaurus builds are optimized for:
- ⚡ Fast page loads (static site generation)
- 📱 Mobile responsive
- 🔍 SEO optimized
- ♿ Accessible
- 🌙 Dark mode support

## Support

If you encounter issues:

1. Check [Docusaurus docs](https://docusaurus.io/)
2. Open an issue on GitHub
3. Ask in GitHub Discussions
