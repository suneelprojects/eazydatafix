# EasyDataFix Architecture

**Version:** 1.0
**Status:** Approved
**Applies From:** Sprint 2+

---

# Vision

EasyDataFix is designed as a modular, extensible, and maintainable data quality framework.

The goal is to keep the Core framework small and stable while allowing new functionality to be added through plugins without modifying the Core.

---

# Core Principles

## 1. Stable Core

The Core framework is responsible for orchestration.

It contains:

- Public API
- Engines
- Models
- Registry
- Configuration
- Reporting orchestration

The Core should rarely change.

---

## 2. Extensible Plugins

Plugins provide functionality.

Examples include:

- Datasources
- Missing Value Strategies
- Validators
- Assessment Rules
- Transformers
- Exporters

Future plugins may include:

- SQL Connectors
- Spark Connectors
- AI Modules
- Cloud Integrations

---

# Architecture Overview

```
                User API
       (fix / assess / profile)
                    │
                    ▼
             Core Framework
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
 Assessment      Fix Engine   Dataset Loader
      │
      ▼
          Plugin Registry
      │
 ┌────┼────┬────┬────┬────┬────┐
 ▼    ▼    ▼    ▼    ▼    ▼
Strategy
Validator
Assessment
Datasource
Transformer
Exporter
```

---

# Core Responsibilities

The Core is responsible for:

- Workflow orchestration
- Plugin discovery
- Plugin execution
- Configuration
- Error handling
- Reporting
- Public APIs

The Core never performs plugin-specific logic.

---

# Plugin Responsibilities

Plugins implement reusable functionality.

Plugins should:

- Have a unique name
- Perform one responsibility
- Be independent
- Be replaceable

Plugins must never communicate directly with other plugins.

---

# Plugin Communication

Plugins never call other plugins.

All communication flows through the Core.

```
Core
 │
 ├── Strategy Plugin
 ├── Validator Plugin
 ├── Datasource Plugin
 └── Exporter Plugin
```

The Core orchestrates execution.

---

# Plugin Lifecycle

## Startup

```
Initialize Registry

↓

Register Built-in Plugins

↓

Validate Registry

↓

Application Ready
```

---

## Runtime

```
Lookup Plugin Class

↓

Instantiate Plugin

↓

Execute Plugin

↓

Destroy Plugin
```

The registry stores plugin classes, not instances.

A new instance is created whenever execution is required.

---

# Plugin Registration

Registration is explicit.

Example:

```
register_builtin_plugins()
```

Automatic registration using decorators is intentionally avoided.

---

# Plugin Categories

Official categories are:

- strategy
- validator
- assessment
- datasource
- transformer
- exporter
- reporter

Categories are centrally defined to avoid inconsistent naming.

---

# Plugin Metadata

Required:

- name

Optional:

- version
- author
- description
- enabled

Plugins use duck typing.

No inheritance from a common Plugin base class is required.

---

# Execution Context

Plugins execute using an Execution Context rather than relying on global state.

The context may include:

- dataframe
- configuration
- metadata
- report
- execution_id

Future versions may extend the context without changing plugin interfaces.

---

# Registry Design

EasyDataFix uses one shared registry.

The registry:

- stores plugin classes
- validates registrations
- provides lookup
- supports future third-party plugins

---

# Backward Compatibility

The following public APIs must remain stable.

```
easydatafix.fix()

easydatafix.assess()

easydatafix.profile()
```

Internal implementation may evolve without affecting users.

---

# Development Workflow

Every feature follows five phases.

## Phase 1

Architecture Design

Discuss requirements.

No implementation.

---

## Phase 2

Architecture Approval

Freeze architecture.

---

## Phase 3

Implementation

One file at a time.

Complete files only.

Tests after every milestone.

---

## Phase 4

Verification

Regression testing.

Full test suite.

---

## Phase 5

Release

Git

GitHub

PyPI

Documentation

Release Notes

---

# Long-Term Roadmap

## Sprint 1

Datasource Architecture

Released.

---

## Sprint 2

Plugin Architecture

---

## Sprint 3

Execution Context

Plugin SDK

---

## Sprint 4

Plugin Discovery

Third-party Plugins

---

## Sprint 5

AI Modules

SQL Connectors

Spark Connectors

Cloud Integrations

---

# Design Philosophy

EasyDataFix follows a simple principle.

> The Core orchestrates.

> Plugins perform the work.

This separation keeps the framework maintainable, extensible, and backward compatible.
