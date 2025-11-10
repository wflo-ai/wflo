import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import { TypeAnimation } from 'react-type-animation';
import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <h1 className={styles.heroTitle}>Engineer reliable AI agents</h1>
        <div className={styles.heroTagline}>
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
        </div>
        <p className={styles.heroSubtitle}>
          The comprehensive platform for building and deploying AI agents safely—with sandboxed execution,
          human approval workflows, cost controls, and full observability.
        </p>
        <div className={styles.buttons}>
          <Link
            className={clsx('button button--primary button--lg', styles.button)}
            to="/docs/getting-started">
            Get Started
          </Link>
          <Link
            className={clsx('button button--lg', styles.buttonGithub)}
            to="https://github.com/wflo-ai/wflo">
            ⭐ View on GitHub
          </Link>
        </div>
        <div className={styles.statusBadge}>
          ⚠️ Early Development - Not production ready yet
        </div>
      </div>
    </header>
  );
}

// Value propositions - 4 key benefits
const valueProps = [
  {
    icon: '👁️',
    title: 'Visibility & Control',
    description: 'Complete observability into every agent action with distributed tracing and real-time monitoring.',
  },
  {
    icon: '⚡',
    title: 'Fast Iteration',
    description: 'Rapid development and testing with instant feedback loops and comprehensive debugging tools.',
  },
  {
    icon: '🛡️',
    title: 'Secure Execution',
    description: 'Sandboxed containers with strict resource limits protect your infrastructure from agent actions.',
  },
  {
    icon: '🔀',
    title: 'Provider Neutral',
    description: 'Works with any LLM provider—OpenAI, Anthropic, local models, or custom implementations.',
  },
];

// Core capabilities
const capabilities = [
  {
    icon: '🔒',
    title: 'Sandboxed Execution',
    description: 'Every agent runs in an isolated Docker container with configurable resource limits and network policies.',
    features: ['Docker-based isolation', 'Resource quotas (CPU, memory)', 'Network policies', 'Filesystem restrictions'],
  },
  {
    icon: '✋',
    title: 'Human Approval Gates',
    description: 'Pause workflows at critical checkpoints to require human review before proceeding with sensitive operations.',
    features: ['Configurable approval points', 'Multi-level approvers', 'Timeout policies', 'Escalation workflows'],
  },
  {
    icon: '💰',
    title: 'Cost Governance',
    description: 'Track and control LLM costs in real-time with automatic budget enforcement across all providers.',
    features: ['Real-time cost tracking', 'Budget limits per workflow', 'Provider cost aggregation', 'Cost alerts'],
  },
  {
    icon: '📊',
    title: 'Full Observability',
    description: 'Distributed tracing, metrics, and structured logging give you complete visibility into agent behavior.',
    features: ['OpenTelemetry integration', 'Custom dashboards', 'Log aggregation', 'Performance metrics'],
  },
  {
    icon: '⏮️',
    title: 'Rollback & Recovery',
    description: 'Automatic state snapshots before critical operations allow you to roll back to any previous state.',
    features: ['Automatic snapshots', 'Point-in-time recovery', 'State versioning', 'Rollback triggers'],
  },
  {
    icon: '🔧',
    title: 'Policy Engine',
    description: 'Define complex governance policies for approval routing, cost limits, and execution controls.',
    features: ['Declarative policy syntax', 'Conditional rules', 'Policy templates', 'Compliance presets'],
  },
];

// Use cases
const useCases = [
  {
    title: 'AI Copilots',
    description: 'Build AI assistants that can take actions on behalf of users with proper safety controls.',
    icon: '🤖',
  },
  {
    title: 'Workflow Automation',
    description: 'Automate complex business processes with AI agents that require human oversight.',
    icon: '⚙️',
  },
  {
    title: 'Data Processing',
    description: 'Process and analyze large datasets with AI agents while controlling costs and resources.',
    icon: '📊',
  },
  {
    title: 'Code Generation',
    description: 'Generate and execute code safely in isolated environments with rollback capabilities.',
    icon: '💻',
  },
];

function ValuePropsSection() {
  return (
    <section className={styles.section}>
      <div className="container">
        <div className={styles.gridFour}>
          {valueProps.map((prop, idx) => (
            <div key={idx} className={styles.valuePropCard}>
              <div className={styles.valuePropIcon}>{prop.icon}</div>
              <h3 className={styles.valuePropTitle}>{prop.title}</h3>
              <p className={styles.valuePropDescription}>{prop.description}</p>
            </div>
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
        <h2 className={styles.sectionTitle}>Core Capabilities</h2>
        <p className={styles.sectionSubtitle}>
          Everything you need to build, deploy, and manage AI agents in production environments.
        </p>
        <div className={styles.gridThree}>
          {capabilities.map((capability, idx) => (
            <div key={idx} className={styles.capabilityCard}>
              <div className={styles.capabilityIcon}>{capability.icon}</div>
              <h3 className={styles.capabilityTitle}>{capability.title}</h3>
              <p className={styles.capabilityDescription}>{capability.description}</p>
              <ul className={styles.featureList}>
                {capability.features.map((feature, fIdx) => (
                  <li key={fIdx}>{feature}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function QuickStartSection() {
  return (
    <section className={styles.section}>
      <div className="container">
        <h2 className={styles.sectionTitle}>Get Started in Minutes</h2>
        <p className={styles.sectionSubtitle}>
          Install Wflo and start building secure AI agents with just a few commands.
        </p>
        <div className={styles.quickStartGrid}>
          <div className={styles.codeBlock}>
            <pre>
              <code>{`# Install Wflo
pip install wflo

# Create a new workflow
wflo init my-agent-workflow

# Run with safety controls
wflo run --budget 10.00 \\
  --require-approval \\
  --sandbox-mode strict`}</code>
            </pre>
          </div>
          <div className={styles.quickStartFeatures}>
            <h3>What you get:</h3>
            <ul>
              <li>✅ Sandboxed execution environment</li>
              <li>✅ Cost tracking and budget limits</li>
              <li>✅ Human approval workflows</li>
              <li>✅ Complete observability</li>
              <li>✅ Rollback capabilities</li>
              <li>✅ Policy enforcement</li>
            </ul>
            <Link
              className="button button--primary button--lg"
              to="/docs/getting-started"
              style={{ marginTop: '1.5rem' }}>
              Read Full Documentation →
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

function UseCasesSection() {
  return (
    <section className={clsx(styles.section, styles.sectionAlt)}>
      <div className="container">
        <h2 className={styles.sectionTitle}>Use Cases</h2>
        <p className={styles.sectionSubtitle}>
          Build secure AI agents for any use case that requires safety, governance, and control.
        </p>
        <div className={styles.gridFour}>
          {useCases.map((useCase, idx) => (
            <div key={idx} className={styles.useCaseCard}>
              <div className={styles.useCaseIcon}>{useCase.icon}</div>
              <h3 className={styles.useCaseTitle}>{useCase.title}</h3>
              <p className={styles.useCaseDescription}>{useCase.description}</p>
            </div>
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
          <div className={styles.stat}>
            <div className={styles.statNumber}>100%</div>
            <div className={styles.statLabel}>Open Source</div>
          </div>
          <div className={styles.stat}>
            <div className={styles.statNumber}>Apache 2.0</div>
            <div className={styles.statLabel}>Licensed</div>
          </div>
          <div className={styles.stat}>
            <div className={styles.statNumber}>Python</div>
            <div className={styles.statLabel}>Built With</div>
          </div>
        </div>
        <div className={styles.finalCta}>
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
        </div>
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
