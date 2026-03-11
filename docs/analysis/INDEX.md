# Architecture Analysis Index

This directory contains comprehensive technical analysis documents covering various aspects of the WebPDTool project's architecture, refactoring efforts, and field migration tracking.

## General Architecture Documents (New)

1. **[architecture_overview.md](./architecture_overview.md)**
   - Complete project architecture overview
   - Technology stack decomposition
   - Key components and their interactions
   - Development commands and service ports
   - Architecture strengths and design patterns

2. **[measurement_abstraction_layer.md](./measurement_abstraction_layer.md)**
   - Deep dive into PDTool4 compatibility layer
   - BaseMeasurement class and lifecycle
   - 17 measurement implementations
   - Validation logic with 7 limit types and 3 value types
   - Registry system and extensibility patterns
   - Integration with MeasurementService

3. **[frontend_architecture.md](./frontend_architecture.md)**
   - Vue 3 Composition API architecture
   - Pinia state management (auth, project, users)
   - Axios API integration with JWT
   - Vue Router with authentication guards
   - Component architecture and reusability
   - 10 main views and their responsibilities

4. **[test_execution_engine.md](./test_execution_engine.md)**
   - TestEngine singleton orchestration
   - MeasurementService dispatching
   - InstrumentManager connection pooling
   - runAllTest mode implementation
   - Complete execution lifecycle
   - Concurrency and async patterns

5. **[architecture_highlights.md](./architecture_highlights.md)**
   - Summary of key architectural decisions
   - Core strengths and technical choices
   - Data flow diagrams
   - Performance optimizations
   - Security considerations
   - Future enhancement opportunities

## Specific Refactoring Analyses (Existing)

6. **[case-type-code-path-tracing.md](./case-type-code-path-tracing.md)**
   - Complete code path tracing for `case_type` field
   - Migration to `switch_mode` consolidation
   - Impact analysis across 14 files with 26 code locations
   - Forward compatibility considerations
   - Based on refactoring plan: `merge-case-type-to-switch-mode.md`

7. **[lowsheen_lib_migration_validation_2026_02_24.md](./lowsheen_lib_migration_validation_2026_02_24.md)**
   - Validation of `lowsheen_lib/` → `app/measurements/` + `app/services/instruments/` migration
   - Strangler fig pattern success assessment
   - Coverage matrix: 15 scripts evaluated
   - Gap identification: MDO34 missing implementation, legacy cleanup paths remain
   - Risk assessment with severity ratings
   - Based on deprecation analysis: `LOWSHEEN_LIB_DEPRECATION_ANALYSIS_2026_02_23.md`

8. **[field-usage-analysis.md](./field-usage-analysis.md)**
   - Field usage analysis for `execute_name` and `case_type`
   - Decision: hide `execute_name` (frontend-only, backend doesn't use), keep `case_type` (core business logic)
   - Data flow tracing across 5 layers (CSV → DB → API → Frontend → Backend services)
   - Implementation recommendations

## Analysis Categories

### Architectural Understanding
- **architecture_overview.md**: Full project structure
- **frontend_architecture.md**: Frontend component design
- **test_execution_engine.md**: Execution orchestration
- **measurement_abstraction_layer.md**: Core measurement system
- **architecture_highlights.md**: Key decisions summary

### Refactoring & Migration
- **case-type-code-path-tracing.md**: Field consolidation analysis
- **field-usage-analysis.md**: Field usage determination
- **lowsheen_lib_migration_validation_2026_02_24.md**: Library migration validation

## Related Documents

### Architecture Guidelines
- `/CLAUDE.md` - Project development guide and CLAUDE agent instructions
- `../architecture/ARCHITECTURE_INDEX.md` - Master architecture reference index
- `../lowsheen_lib/README.md` - Instrument driver documentation
- `../pytest-migration-summary.md` - Test framework migration guide

### Refactoring Plans
- `../refactoring/field-merging/merge-case-type-to-switch-mode.md`
- `../code_review/LOWSHEEN_LIB_DEPRECATION_ANALYSIS_2026_02_23.md`

## Quick Reference Table

| Document | Type | Scope | Status |
|----------|------|-------|--------|
| architecture_overview.md | Architecture | End-to-end | ✅ Complete |
| measurement_abstraction_layer.md | Architecture | Layer deep dive | ✅ Complete |
| frontend_architecture.md | Architecture | Frontend only | ✅ Complete |
| test_execution_engine.md | Architecture | Backend orchestration | ✅ Complete |
| architecture_highlights.md | Architecture | Summary | ✅ Complete |
| field-usage-analysis.md | Refactoring | Field analysis | ✅ Complete |
| case-type-code-path-tracing.md | Refactoring | Migration tracking | ✅ Complete |
| lowsheen_lib_migration_validation_2026_02_24.md | Migration | Validation | ✅ Complete |

## Using These Documents

### For New Developers
Start with: `architecture_overview.md` → `measurement_abstraction_layer.md` → `frontend_architecture.md`

### For Refactoring Work
Consult: `field-usage-analysis.md`, `case-type-code-path-tracing.md`, `lowsheen_lib_migration_validation_2026_02_24.md`

### For System Understanding
Read: `architecture_highlights.md` + `test_execution_engine.md`

### For API Development
Reference: `frontend_architecture.md` (API layer section) + `test_execution_engine.md`

## Document Creation Dates

- **2026-03-10**: Initial architecture overview documents (5 files)
- **2026-02-10**: Field usage analysis and case-type tracing
- **2026-02-24**: Lowsheen lib migration validation

## Contributing New Analysis

When adding new analysis documents:

1. Follow existing filename patterns: `topic-date.md` or `topic_description.md`
2. Add entry to this INDEX.md with brief description
3. Reference related documents in "Related Documents" section
4. Maintain consistent markdown formatting and heading hierarchy
5. Include practical examples with file paths and line numbers where applicable
6. Add a "Quick Reference" section for key findings if appropriate

---

**Last Updated:** 2026-03-10
**Total Documents:** 8
**Analysis Coverage:** Complete architecture + 3 active refactoring efforts