import React, { useState, useEffect } from 'react';
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
  Shuffle,
  Lock,
  Hand,
  DollarSign,
  BarChart3,
  RotateCcw,
  Settings,
  Bot,
  Cog,
  Database,
  Code2,
  Copy,
  Check,
  Play,
  Pause,
  AlertCircle,
  CheckCircle,
  Clock,
  Activity
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

// Interactive workflow visualization
function WorkflowVisualization() {
  const [activeStep, setActiveStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  const steps = [
    { icon: Play, label: 'Request', color: 'var(--accent-cyan)', description: 'Agent receives task' },
    { icon: AlertCircle, label: 'Approval', color: 'var(--accent-violet)', description: 'Human review required' },
    { icon: Lock, label: 'Sandbox', color: 'var(--accent-neon-green)', description: 'Isolated execution' },
    { icon: Activity, label: 'Execute', color: 'var(--accent-electric-blue)', description: 'Running workflow' },
    { icon: CheckCircle, label: 'Complete', color: 'var(--accent-emerald)', description: 'Task completed' },
  ];

  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % steps.length);
    }, 2000);

    return () => clearInterval(interval);
  }, [isPlaying, steps.length]);

  return (
    <motion.div
      className={styles.workflowVisualization}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.6 }}
    >
      <div className={styles.workflowHeader}>
        <h3>Agent Lifecycle</h3>
        <button
          className={styles.workflowControl}
          onClick={() => setIsPlaying(!isPlaying)}
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
        </button>
      </div>
      <div className={styles.workflowSteps}>
        {steps.map((step, idx) => {
          const StepIcon = step.icon;
          const isActive = idx === activeStep;
          const isPast = idx < activeStep;

          return (
            <React.Fragment key={idx}>
              <motion.div
                className={clsx(styles.workflowStep, {
                  [styles.workflowStepActive]: isActive,
                  [styles.workflowStepPast]: isPast,
                })}
                onClick={() => setActiveStep(idx)}
                animate={{
                  scale: isActive ? 1.1 : 1,
                  opacity: isActive ? 1 : isPast ? 0.6 : 0.4,
                }}
                transition={{ duration: 0.3 }}
              >
                <div className={styles.workflowStepIcon} style={{ color: step.color }}>
                  <StepIcon size={24} strokeWidth={2} />
                </div>
                <div className={styles.workflowStepLabel}>{step.label}</div>
                <div className={styles.workflowStepDescription}>{step.description}</div>
              </motion.div>
              {idx < steps.length - 1 && (
                <div className={styles.workflowConnector}>
                  <motion.div
                    className={styles.workflowConnectorLine}
                    initial={{ scaleX: 0 }}
                    animate={{
                      scaleX: idx < activeStep ? 1 : 0,
                      backgroundColor: idx < activeStep ? step.color : 'var(--ifm-hr-border-color)',
                    }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </motion.div>
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
          Run AI agents safely in production
        </motion.h1>
        <motion.div
          className={styles.heroTagline}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.4, 0, 0.2, 1] }}
        >
          <TypeAnimation
            sequence={[
              'Docker-based sandboxing with resource limits',
              2500,
              'Temporal.io orchestration with durable execution',
              2500,
              'Real-time cost tracking across LLM providers',
              2500,
              'PostgreSQL state snapshots with rollback',
              2500,
              'OpenTelemetry traces with Jaeger visualization',
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
          Production-ready orchestration platform for AI agents with Docker-based sandboxing,
          Temporal.io workflows, real-time cost tracking, and rollback capabilities. Built with Python, PostgreSQL, and OpenTelemetry.
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
            Get Started
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
          ⚠️ Early Development - Not production ready yet
        </motion.div>
        <motion.div
          className={styles.badgeContainer}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5, ease: [0.4, 0, 0.2, 1] }}
        >
          <a href="https://github.com/wflo-ai/wflo" target="_blank" rel="noopener noreferrer" className={styles.badge}>
            <img src="https://img.shields.io/github/stars/wflo-ai/wflo?style=social" alt="GitHub stars" />
          </a>
          <a href="https://github.com/wflo-ai/wflo/blob/main/LICENSE" target="_blank" rel="noopener noreferrer" className={styles.badge}>
            <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License" />
          </a>
          <a href="https://github.com/wflo-ai/wflo" target="_blank" rel="noopener noreferrer" className={styles.badge}>
            <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
          </a>
        </motion.div>
        <WorkflowVisualization />
      </div>
    </header>
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

// Value propositions - 4 key benefits with Lucide icons
const valueProps = [
  {
    icon: Eye,
    title: 'Production Observability',
    description: 'OpenTelemetry tracing, Prometheus metrics, and structured logging with Jaeger visualization for complete visibility.',
  },
  {
    icon: Zap,
    title: 'Durable Workflows',
    description: 'Temporal.io-powered orchestration with automatic retries, exponential backoff, and failure recovery.',
  },
  {
    icon: Shield,
    title: 'Docker Sandboxing',
    description: 'Isolated containers with CPU/memory limits, network isolation, and read-only filesystems using aiodocker.',
  },
  {
    icon: Shuffle,
    title: 'Multi-Provider Support',
    description: 'Track costs across OpenAI, Anthropic, Cohere, and local models with unified cost attribution.',
  },
];

// Core capabilities with Lucide icons
const capabilities = [
  {
    icon: Lock,
    title: 'Docker-Based Sandboxing',
    description: 'Every workflow runs in isolated Docker containers with strict resource limits, network isolation, and read-only filesystems.',
    features: ['aiodocker integration', 'CPU & memory quotas', 'Network disabled by default', 'Timeout enforcement'],
  },
  {
    icon: Hand,
    title: 'Human Approval Gates',
    description: 'Risk-based approval routing with Slack/webhook notifications. Auto-approve low-risk operations, require review for high-risk changes.',
    features: ['Risk-based routing', 'Configurable approvers', 'Slack notifications', 'Complete audit trails'],
  },
  {
    icon: DollarSign,
    title: 'Real-Time Cost Tracking',
    description: 'Track LLM API costs across providers with circuit breakers, multi-threshold alerts, and per-workflow budget enforcement.',
    features: ['OpenAI/Anthropic/Cohere', 'Budget circuit breakers', '50%-75%-90% alerts', 'Cost attribution'],
  },
  {
    icon: BarChart3,
    title: 'OpenTelemetry Tracing',
    description: 'Complete distributed traces with span tracking for each workflow step. Jaeger UI integration for trace visualization.',
    features: ['Jaeger exporter', 'Prometheus metrics', 'structlog JSON logs', 'Correlation IDs'],
  },
  {
    icon: RotateCcw,
    title: 'State Snapshots & Rollback',
    description: 'PostgreSQL-backed state snapshots before critical operations. Point-in-time recovery with compensating transactions.',
    features: ['Automatic snapshots', 'asyncpg persistence', 'Manual rollback API', 'State versioning'],
  },
  {
    icon: Settings,
    title: 'DAG-Based Workflows',
    description: 'Define workflows as directed acyclic graphs with dependency resolution, parallel execution, and topological sorting.',
    features: ['Topological sort', 'Circular dep detection', 'Parallel steps', 'Pydantic validation'],
  },
];

// Use cases with Lucide icons
const useCases = [
  {
    title: 'Financial Services',
    description: 'Fraud detection agents with mandatory approval gates for high-value transactions and complete audit trails for compliance.',
    icon: DollarSign,
  },
  {
    title: 'Healthcare & Compliance',
    description: 'HIPAA-compliant agent workflows with sandboxed execution, data isolation, and detailed observability for audit requirements.',
    icon: Shield,
  },
  {
    title: 'E-commerce Automation',
    description: 'Customer service agents with approval gates for refunds, cost tracking for LLM usage, and rollback for incorrect changes.',
    icon: Bot,
  },
  {
    title: 'Data Engineering',
    description: 'ETL agents with state snapshots for recovery, budget controls to prevent runaway costs, and observability for debugging.',
    icon: Database,
  },
];

function ValuePropsSection() {
  return (
    <section className={styles.section}>
      <div className="container">
        <div className={styles.gridFour}>
          {valueProps.map((prop, idx) => (
            <AnimatedCard key={idx} className={styles.valuePropCard} delay={idx * 0.1}>
              <div className={styles.valuePropIcon}>
                <prop.icon size={40} strokeWidth={1.5} />
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

function CapabilitiesSection() {
  return (
    <section className={clsx(styles.section, styles.sectionAlt)}>
      <div className="container">
        <motion.h2
          className={styles.sectionTitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          Core Capabilities
        </motion.h2>
        <motion.p
          className={styles.sectionSubtitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Everything you need to build, deploy, and manage AI agents in production environments.
        </motion.p>
        <div className={styles.gridThree}>
          {capabilities.map((capability, idx) => (
            <AnimatedCard key={idx} className={styles.capabilityCard} delay={idx * 0.1}>
              <div className={styles.capabilityIcon}>
                <capability.icon size={48} strokeWidth={1.5} />
              </div>
              <h3 className={styles.capabilityTitle}>{capability.title}</h3>
              <p className={styles.capabilityDescription}>{capability.description}</p>
              <ul className={styles.featureList}>
                {capability.features.map((feature, fIdx) => (
                  <li key={fIdx}>{feature}</li>
                ))}
              </ul>
            </AnimatedCard>
          ))}
        </div>
      </div>
    </section>
  );
}

function CodeBlock({ code }: { code: string }) {
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
        <code>{code}</code>
      </pre>
    </div>
  );
}

function QuickStartSection() {
  const codeExample = `# Clone and set up development environment
git clone https://github.com/wflo-ai/wflo.git
cd wflo

# Install dependencies with Poetry
poetry install

# Start infrastructure (PostgreSQL, Redis, Temporal, Jaeger)
docker-compose up -d

# Run the Temporal worker
poetry run python -m wflo.temporal.worker

# Define and execute a workflow (Python SDK - Coming Soon)
# from wflo import Workflow, WorkflowStep
# workflow = Workflow(...)
# result = await workflow.execute()`;

  return (
    <section className={styles.section}>
      <div className="container">
        <motion.h2
          className={styles.sectionTitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          Get Started (Early Development)
        </motion.h2>
        <motion.p
          className={styles.sectionSubtitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Wflo is in early development. Set up the development environment to explore the architecture and contribute.
        </motion.p>
        <div className={styles.quickStartGrid}>
          <AnimatedCard className={styles.codeBlock} delay={0.2}>
            <CodeBlock code={codeExample} />
          </AnimatedCard>
          <AnimatedCard className={styles.quickStartFeatures} delay={0.3}>
            <h3>Tech Stack:</h3>
            <ul>
              <li><Check size={18} className={styles.checkIcon} /> Python 3.11+ with async/await</li>
              <li><Check size={18} className={styles.checkIcon} /> Temporal.io for orchestration</li>
              <li><Check size={18} className={styles.checkIcon} /> PostgreSQL + Redis backend</li>
              <li><Check size={18} className={styles.checkIcon} /> Docker sandbox runtime</li>
              <li><Check size={18} className={styles.checkIcon} /> OpenTelemetry + Jaeger</li>
              <li><Check size={18} className={styles.checkIcon} /> Poetry dependency management</li>
            </ul>
            <Link
              className="button button--primary button--lg"
              to="/docs/getting-started"
              style={{ marginTop: '1.5rem' }}>
              Read Architecture Docs →
            </Link>
          </AnimatedCard>
        </div>
      </div>
    </section>
  );
}

function UseCasesSection() {
  return (
    <section className={clsx(styles.section, styles.sectionAlt)}>
      <div className="container">
        <motion.h2
          className={styles.sectionTitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          Use Cases
        </motion.h2>
        <motion.p
          className={styles.sectionSubtitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Build secure AI agents for any use case that requires safety, governance, and control.
        </motion.p>
        <div className={styles.gridFour}>
          {useCases.map((useCase, idx) => (
            <AnimatedCard key={idx} className={styles.useCaseCard} delay={idx * 0.1}>
              <div className={styles.useCaseIcon}>
                <useCase.icon size={48} strokeWidth={1.5} />
              </div>
              <h3 className={styles.useCaseTitle}>{useCase.title}</h3>
              <p className={styles.useCaseDescription}>{useCase.description}</p>
            </AnimatedCard>
          ))}
        </div>
      </div>
    </section>
  );
}

function StatsSection() {
  return (
    <section className={styles.section}>
      <div className="container">
        <div className={styles.statsContainer}>
          <motion.div
            className={styles.stat}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <div className={styles.statNumber}>v0.1.0</div>
            <div className={styles.statLabel}>Early Stage</div>
          </motion.div>
          <motion.div
            className={styles.stat}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className={styles.statNumber}>Apache 2.0</div>
            <div className={styles.statLabel}>Open Source</div>
          </motion.div>
          <motion.div
            className={styles.stat}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div className={styles.statNumber}>Python 3.11+</div>
            <div className={styles.statLabel}>Built With</div>
          </motion.div>
        </div>
        <motion.div
          className={styles.finalCta}
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2>Building in public. Join the journey.</h2>
          <p>Wflo is in active development. Star the repo, contribute code, or follow along as we build production-ready AI agent infrastructure.</p>
          <div className={styles.buttons}>
            <Link
              className="button button--primary button--lg"
              to="https://github.com/wflo-ai/wflo">
              Star on GitHub
            </Link>
            <Link
              className="button button--secondary button--lg"
              to="/docs/getting-started">
              Read the Docs
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - The secure runtime for AI agents`}
      description="Production-ready infrastructure for running AI agents safely with sandboxed execution, human approval gates, cost governance, and full observability.">
      <HomepageHeader />
      <main>
        <ValuePropsSection />
        <CapabilitiesSection />
        <QuickStartSection />
        <UseCasesSection />
        <StatsSection />
      </main>
    </Layout>
  );
}
