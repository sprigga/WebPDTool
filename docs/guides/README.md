# WebPDTool Documentation Guides

## Overview

This directory contains practical guides for developing, testing, and maintaining WebPDTool. Each guide focuses on specific aspects of the system.

## Table of Contents

### Core Architecture and Integration

#### 1. [Measurement and TestPlan Integration Guide](./measurement_testplan_integration.md)
**Target Audience:** Developers, Test Engineers

Comprehensive guide explaining how measurements, instruments, and test plans work together.

**Topics Covered:**
- TestPlan model structure and field mapping
- BaseMeasurement abstract class and PDTool4 validation logic
- 17 measurement implementations (POWER_READ, RELAY, RF tests, etc.)
- 25 instrument drivers and hardware abstraction
- Measurement registry and dynamic dispatch
- Complete data flow from API to hardware
- Integration patterns and best practices

**Key Sections:**
- Architecture Components Overview
- Complete Data Flow Diagrams
- Example: Voltage Check Flow
- Parameter Design in TestPlan.parameters JSON field
- Error Handling Patterns
- Common Issues and Solutions

**Use This Guide When:**
- Adding a new measurement type
- Understanding how test execution works
- Debugging measurement failures
- Implementing instrument drivers
- Writing integration tests

---

#### 2. [API Testing Examples](./api_testing_examples.md)
**Target Audience:** QA Engineers, Developers

Practical examples for testing WebPDTool APIs at unit, integration, and end-to-end levels.

**Topics Covered:**
- Unit tests for measurement validation (7 limit types, 3 value types)
- Service layer integration tests with mocked instruments
- End-to-end API tests from HTTP request to database
- Test structure and organization best practices
- Mock-based testing without real hardware

**Test Coverage:**
- BaseMeasurement validation (none/lower/upper/both/equality/partial/inequality)
- PowerRead/PowerSet measurements with instrument mocking
- Relay and Chassis control measurements
- MeasurementService orchestration
- Complete test session flow (create → start → check results)

**Use This Guide When:**
- Writing tests for new measurements
- Setting up CI/CD testing pipelines
- Debugging test failures
- Understanding test patterns
- Ensuring measurement validation correctness

---

### Development Workflow

#### 3. [Test Plan Import Guide](./README_import_testplan.md)
**Target Audience:** Test Engineers, DevOps

Step-by-step instructions for importing PDTool4 CSV test plans into WebPDTool.

**Topics Covered:**
- CSV file format and field mapping
- Single file import vs batch import
- Docker container usage
- Validation and error handling
- Troubleshooting common import issues

**Use This Guide When:**
- Migrating test plans from PDTool4
- Setting up new test projects
- Batch importing multiple test plans
- Verifying import results

---

#### 4. [Code Review Guidelines](./code_review.md)
**Target Audience:** Developers, Architects

Standards and criteria for reviewing WebPDTool code.

**Review Criteria:**
1. Functionality - Does it work correctly?
2. Readability - Is the code clear and maintainable?
3. Architecture - Does it fit the system design?
4. Security - Are there vulnerabilities?
5. Performance - Is it efficient?
6. Test Coverage - Are there adequate tests?

**Use This Guide When:**
- Conducting peer code reviews
- Evaluating pull requests
- Refactoring code
- Assessing code quality

---

#### 5. [Ralph Loop Usage Guide](./ralph_loop_usage.md)
**Target Audience:** Advanced Users

Instructions for using the Ralph Loop feature for iterative task execution.

**Topics Covered:**
- Ralph Loop setup and activation
- Completion promise mechanism
- Iteration control and stopping conditions
- Best practices and use cases

**Use This Guide When:**
- Performing iterative refinement tasks
- Running multi-step automated workflows
- Understanding Ralph Loop behavior

---

### Command and UML Documentation

#### 6. [Command Field Usage Guide](./command_field_usage.md)
**Target Audience:** Test Engineers

Explains how to use the `command` field in test plans for various test types.

**Topics Covered:**
- Command field syntax for different case_types
- Console command examples
- Comport (serial) command examples
- TCPIP command examples
- Android ADB command examples

**Use This Guide When:**
- Writing CommandTest measurements
- Debugging command execution issues
- Converting PDTool4 command syntax

---

#### 7. [UML Diagram Guide](./uml_diagram.md)
**Target Audience:** Architects, Developers

System architecture diagrams and component relationships.

**Topics Covered:**
- System architecture overview
- Component interaction diagrams
- Database entity relationships
- Data flow visualizations

**Use This Guide When:**
- Understanding system architecture
- Planning new features
- Onboarding new developers

---

#### 8. [Summary Best Practices](./summary_best_practices.md)
**Target Audience:** All Developers

General best practices for WebPDTool development.

**Topics Covered:**
- Coding standards
- Documentation practices
- Git workflow
- Testing guidelines

**Use This Guide When:**
- Starting development on WebPDTool
- Establishing team conventions
- Reviewing development processes

---

## Quick Reference

### For New Developers

1. Start with [UML Diagram Guide](./uml_diagram.md) to understand architecture
2. Read [Measurement and TestPlan Integration](./measurement_testplan_integration.md) to understand core concepts
3. Use [API Testing Examples](./api_testing_examples.md) to write your first tests
4. Follow [Code Review Guidelines](./code_review.md) before submitting code

### For Test Engineers

1. Use [Test Plan Import Guide](./README_import_testplan.md) to import test plans
2. Reference [Command Field Usage](./command_field_usage.md) for command syntax
3. Consult [Measurement and TestPlan Integration](./measurement_testplan_integration.md) for test plan structure
4. Use [API Testing Examples](./api_testing_examples.md) for validation testing

### For QA Engineers

1. Read [API Testing Examples](./api_testing_examples.md) for test patterns
2. Use [Measurement and TestPlan Integration](./measurement_testplan_integration.md) to understand validation logic
3. Reference [Code Review Guidelines](./code_review.md) for quality standards

### For Architects

1. Review [UML Diagram Guide](./uml_diagram.md) for system overview
2. Study [Measurement and TestPlan Integration](./measurement_testplan_integration.md) for architecture patterns
3. Apply [Code Review Guidelines](./code_review.md) for design reviews
4. Reference [Summary Best Practices](./summary_best_practices.md) for architectural decisions

---

## Related Documentation

### Project Root Documentation

- **[CLAUDE.md](../../CLAUDE.md)** - Claude Code AI assistant guidance, architecture overview, and development commands
- **[README.md](../../README.md)** - Project setup, installation, and getting started

### Architecture Documentation

- **[Backend Analysis](../architecture/)** - Detailed backend module analysis
  - `backend_complete_analysis.md` - Comprehensive backend codebase analysis
  - `backend_module_relationships.md` - Module dependency analysis
  - `backend_request_flows.md` - API request flow documentation

### Code Review Documentation

- **[Code Reviews](../code_review/)** - Code review reports and issue tracking
  - Latest reviews organized by date
  - Issues categorized by severity (CRITICAL/HIGH/MEDIUM/LOW)

### Measurement Documentation

- **[Measurement Specs](../Measurement/)** - PDTool4 measurement module analysis
  - PDTool4 architecture reference
  - Measurement type specifications
  - Compatibility requirements

### Library Documentation

- **[lowsheen_lib](../lowsheen_lib/)** - Lowsheen hardware control library
- **[Polish](../Polish/)** - Polish framework analysis

---

## Contributing

When adding new guides:

1. Follow the structure of existing guides
2. Include practical examples and code snippets
3. Target a specific audience (Developers/Test Engineers/QA/Architects)
4. Add "Use This Guide When:" section with clear use cases
5. Update this README.md with a link to your new guide
6. Follow naming convention: `lowercase_with_underscores.md`

---

## Feedback

If you find issues in the documentation or have suggestions for new guides:

1. Open an issue in the project repository
2. Provide specific feedback on which section needs improvement
3. Suggest additional topics that should be documented

---

## Document Versions

| Document | Last Updated | Version |
|----------|-------------|---------|
| README.md | 2026-02-05 | 1.0.0 |
| measurement_testplan_integration.md | 2026-02-05 | 1.0.0 |
| api_testing_examples.md | 2026-02-05 | 1.0.0 |
| code_review.md | 2026-02-05 | 1.0.0 |
| ralph_loop_usage.md | 2026-02-05 | 1.0.0 |
| command_field_usage.md | 2026-01-08 | 1.0.0 |
| README_import_testplan.md | 2025-12-24 | 1.0.0 |
| summary_best_practices.md | 2025-12-16 | 1.0.0 |
| uml_diagram.md | 2026-02-05 | 1.0.0 |
