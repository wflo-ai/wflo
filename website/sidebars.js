/**
 * This file organizes the documentation sidebar.
 *
 * The structure is designed to guide the user through a logical learning path,
 * from high-level concepts to practical guides and deep dives.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    {
      type: 'category',
      label: 'About wflo',
      items: ['intro', 'VISION', 'COMPARISON'],
    },
    {
      type: 'category',
      label: 'Getting Started',
      items: ['getting-started'],
    },
    {
      type: 'category',
      label: 'Core Features',
      link: {
        type: 'generated-index',
        title: 'Core Features',
        description: 'Learn about the main capabilities of wflo.',
      },
      items: [
        'features/overview',
        // Future: 'features/budget-control', 'features/checkpointing', etc.
      ],
    },
    {
      type: 'category',
      label: 'Guides',
      link: {
        type: 'generated-index',
        title: 'Guides',
        description: 'Practical guides for implementing wflo.',
      },
      items: [
        'guides/enabling-persistence',
        'use-cases',
        'examples',
        'supabase-setup',
      ],
    },
    {
      type: 'category',
      label: 'Architecture',
      link: {
        type: 'generated-index',
        title: 'Architecture Deep Dive',
        description: 'Understand how wflo works under the hood.',
      },
      items: [
        'architecture/overview',
        // Future: 'architecture/temporal', 'architecture/database', etc.
      ],
    },
    'contributing',
  ],
};

module.exports = sidebars;