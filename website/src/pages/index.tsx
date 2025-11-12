import React, { useState } from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import { TypeAnimation } from 'react-type-animation';
import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import {
  Eye,
  Zap,
  Shield,
  DollarSign,
  Code2,
  Copy,
  Check,
  AlertTriangle,
  Terminal,
} from 'lucide-react';
import styles from './index.module.css';

// Animated gradient background component
function AnimatedGradient() {
  return (
    <div className={styles.gradientBackground}>
      <div className={styles.gradientOrb1}></div>
      <div className={styles.gradientOrb2}></div>
      <div className={styles.gradientOrb3}></div>
    </div>
  );
}

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <AnimatedGradient />
      <div className="container" style={{ position: 'relative', zIndex: 1 }}>
        <motion.h1
          className={styles.heroTitle}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
        >
          The Safety Layer for AI Agents
        </motion.h1>
        <motion.div
          className={styles.heroTagline}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.4, 0, 0.2, 1] }}
        >
          <TypeAnimation
            sequence={[
              'Ship AI Agents Without Burning Your Budget.',
              2500,
              'From Prototype to Production.',
              2500,
              'Stop runaway costs with real-time budgets.',
              2500,
              'Never lose progress with automatic checkpoints.',
              2500,
              'Prevent failures with built-in resilience.',
              2500,
              'Works with your existing agent code.',
              2500,
            ]}
            wrapper="span"
            speed={50}
            repeat={Infinity}
            cursor={true}
            style={{ display: 'inline-block' }}
          />
        </motion.div>
        <motion.p
          className={styles.heroSubtitle}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: [0.4, 0, 0.2, 1] }}
        >
          Wflo adds production-grade cost control, checkpointing, and resilience
          to your existing AI agent frameworks like LangGraph and CrewAI.
        </motion.p>
        <motion.div
          className={styles.buttons}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: [0.4, 0, 0.2, 1] }}
        >
          <Link
            className={clsx('button button--primary button--lg', styles.buttonPrimary)}
            to="/docs/getting-started">
            Get Started in 5 Minutes
          </Link>
          <Link
            className={clsx('button button--lg', styles.buttonGithub)}
            to="https://github.com/wflo-ai/wflo">
            ⭐ View on GitHub
          </Link>
        </motion.div>
        <motion.div
          className={styles.statusBadge}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.4, ease: [0.4, 0, 0.2, 1] }}
        >
          <Check size={16} /> <b>Phase 1 SDK is Production Ready.</b> Core features are stable.
        </motion.div>
      </div>
    </header>
  );
}

function CodeBlock({ code, language = 'python' }: { code: string, language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={styles.codeBlockWrapper}>
      <button className={styles.copyButton} onClick={handleCopy} aria-label="Copy code">
        {copied ? <Check size={18} /> : <Copy size={18} />}
      </button>
      <pre className={styles.codeBlockPre}>
        <code className={`language-${language}`}>{code}</code>
      </pre>
    </div>
  );
}

function BeforeAfterSection() {
  const beforeCode = `from crewai import Agent, Task, Crew

# Your existing agent code
researcher = Agent(role="Researcher", goal="...", llm=gpt4)
writer = Agent(role="Writer", goal="...", llm=gpt4)
task1 = Task(description="Research topic", agent=researcher)
task2 = Task(description="Write article", agent=writer)
crew = Crew(agents=[researcher, writer], tasks=[task1, task2])

# How much will this cost? What if it fails?
result = crew.kickoff()
`;

  const afterCode = `from wflo.sdk.workflow import WfloWorkflow
from crewai import Agent, Task, Crew

# Your existing agent code (unchanged)
researcher = Agent(role="Researcher", goal="...", llm=gpt4)
writer = Agent(role="Writer", goal="...", llm=gpt4)
task1 = Task(description="Research topic", agent=researcher)
task2 = Task(description="Write article", agent=writer)
crew = Crew(agents=[researcher, writer], tasks=[task1, task2])

# Wrap it with wflo for safety
workflow = WfloWorkflow(
  name="crew-ai-blog-post",
  budget_usd=5.00  // ✅ Budget enforced
)
result = await workflow.execute(crew, {}) // ✅ Costs tracked
`;

  return (
    <section className={styles.section}>
      <div className="container">
        <motion.div
          className={styles.gridTwo}
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className={styles.column}>
            <h2 className={styles.columnTitle}><AlertTriangle className={styles.columnIcon} /> Your Agent is a Black Box</h2>
            <p className={styles.columnDescription}>
              Your agent code is powerful, but in production, it's unpredictable. What if it gets stuck in a loop? How much will it cost? What happens if a step fails?
            </p>
            <CodeBlock code={beforeCode} />
          </div>
          <div className={styles.column}>
            <h2 className={styles.columnTitle}><Shield className={styles.columnIcon} /> wflo Gives You the Controls</h2>
            <p className={styles.columnDescription}>
              Add `wflo` in two lines to get production-grade safety. Enforce budgets, track costs, and enable checkpoints without rewriting your agent logic.
            </p>
            <CodeBlock code={afterCode} />
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function DemoSection() {
  return (
    <section className={clsx(styles.section, styles.sectionAlt)}>
      <div className="container text--center">
        <motion.h2
            className={styles.sectionTitle}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
          See It In Action
        </motion.h2>
        <motion.p
          className={styles.sectionSubtitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          This is how wflo makes the invisible, visible.
        </motion.p>
        <AnimatedCard delay={0.2}>
          <div className={styles.demoPlaceholder}>
            [Placeholder for 'Before & After' Demo Video/GIF]
            <p>This video will show an agent's costs spiraling out of control, and then how `wflo` stops it right at the budget limit.</p>
          </div>
        </AnimatedCard>
      </div>
    </section>
  );
}

const valueProps = [
  {
    icon: DollarSign,
    title: 'Cost Control',
    description: 'Set a hard budget for any workflow. Wflo halts execution before you overspend, guaranteed.',
  },
  {
    icon: Eye,
    title: 'Full Observability',
    description: 'Get detailed cost breakdowns and execution history for every run, stored in your own database.',
  },
  {
    icon: Zap,
    title: 'Built-in Resilience',
    description: 'Automatic retries for transient errors and circuit breakers for major outages, built right in.',
  },
  {
    icon: Code2,
    title: 'Framework Agnostic',
    description: 'Drop `wflo` into your existing LangGraph, CrewAI, or custom agent code without a rewrite.',
  },
];

function ValuePropsSection() {
  return (
    <section className={clsx(styles.section, styles.sectionAlt)}>
      <div className="container">
        <div className={styles.gridFour}>
          {valueProps.map((prop, idx) => (
            <AnimatedCard key={idx} className={styles.valuePropCard} delay={idx * 0.1}>
              <div className={styles.valuePropIcon}>
                <prop.icon size={32} strokeWidth={1.5} />
              </div>
              <h3 className={styles.valuePropTitle}>{prop.title}</h3>
              <p className={styles.valuePropDescription}>{prop.description}</p>
            </AnimatedCard>
          ))}
        </div>
      </div>
    </section>
  );
}

function FinalCtaSection() {
  return (
    <section className={styles.section}>
      <div className="container">
        <motion.div
          className={styles.finalCta}
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2>Ready to Ship Agents Safely?</h2>
          <p>Explore the docs, run the 5-minute quickstart, or star the repo on GitHub to follow our progress.</p>
          <div className={styles.buttons}>
            <Link
              className="button button--primary button--lg"
              to="/docs/getting-started">
              Get Started
            </Link>
            <Link
              className="button button--secondary button--lg"
              to="https://github.com/wflo-ai/wflo">
              Star on GitHub
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// Animated card wrapper with scroll detection
function AnimatedCard({ children, className, delay = 0 }) {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{ duration: 0.5, delay, ease: [0.4, 0, 0.2, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}


export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - The Safety Layer for AI Agents`}
      description="Production-grade cost control, checkpointing, and resilience for your AI agent workflows. Works with LangGraph, CrewAI, and more.">
      <HomepageHeader />
      <main>
        <ValuePropsSection />
        <BeforeAfterSection />
        <DemoSection />
        <FinalCtaSection />
      </main>
    </Layout>
  );
}
