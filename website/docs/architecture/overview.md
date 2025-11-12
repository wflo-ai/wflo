---
sidebar_position: 6
title: Architecture
description: Technical architecture of Wflo
---

# Architecture

Technical architecture for the secure AI agent runtime.

## Overview

Wflo is designed as a multi-layered orchestration platform that provides production-grade safety controls for AI agent workflows.

## High-Level Architecture

```
┌─────────────────────────────────────────────┐
│         Wflo Orchestration Engine           │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Workflow │  │  Policy  │  │   Cost   │ │
│  │  Engine  │  │  Engine  │  │  Manager │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │      Observability Layer              │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
           │                │
           ▼                ▼
    ┌─────────────┐  ┌─────────────┐
    │  Sandbox 1  │  │  Sandbox 2  │
    │   (Agent)   │  │   (Agent)   │
    └─────────────┘  └─────────────┘
```

## Core Components

### Workflow Manager
- Parse and validate workflow definitions
- Schedule workflow execution
- Manage workflow lifecycle

### State Manager
- Maintain workflow execution state
- Provide state snapshots for rollback
- Handle state persistence

### Approval Gates
- Pause workflow execution at checkpoints
- Route approval requests
- Track approval audit trail

### Cost Manager
- Track costs per workflow execution
- Enforce budget limits
- Support multiple pricing providers

### Sandbox Runtime
- Provide isolated execution environments
- Enforce resource limits
- Manage container lifecycle

[See full architecture →](https://github.com/wflo-ai/wflo/blob/main/docs/ARCHITECTURE.md)
