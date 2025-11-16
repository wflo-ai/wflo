# wflo Interactive Demo

Interactive demonstration of wflo's killer features: cost control and human-in-the-loop approval gates.

## 🎯 Purpose

This demo provides a visceral, visual comparison showing:

1. **Without wflo** - Watch costs spiral out of control as an AI agent enters an infinite loop
2. **With Budget Control** - See wflo halt execution when budget limits are reached
3. **With HITL Approval Gates** - Experience the approval workflow for high-risk operations

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) to see the demo.

## 📊 Features

### Before wflo Demo
- Live-updating cost counter that accelerates as agent loops
- Workflow execution log showing redundant LLM calls
- Visual anxiety-inducing cost escalation ($47+ wasted)
- Clear failure message

### After wflo Demo
- Real-time budget bar (0-100%) with color transitions
- Budget enforcement at $5.00 limit
- Graceful workflow termination
- Savings calculation ($45.53 prevented)

### HITL Approval Gate Demo
- Interactive approval card showing:
  - **Who**: Agent identifier
  - **What**: Exact operation (SQL DELETE query)
  - **Why**: Business justification
  - **Risk**: Visual risk level badge (HIGH)
  - **Cost**: Estimated operation cost
- Approve/Reject buttons with optional comments
- Complete audit trail in execution log
- Simulates Slack/email notifications

### Metrics Comparison Table
- Side-by-side comparison of all three scenarios
- 89% cost reduction with budget control
- 100% risk mitigation with HITL gates
- Full audit trail for compliance

## 🎨 Technical Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **Animations**: Custom CSS + Tailwind animations
- **Deployment**: Vercel (recommended)

## 📁 Project Structure

```
demo/
├── app/
│   ├── page.tsx          # Main demo page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── BeforeWfloDemo.tsx      # "Without wflo" component
│   ├── AfterWfloDemo.tsx       # "With budget" component
│   ├── HITLDemo.tsx            # "With HITL" component
│   └── MetricsComparison.tsx   # Comparison table
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.mjs
└── README.md
```

## 🎬 Recording Demo Video

To create a promotional video/GIF:

1. Run the demo locally
2. Use screen recording software (e.g., OBS, QuickTime, Loom)
3. Record 60-90 second sequence:
   - Start with "Without wflo" - let cost reach ~$20
   - Switch to "With wflo" - show budget halt
   - Switch to "HITL" - click through approval flow
   - End on metrics comparison table

4. Convert to GIF using ffmpeg:
```bash
ffmpeg -i demo.mp4 -vf "fps=10,scale=1200:-1:flags=lanczos" demo.gif
```

## 🌐 Deployment

### Deploy to Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Or connect your GitHub repository to Vercel for automatic deployments.

### Environment Variables

No environment variables required - this is a fully client-side demo.

### Custom Domain

After deploying, configure a custom subdomain:
- Recommended: `demo.wflo.ai` or `try.wflo.ai`
- Set up in Vercel dashboard under "Domains"

## 📝 Customization

### Adjusting Simulation Speed

Edit the `setInterval` delays in each component:
- `BeforeWfloDemo.tsx`: Line ~85
- `AfterWfloDemo.tsx`: Line ~115
- `HITLDemo.tsx`: Line ~60

### Changing Budget Limit

Edit `BUDGET_LIMIT` constant in `AfterWfloDemo.tsx` (currently $5.00)

### Customizing Colors

Edit `tailwind.config.ts` to change color scheme:
- Red theme: "Without wflo"
- Green theme: "With budget"
- Purple theme: "With HITL"

## 🎯 Usage Tips

1. **For YC Application**: Embed GIF directly in application materials
2. **For GitHub README**: Add demo link to main repository README
3. **For Sales**: Share demo.wflo.ai link in pitch decks
4. **For Contributors**: Use to quickly explain project value

## 🔗 Links

- [Main Repository](https://github.com/wflo-ai/wflo)
- [Documentation](https://github.com/wflo-ai/wflo/blob/main/README.md)
- [Phase Implementation Roadmap](../docs/PHASED_IMPLEMENTATION_ROADMAP.md)

## 📄 License

MIT License - Same as main wflo project
