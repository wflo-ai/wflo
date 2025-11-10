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
          Engineer reliable AI agents
        </motion.h1>
        <motion.div
          className={styles.heroTagline}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.4, 0, 0.2, 1] }}
        >
          <TypeAnimation
            sequence={[
              'Production-ready infrastructure for AI agents',
              2500,
              'Sandboxed execution with safety controls',
              2500,
              'Cost governance and approval gates',
              2500,
              'Built for mission-critical workflows',
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
          The comprehensive platform for building and deploying AI agents safely—with sandboxed execution,
          human approval workflows, cost controls, and full observability.
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
    title: 'Visibility & Control',
    description: 'Complete observability into every agent action with distributed tracing and real-time monitoring.',
  },
  {
    icon: Zap,
    title: 'Fast Iteration',
    description: 'Rapid development and testing with instant feedback loops and comprehensive debugging tools.',
  },
  {
    icon: Shield,
    title: 'Secure Execution',
    description: 'Sandboxed containers with strict resource limits protect your infrastructure from agent actions.',
  },
  {
    icon: Shuffle,
    title: 'Provider Neutral',
    description: 'Works with any LLM provider—OpenAI, Anthropic, local models, or custom implementations.',
  },
];

// Core capabilities with Lucide icons
const capabilities = [
  {
    icon: Lock,
    title: 'Sandboxed Execution',
    description: 'Every agent runs in an isolated Docker container with configurable resource limits and network policies.',
    features: ['Docker-based isolation', 'Resource quotas (CPU, memory)', 'Network policies', 'Filesystem restrictions'],
  },
  {
    icon: Hand,
    title: 'Human Approval Gates',
    description: 'Pause workflows at critical checkpoints to require human review before proceeding with sensitive operations.',
    features: ['Configurable approval points', 'Multi-level approvers', 'Timeout policies', 'Escalation workflows'],
  },
  {
    icon: DollarSign,
    title: 'Cost Governance',
    description: 'Track and control LLM costs in real-time with automatic budget enforcement across all providers.',
    features: ['Real-time cost tracking', 'Budget limits per workflow', 'Provider cost aggregation', 'Cost alerts'],
  },
  {
    icon: BarChart3,
    title: 'Full Observability',
    description: 'Distributed tracing, metrics, and structured logging give you complete visibility into agent behavior.',
    features: ['OpenTelemetry integration', 'Custom dashboards', 'Log aggregation', 'Performance metrics'],
  },
  {
    icon: RotateCcw,
    title: 'Rollback & Recovery',
    description: 'Automatic state snapshots before critical operations allow you to roll back to any previous state.',
    features: ['Automatic snapshots', 'Point-in-time recovery', 'State versioning', 'Rollback triggers'],
  },
  {
    icon: Settings,
    title: 'Policy Engine',
    description: 'Define complex governance policies for approval routing, cost limits, and execution controls.',
    features: ['Declarative policy syntax', 'Conditional rules', 'Policy templates', 'Compliance presets'],
  },
];

// Use cases with Lucide icons
const useCases = [
  {
    title: 'AI Copilots',
    description: 'Build AI assistants that can take actions on behalf of users with proper safety controls.',
    icon: Bot,
  },
  {
    title: 'Workflow Automation',
    description: 'Automate complex business processes with AI agents that require human oversight.',
    icon: Cog,
  },
  {
    title: 'Data Processing',
    description: 'Process and analyze large datasets with AI agents while controlling costs and resources.',
    icon: Database,
  },
  {
    title: 'Code Generation',
    description: 'Generate and execute code safely in isolated environments with rollback capabilities.',
    icon: Code2,
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
  const codeExample = `# Install Wflo
pip install wflo

# Create a new workflow
wflo init my-agent-workflow

# Run with safety controls
wflo run --budget 10.00 \\
  --require-approval \\
  --sandbox-mode strict`;

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
          Get Started in Minutes
        </motion.h2>
        <motion.p
          className={styles.sectionSubtitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Install Wflo and start building secure AI agents with just a few commands.
        </motion.p>
        <div className={styles.quickStartGrid}>
          <AnimatedCard className={styles.codeBlock} delay={0.2}>
            <CodeBlock code={codeExample} />
          </AnimatedCard>
          <AnimatedCard className={styles.quickStartFeatures} delay={0.3}>
            <h3>What you get:</h3>
            <ul>
              <li><Check size={18} className={styles.checkIcon} /> Sandboxed execution environment</li>
              <li><Check size={18} className={styles.checkIcon} /> Cost tracking and budget limits</li>
              <li><Check size={18} className={styles.checkIcon} /> Human approval workflows</li>
              <li><Check size={18} className={styles.checkIcon} /> Complete observability</li>
              <li><Check size={18} className={styles.checkIcon} /> Rollback capabilities</li>
              <li><Check size={18} className={styles.checkIcon} /> Policy enforcement</li>
            </ul>
            <Link
              className="button button--primary button--lg"
              to="/docs/getting-started"
              style={{ marginTop: '1.5rem' }}>
              Read Full Documentation →
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
            <div className={styles.statNumber}>100%</div>
            <div className={styles.statLabel}>Open Source</div>
          </motion.div>
          <motion.div
            className={styles.stat}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className={styles.statNumber}>Apache 2.0</div>
            <div className={styles.statLabel}>Licensed</div>
          </motion.div>
          <motion.div
            className={styles.stat}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div className={styles.statNumber}>Python</div>
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
          <h2>Ready to build secure AI agents?</h2>
          <p>Join developers building production-ready AI workflows with safety controls.</p>
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
