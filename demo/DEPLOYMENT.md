# Deploying wflo Demo to Vercel

## Quick Deploy (Recommended)

### Option 1: Deploy with Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Navigate to demo directory
cd demo

# Deploy
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? (your account)
# - Link to existing project? No
# - Project name: wflo-demo
# - Directory: ./ (current directory)
# - Override settings? No
```

Your demo will be live at: `https://wflo-demo-[random].vercel.app`

### Option 2: Deploy via GitHub (Automatic Deployments)

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your `wflo` repository
4. Configure project:
   - **Root Directory**: `demo`
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
5. Click "Deploy"

Every push to your branch will automatically redeploy!

## Custom Domain Setup

### Configure Subdomain

After deployment, add a custom domain:

1. Go to your Vercel project dashboard
2. Click "Settings" → "Domains"
3. Add domain: `demo.wflo.ai` or `try.wflo.ai`
4. Configure DNS:

```
# Add CNAME record to your DNS provider
Type: CNAME
Name: demo (or try)
Value: cname.vercel-dns.com
```

5. Wait for DNS propagation (5-30 minutes)
6. Your demo will be live at `https://demo.wflo.ai`

## Environment Variables

No environment variables required! This is a fully static demo.

## Production Optimizations

The demo is already optimized:
- ✅ Static generation (SSG)
- ✅ Tailwind CSS purging
- ✅ Next.js image optimization
- ✅ Turbopack for fast builds
- ✅ Standalone output mode

## Build Settings

If asked, use these settings:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "framework": "nextjs"
}
```

## Troubleshooting

### Build Fails

**Problem**: `Module not found: Can't resolve '@tailwindcss/postcss'`

**Solution**: Ensure `@tailwindcss/postcss` is in dependencies (already done)

### Workspace Root Warning

**Problem**: Warning about multiple lockfiles

**Solution**: This is a monorepo warning and can be ignored. Or add to `next.config.mjs`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  turbopack: {
    root: './',  // Add this line
  },
};
```

### 404 on Routes

**Problem**: Routes return 404 after deployment

**Solution**: This is a static export - all routes are pre-rendered. Should work by default.

## Monitoring

After deployment, monitor:
- **Analytics**: Vercel Analytics (free tier)
- **Performance**: Lighthouse scores (should be 90+)
- **Uptime**: Vercel provides 99.99% uptime SLA

## Sharing the Demo

Once deployed, share the link:

1. **For YC Application**: Embed in application materials
2. **For GitHub README**: Add badge and link
3. **For Sales**: Include in pitch decks
4. **Social Media**: Tweet/LinkedIn with demo link

### Suggested GitHub README Badge

```markdown
[![Try Live Demo](https://img.shields.io/badge/Try-Live_Demo-purple?style=for-the-badge)](https://demo.wflo.ai)
```

### Suggested Tweet

```
🚀 Built an interactive demo showing how wflo prevents runaway AI costs

Watch an AI agent loop infinitely ($47 wasted) → Then see wflo halt it at $5 budget

Plus: Human-in-the-Loop approval gates for high-risk operations

Try it: https://demo.wflo.ai

#AI #OpenSource
```

## Recording Demo Video

Once deployed, record a promotional video:

### Setup
1. Open demo at full screen (1920x1080)
2. Use screen recording: OBS, QuickTime, or Loom
3. Record 60-90 seconds

### Script
```
[0-20s] Click "Without wflo" → watch cost escalate
[20-40s] Click "With wflo Budget" → show budget enforcement
[40-70s] Click "With HITL" → interact with approval card
[70-90s] Scroll to metrics comparison table
```

### Export as GIF

```bash
# Using ffmpeg
ffmpeg -i demo-recording.mp4 \
  -vf "fps=10,scale=1200:-1:flags=lanczos" \
  -loop 0 \
  demo.gif

# Optimize
gifsicle -O3 --colors 256 demo.gif -o demo-optimized.gif
```

### Embed in GitHub README

```markdown
![wflo Demo](./demo/demo-optimized.gif)
```

## Cost

Vercel pricing for this demo:
- **Hobby (Free)**: 100GB bandwidth/month - Perfect for demo
- **Pro ($20/month)**: If you need custom domain + analytics

For a demo site, the free tier is more than sufficient.

## Support

If deployment fails:
1. Check Vercel build logs
2. Test locally: `npm run build` in demo directory
3. Open issue: https://github.com/wflo-ai/wflo/issues
