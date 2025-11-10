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
        <h1 className={styles.heroTitle}>{siteConfig.title}</h1>
        <div className={styles.heroTagline}>
          <TypeAnimation
            sequence={[
              'The secure runtime for AI agents',
              2000,
              'Production-ready AI infrastructure',
              2000,
              'Enterprise-grade safety controls',
              2000,
              'Built for mission-critical workflows',
              2000,
            ]}
            wrapper="span"
            speed={50}
            repeat={Infinity}
            cursor={true}
            style={{ display: 'inline-block' }}
          />
        </div>
        <p className={styles.heroSubtitle}>
          Production-ready infrastructure for running AI agents safely with sandboxed execution,
          human approval gates, cost governance, and full observability.
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
      </div>
    </header>
  );
}

const problems = [
  {
    icon: '💸',
    title: 'Runaway Costs',
    description: 'One misconfigured agent can burn thousands in API fees before you notice.',
  },
  {
    icon: '🔒',
    title: 'Security Risks',
    description: 'Agents executing arbitrary code without isolation puts your systems at risk.',
  },
  {
    icon: '🚫',
    title: 'Irreversible Actions',
    description: 'No way to undo mistakes when agents make wrong decisions.',
  },
  {
    icon: '📊',
    title: 'No Visibility',
    description: 'Can\'t debug what agents actually did or why they made certain decisions.',
  },
  {
    icon: '⚖️',
    title: 'Compliance Gaps',
    description: 'No audit trails or approval workflows for regulated industries.',
  },
  {
    icon: '🎯',
    title: 'The Solution',
    description: 'Wflo provides enterprise-grade safety controls for production AI workflows.',
  },
];

const features = [
  {
    title: '🛡️ Sandboxed Execution',
    description: 'Isolated container environments with strict resource limits. No agent can access your host system.',
  },
  {
    title: '✋ Human Approval Gates',
    description: 'Pause workflows at critical checkpoints. Define approvers, timeouts, and escalation policies.',
  },
  {
    title: '💰 Cost Governance',
    description: 'Real-time cost tracking across all LLM providers with automatic budget enforcement.',
  },
  {
    title: '⏮️ Rollback & Recovery',
    description: 'Automatic state snapshots before critical operations. Roll back to any previous state.',
  },
  {
    title: '📈 Full Observability',
    description: 'Distributed tracing, metrics, and structured logging for every workflow execution.',
  },
  {
    title: '🔧 Policy Engine',
    description: 'Define complex policies for approval routing, cost limits, and execution controls.',
  },
];

export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - ${siteConfig.tagline}`}
      description="The secure runtime for AI agents. Production-ready infrastructure for running AI agents safely.">
      <HomepageHeader />
      <main>
        {/* Problems Section */}
        <section className={styles.section}>
          <div className="container">
            <h2 className={styles.sectionTitle}>The Problem</h2>
            <div className={styles.grid}>
              {problems.map((problem, idx) => (
                <div key={idx} className={styles.card}>
                  <div className={styles.cardIcon}>{problem.icon}</div>
                  <h3 className={styles.cardTitle}>{problem.title}</h3>
                  <p className={styles.cardDescription}>{problem.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className={clsx(styles.section, styles.sectionAlt)}>
          <div className="container">
            <h2 className={styles.sectionTitle}>Core Features</h2>
            <div className={styles.grid}>
              {features.map((feature, idx) => (
                <div key={idx} className={styles.card}>
                  <h3 className={styles.cardTitle}>{feature.title}</h3>
                  <p className={styles.cardDescription}>{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Quick Start Section */}
        <section className={styles.section}>
          <div className="container">
            <h2 className={styles.sectionTitle}>Quick Start</h2>
            <div className={styles.codeBlock}>
              <pre>
                <code>{`# Install
pip install wflo

# Create workflow
wflo init my-agent-workflow

# Run with safety controls
wflo run --budget 10.00 --require-approval`}</code>
              </pre>
            </div>
            <div className={styles.centerButton}>
              <Link
                className="button button--primary button--lg"
                to="/docs/getting-started">
                Read Full Documentation →
              </Link>
            </div>
          </div>
        </section>

        {/* Status Banner */}
        <section className={styles.section}>
          <div className="container">
            <div className={styles.statusBanner}>
              <span className={styles.statusIcon}>⚠</span>
              <span className={styles.statusText}>Early Development - Not production ready yet</span>
            </div>
            <p className={styles.statusSubtext}>
              We're actively building in public. Star the repo to follow our progress!
            </p>
          </div>
        </section>
      </main>
    </Layout>
  );
}
