# ADR Framework Specification

A structured methodology for organizing Architecture Decision Records in Claude Code plugin projects (and general software projects). Designed for reuse across repositories.

**Version**: 1.0
**Origin**: Derived from audit of vsify-me-claude-plugin ADR corpus (13 ADRs, Feb 2026)

---

## 1. Three-Layer Taxonomy

Every ADR belongs to exactly one layer. The layer determines reusability, audience, and where it lives on disk.

### Layer 1: Platform (prefix: `P`)

Decisions about **how to build** with the framework. These are reusable across any project using the same technology (e.g., Claude Code plugins, React apps, Go microservices).

**Characteristics**:
- Describes structural patterns, component conventions, or runtime behavior
- References framework capabilities, not domain logic
- A new project in a completely different domain would still benefit from this ADR

**Examples**:
- How to define named agents with model grade assignments
- Standard phase-based execution structure for commands
- Plugin manifest conventions (auto-discovery vs explicit paths)
- Stateless command design principles
- User interaction patterns (structured prompts vs free-text)

### Layer 2: Governance (prefix: `G`)

Decisions about **guardrails and operational safety**. These constrain agent behavior, enforce process boundaries, or define security policies.

**Characteristics**:
- Prescribes what agents/automation must NOT do (behavioral boundaries)
- Defines authorization, privilege, or approval policies
- Usually motivated by a specific incident where automation misbehaved
- Reusable across projects with similar automation risk profiles

**Examples**:
- Version management is manual-only (agents must not bump versions)
- Tool authorization allowlists/blocklists for agents
- Mandatory approval gates before irreversible actions
- Secret/credential handling policies

### Layer 3: Domain (prefix: `D`)

Decisions about **what this specific project does**. These encode business logic, methodology, or workflow design unique to this project's problem space.

**Characteristics**:
- Describes algorithms, classification systems, or analysis strategies
- References specific commands, skills, or features by name
- A project in a different domain would not need this ADR
- May include inventories or registries of project-specific components

**Examples**:
- Deduplication methodology for batch error analysis
- Complexity gates and fix safety classification tiers
- Language-agnostic design for multi-stack code analysis
- Specific agent-to-command topology mapping
- Skill inventory and interaction flow diagrams

### Layer Assignment Decision Tree

```
Is this about how the framework/platform works?
  YES -> Platform (P)
  NO  |

Is this about constraining automation behavior or enforcing safety?
  YES -> Governance (G)
  NO  |

Is this about what this specific project does or how its features work?
  YES -> Domain (D)
```

### Identifying Mixed ADRs

A mixed ADR is one that contains content belonging to two or more layers. Common symptoms:

- A "Platform" ADR that lists specific project commands or skills by name
- A "Domain" ADR that includes generic framework guidance applicable to any project
- An ADR that starts with universal principles but ends with a project-specific inventory

**Resolution**: Split the ADR into two documents -- one per layer. The platform half gets a `P` prefix, the domain half gets a `D` prefix. Both reference each other in their `related` field.

---

## 2. Directory Structure

```
docs/architecture/decisions/
  README.md              # Index with all three layers
  platform/              # Reusable framework patterns
    ADR-P001-*.md
    ADR-P002-*.md
  governance/            # Operational guardrails
    ADR-G001-*.md
    ADR-G002-*.md
  domain/                # Project-specific decisions
    ADR-D001-*.md
    ADR-D002-*.md
```

### Naming Convention

```
ADR-{layer}{number}-{kebab-case-title}.md

Examples:
  ADR-P001-named-agents-as-components.md
  ADR-G001-manual-version-management.md
  ADR-D001-dedup-first-methodology.md
```

- **Layer prefix**: `P` (Platform), `G` (Governance), `D` (Domain)
- **Number**: Three-digit, zero-padded, sequential within each layer
- **Title**: Kebab-case, descriptive, max ~50 characters

### Flat Directory Alternative

For smaller projects (fewer than 10 ADRs), a flat structure with prefixed filenames is acceptable:

```
docs/architecture/decisions/
  README.md
  ADR-P001-named-agents.md
  ADR-G001-version-management.md
  ADR-D001-dedup-methodology.md
```

The layer prefix provides the same taxonomic signal without subdirectory overhead.

---

## 3. ADR File Format

### Frontmatter Schema

```yaml
---
type: adr
id: "P001"                        # Layer prefix + number (string)
title: "Human-Readable Title"
date_created: "YYYY-MM-DD"
date_modified: "YYYY-MM-DD"
version: "1.0"                    # ADR document version (not project version)
decision_status: proposed          # proposed | accepted | deprecated | superseded
layer: platform                    # platform | governance | domain
category: architecture             # Free-form (architecture, methodology, ux, etc.)
tags: [tag1, tag2]                 # Searchable keywords
depends_on: ["P002", "G001"]       # IDs of ADRs this decision builds upon
impacts: ["D003"]                  # IDs of ADRs influenced by this decision
superseded_by: null                # ID of the ADR that replaces this one
plugin_artifacts:                  # Files in the project governed by this ADR
  - type: agent                    # agent | skill | command | test | config
    name: component-name
    status: implemented            # proposed | implemented | deprecated
---
```

### Required Fields

| Field | Purpose |
|-------|---------|
| `id` | Unique identifier with layer prefix |
| `title` | Human-readable name |
| `date_created` | When the ADR was first written |
| `date_modified` | Last substantive update |
| `decision_status` | Current lifecycle state |
| `layer` | Taxonomy classification |
| `depends_on` | What this ADR builds upon |
| `impacts` | What this ADR influences |

### Body Structure

```markdown
# ADR-{id}: {title}

**Deciders**: [Who made this decision]
**Context**: [Brief context -- feature, incident, refactor that prompted this]

## Context
[Problem statement and background. Why was a decision needed?]

## Decision
[What was decided. The normative content -- what MUST, SHOULD, or MAY be done.]

## Consequences

**Positive**:
- [Benefits]

**Negative**:
- [Costs, risks, tradeoffs]

**Mitigation**:
- [How negatives are addressed]

## Alternatives Considered
[Other options evaluated and why they were rejected]

## Related Decisions
- ADR-{id}: {title} -- [brief note on relationship]
```

### Optional Sections

| Section | When to Include |
|---------|-----------------|
| `## Implementation` | When the ADR prescribes specific file changes or code patterns |
| `## Migration Pattern` | When the ADR changes an existing convention (before/after) |
| `## Validation` | When automated tests enforce the decision |
| `## Metrics` | When the decision has measurable outcomes |

---

## 4. Cross-Reference Rules

### Bidirectional Consistency

Every `depends_on` relationship MUST have a corresponding `impacts` entry in the referenced ADR:

```
ADR-P001: depends_on: ["P002"]
ADR-P002: impacts: ["P001"]       <- MUST exist
```

### Cross-Layer References

References across layers are expected and encouraged:

```
ADR-D001 (domain) depends_on ADR-P003 (platform)
  -> "Our dedup methodology uses the phase-based execution structure"

ADR-G001 (governance) depends_on ADR-P005 (platform)
  -> "Version management policy applies to the plugin manifest format"
```

### No Circular Dependencies

If two ADRs were co-developed and inform each other, use a `related` note in the body rather than circular `depends_on`:

```yaml
# BAD -- circular
ADR-P003: depends_on: ["P004"]
ADR-P004: depends_on: ["P003"]

# GOOD -- pick the primary direction, note the relationship
ADR-P003: depends_on: ["P004"]
ADR-P004: impacts: ["P003"]
# In ADR-P004's Related Decisions section:
# "ADR-P003 and ADR-P004 were co-developed and inform each other."
```

### Supersession

When an ADR is replaced:

1. Set `decision_status: superseded` on the old ADR
2. Set `superseded_by: "{new_id}"` on the old ADR
3. Add a note at the top of the old ADR's body: `> **Superseded by [ADR-{new_id}](./{new_file})**`
4. The new ADR should reference the old one in its Context section

### Merging ADRs

When consolidating two ADRs into one:

1. The surviving ADR absorbs the content and gets a version bump
2. The retired ADR gets `decision_status: superseded` and `superseded_by: "{survivor_id}"`
3. All external references to the retired ADR are updated to point to the survivor

---

## 5. README Index Template

```markdown
# Architecture Decision Records

## Index

### Platform Decisions
| ID | Title | Status | Date |
|----|-------|--------|------|
| [P001](platform/ADR-P001-*.md) | Title | Accepted | YYYY-MM-DD |

### Governance Decisions
| ID | Title | Status | Date |
|----|-------|--------|------|
| [G001](governance/ADR-G001-*.md) | Title | Accepted | YYYY-MM-DD |

### Domain Decisions
| ID | Title | Status | Date |
|----|-------|--------|------|
| [D001](domain/ADR-D001-*.md) | Title | Accepted | YYYY-MM-DD |

## Decision Map
[Mermaid diagram showing dependency relationships across all layers]

## Superseded Decisions
| ID | Title | Superseded By | Date |
|----|-------|---------------|------|
```

### Decision Map Conventions

Use color coding by layer in Mermaid diagrams:

```
Platform nodes:   fill:#e1f5ff (light blue)
Governance nodes: fill:#fff3e0 (light orange)
Domain nodes:     fill:#e8f5e9 (light green)
Superseded nodes: fill:#f5f5f5 (gray), dashed border
```

---

## 6. Validation Checklist

Use this checklist when auditing an ADR set. Each item should pass.

### Per-ADR Checks

- [ ] `id` uses correct layer prefix (`P`, `G`, `D`)
- [ ] `layer` field matches the directory the file is in
- [ ] `date_created` and `date_modified` are accurate (not copy-paste errors)
- [ ] `decision_status` reflects current state
- [ ] Every entry in `depends_on` has a corresponding `impacts` in the referenced ADR
- [ ] Every entry in `impacts` has a corresponding `depends_on` in the referenced ADR
- [ ] No circular `depends_on` chains
- [ ] `superseded_by` is set if `decision_status` is `superseded`
- [ ] Body contains all required sections: Context, Decision, Consequences, Alternatives
- [ ] No content from a different layer is embedded (check for mixed ADRs)
- [ ] Code examples are labeled as pseudocode/illustration if not actual project code
- [ ] `plugin_artifacts` lists files this ADR governs (if applicable)

### Corpus-Level Checks

- [ ] README index lists every ADR file that exists on disk
- [ ] Every ADR file on disk appears in the README index
- [ ] No ID gaps within a layer (P001, P002, P003 -- not P001, P003)
- [ ] Decision Map in README reflects current `depends_on`/`impacts` relationships
- [ ] Superseded Decisions section lists all ADRs with `decision_status: superseded`
- [ ] No two ADRs in the same layer cover substantially the same functional area

### Layer Health Checks

- [ ] Platform ADRs do not reference project-specific commands/skills/agents by name
- [ ] Domain ADRs do not contain generic framework guidance that belongs in Platform
- [ ] Governance ADRs are motivated by a documented incident or risk
- [ ] Mixed ADRs have been identified and split (or documented as intentionally mixed)

---

## 7. Migration Guide: Flat ADRs to Layered Structure

For projects with an existing flat ADR set (e.g., `ADR-001` through `ADR-013`):

### Step 1: Classify Each ADR

Create a classification table:

```markdown
| Current ID | Title | Layer | New ID | Notes |
|------------|-------|-------|--------|-------|
| ADR-001 | Multi-Agent Coordination | Mixed | P001 + D001 | Split: principles vs topology |
| ADR-002 | Dedup-First Methodology | Domain | D002 | Clean, no split needed |
| ADR-006 | Stateless Command Design | Platform | P003 | Clean, no split needed |
| ADR-012 | Manual Version Management | Governance | G001 | Clean, no split needed |
```

### Step 2: Handle Mixed ADRs

For each ADR classified as "Mixed":

1. Identify which paragraphs/sections belong to which layer
2. Create two new ADR files (one per layer)
3. Add cross-references between the split halves
4. Mark the original as superseded by both new IDs

### Step 3: Renumber and Relocate

1. Assign new IDs with layer prefixes
2. Move files to layer subdirectories
3. Update all `depends_on` and `impacts` references to use new IDs
4. Update the README index

### Step 4: Create Redirect Map

Maintain a mapping from old IDs to new IDs for transition period:

```markdown
## ID Migration Map

| Old ID | New ID(s) | Notes |
|--------|-----------|-------|
| ADR-001 | ADR-P001, ADR-D001 | Split into platform principles + domain topology |
| ADR-002 | ADR-D002 | Renumbered only |
| ADR-006 | ADR-P003 | Reclassified to Platform |
```

### Step 5: Validate

Run the full validation checklist (Section 6) against the migrated corpus.

---

## 8. Anti-Patterns

### ADR as Registry

**Symptom**: An ADR that keeps growing as new components are added, becoming a living inventory rather than a point-in-time decision.

**Example**: A "Skills Architecture" ADR that was written for 4 skills but now lists 9 with detailed interaction diagrams.

**Fix**: Keep the ADR focused on the *decision* (why skills, how they're structured). Move the inventory to a separate reference document or to individual component READMEs.

### ADR as Tutorial

**Symptom**: Extensive code examples showing how to use the pattern, what not to do, edge cases, and step-by-step workflows. The ADR reads like documentation rather than a decision record.

**Fix**: Trim to 1-2 key examples that illustrate the decision. Move tutorial content to a developer guide or the component's own documentation.

### Phantom Cross-References

**Symptom**: `depends_on` or `impacts` fields that are stale -- they reference ADRs that have been superseded, renumbered, or deleted.

**Fix**: Run the bidirectional consistency check from the validation checklist after every ADR change.

### Version-Coupled Grouping

**Symptom**: ADRs grouped by the project version they were introduced in (e.g., "v1.1.0 ADRs", "v2.0.0 ADRs"). Version labels become meaningless as the project evolves.

**Fix**: Group by layer (Platform/Governance/Domain) or by functional area. Record the originating version in the ADR's metadata, not in the index grouping.

### Date Drift

**Symptom**: `date_created` values copied from a template or earlier ADR without updating, resulting in incorrect historical records.

**Fix**: Include date validation in the automated test suite -- at minimum, verify dates are not in the future and not before the project's creation date.

---

## 9. Automated Enforcement

If your project has a test suite for ADR validation, enforce these rules:

```bash
# 1. Every ADR file has required frontmatter fields
for field in id title date_created decision_status layer depends_on impacts; do
  # Verify field exists in YAML frontmatter
done

# 2. Layer prefix in ID matches layer field
# ADR-P* must have layer: platform
# ADR-G* must have layer: governance
# ADR-D* must have layer: domain

# 3. Bidirectional cross-references
# For each depends_on entry, verify the target ADR has this ID in its impacts

# 4. No orphan files (every .md in decisions/ is in README index)

# 5. Superseded ADRs have superseded_by set

# 6. Date sanity (date_created <= date_modified, both <= today)
```

---

## Appendix: Quick-Start for New Projects

To bootstrap an ADR framework in a new project:

1. Create the directory structure:
   ```
   docs/architecture/decisions/
     README.md
     platform/
     governance/
     domain/
   ```

2. Copy this specification into `docs/adr-framework-specification.md`

3. Write your first ADR -- typically a Platform decision about the project's foundational architecture

4. Add an ADR validation script to your test suite (see Section 9)

5. Update the README index after each new ADR

6. Periodically audit using the validation checklist (Section 6)
