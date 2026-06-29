# Phase 1: Knowledge Model — Loop Engineering Review

**Status:** APPROVED  
**Date:** 20 June 2026  
**Initial Dataset:** Scheme 33(9)  
**Corpus Scope:** DCPR 2034

---

## 1. Initial Design

The initial design comprises:
1. **The Canonical Knowledge Schema** (`canonical-knowledge-model.schema.yaml`), representing a single source of truth for the regulatory corpus.
2. **Centralized registries** for concepts (`concepts.yaml`), units (`units.yaml`), and precision policies (`precision-policies.yaml`).
3. **The Scheme 33(9) Knowledge Package Instance** (`33-9.yaml`), which models Scheme 33(9) applicability conditions, calculation formulas, and Tables B and C.
4. **An automated validation script** (`validate.py`), which uses JSON Schema validation to enforce strict compliance.

---

## 2. Architect Review

### Critique by System Architect (Agent 1)
* **Scalability:** The schema is highly modular and allows individual schemes to be developed and verified independently. The design of global registries prevents the namespace from decomposing into a set of fragmented, scheme-specific dialects.
* **Maintainability:** Separation of the schema from the calculation runtime ensures that introducing a new scheme does not require writing backend code. The model represents calculations using a declarative AST.
* **Extensibility:** The schema is designed to support 100+ schemes. However, as the corpus grows, loading multiple large scheme packages into memory might become a bottleneck. We must ensure compilation produces a fast, query-optimized projection.

### Findings
* **P1: Global Namespace Collision:** If two packages declare conflicting local facts using the same namespace (e.g. `dcpr:33-9:...`), the compiler may experience naming collisions. We must enforce naming rules prefixing facts with the package ID. (Status: Resolved in target layout).
* **P2: Distributed Package Loading:** When 100+ packages are active, loading all YAMLs synchronously will cause slow server start times. (Status: Deferred to future deployment optimization).

---

## 3. Domain Review

### Critique by Domain Expert (Agent 2)
* **DCPR Definitions & Formulae:** Scheme 33(9) under DCPR 2034 includes complex spatial terms, such as "Basic Ratio" (Land Rate / Construction Rate) and "FSI Base Area" (Gross Area minus reservations and setbacks). The AST representation of the basic ratio and FSI calculations matches the legal intent of Table B and Table C.
* **Source Conflicts:** The unresolved conflict between DTP and MCGM compilations (suburban minimum cluster area of 6,000 sq. m vs 10,000 sq. m, overall consent of 60% vs 70%, and rehab carpet area of 27.88 sq. m vs 25.00 sq. m) is a major legal risk.
* **Exceptions:** Discretionary approvals from authorities (e.g., Municipal Commissioner approval for reduced road width access) are common exceptions that must be modeled as conditional overrides.

### Findings
* **P0: Silent Source Resolution:** Developers must not silently decide which PDF copy is legally binding. The conflict must be declared at the data level. (Status: Resolved. Flagged as a blocker finding `dcpr:33-9:finding-source-conflict` in `33-9.yaml`).
* **P1: Discretionary Authority Approval inputs:** Discretionary road width permissions must require explicit authority approval inputs rather than defaulting to pass/fail. (Status: Resolved. Modeled `access_road_width` checks with clear validation logic).

---

## 4. Knowledge Review

### Critique by Knowledge Engineer (Agent 3)
* **Metadata Completeness:** The initial draft lacked strict metadata validation fields, leaving concepts and units poorly defined. The schema-conforming design improves on this by verifying that every entity, definition, fact, and formula links back to a `SourceSpan` and possesses a `Confidence` profile.
* **Coverage Verification:** The `Coverage` entity ensures that every sentence of a provision is mapped to a modeling status (`MODELED_EXECUTABLE`, `MODELED_NON_EXECUTABLE`, etc.). This guarantees that no provision is silently omitted.

### Findings
* **P0: Schema Property Mismatch:** The initial `scheme-33-9.review-draft.yaml` did not conform to the root property schema of `canonical-knowledge-model.schema.yaml` (e.g. it used `sources` instead of `source_documents`, `knowledge_release` instead of `package`, etc.). (Status: Resolved. Migrated draft to fully compliant `33-9.yaml`).
* **P1: Orphan Concepts:** Concepts used in formulas (like `FloorSpaceIndex`, `PlotArea`) were defined inline in the draft, creating duplicate logic. (Status: Resolved. Extracted to a global concept registry `concepts.yaml`).

---

## 5. Graph Review

### Critique by Graph Engineer (Agent 4)
* **Node-Relationship Consistency:** The compiled knowledge package must easily map to a Neo4j projection. Each entity has `semantic_links` containing references to related facts, formulas, and conditions, allowing the graph builder to build edges (e.g., `(:SCHEME)-[:DEFINES_POLICY]->(:Condition)`) deterministically.
* **Cycle Detection:** The parser must identify circular dependencies in `semantic_links` before building the graph database.

### Findings
* **P1: Acyclic Reference Verification:** If a formula depends on another derived variable that forms a loop (e.g., FSI depends on Rehab BUA, which depends on FSI), the graph will contain execution cycles. We must enforce acyclic compiler verification. (Status: Resolved in Phase 1 design; verification script enforces validation).
* **P2: Neo4j Traversal Limits:** As the graph expands to 100k+ nodes, deep traversals on unindexed nodes will degrade performance. All queries must start from an indexed ID. (Status: Deferred to Phase 4).

---

## 6. Rule Review

### Critique by Rule Engine Engineer (Agent 5)
* **Deterministic Computations:** The rule engine is the source of truth; the LLM (Qwen) does not calculate. Calculations are modeled strictly using mathematical operators (`DIVIDE`, `MULTIPLY`, `ADD`, `MAX`, `SUBTRACT`) in the AST.
* **Typing & Units:** All calculations use `Decimal` strings to prevent binary floating-point errors. Units are verified before executing arithmetic operators.

### Findings
* **P0: Lowercase Operators in Schema:** The JSON Schema defines allowed AST operators in UPPERCASE (e.g. `DIVIDE`, `MULTIPLY`). The draft used lowercase operators (e.g. `divide`, `multiply`). (Status: Resolved. Updated all AST operators to uppercase).
* **P1: Lookup Operator Ambiguity:** The draft used a custom `lookup_percent` operator which is not supported by the schema enums. (Status: Resolved. Replaced with standard `LOOKUP` operator, passing basic ratio and cluster area as arguments).

---

## 7. QA Review

### Critique by QA Engineer (Agent 6)
* **Boundary Cases:** Table B has multiple basic ratio and cluster area bands. Table C has balance sharing percentages. We must verify that inputs falling exactly on boundaries (e.g., basic ratio of exactly 2.00, or cluster area of exactly 10,000 sq. m) evaluate to the correct band.
* **Negative & Invalid Inputs:** QA must stress-test inputs: negative areas, access road widths of 0, or empty inputs. The input contract must enforce constraints to fail-closed on invalid data.

### Findings
* **P1: Band Overlap / Gaps:** In Table B, the basic ratio bands must be clearly bounded (e.g. `lower_exclusive: 4.00, upper_inclusive: 6.00`). (Status: Resolved. Added explicit inclusive/exclusive bounds to table dimensions).
* **P1: Input Validation Constraints:** The input contract must validate numeric bounds. (Status: Resolved. Added validation expressions to input fields, e.g. `gross_cluster_area > 0`).

---

## 8. Security Review

### Critique by Security and Data Integrity Engineer (Agent 7)
* **Data Corruption:** Unreviewed modifications to the canonical YAML can alter calculations without notice. We must implement cryptographic checksums (SHA-256) on all source PDFs and release manifests.
* **Hallucination Risks:** Since Qwen is for explanation only and does not execute math, we must prevent users from injecting prompts through calculation inputs.

### Findings
* **P1: Source Integrity:** The system must refuse calculation requests if the release ID or checksum does not match the manifest. (Status: Resolved. Package manifest captures `source_documents` SHA-256).
* **P2: Input Sanitization:** Ensure FastAPI input parsing blocks SQL or prompt injection sequences. (Status: Deferred to Phase 8).

---

## 9. Revised Design

The design was updated to address all P0 and P1 findings:
1. **Centralized Registries:** Central registries were created under `knowledge/registries/` to prevent duplicate terms and type definitions.
2. **Schema Alignment:** The Scheme 33(9) draft was fully restructured to match the `canonical-knowledge-model.schema.yaml` properties list, resolving the validation mismatches.
3. **AST Uppercasing:** All mathematical and logical operators in the AST were converted to uppercase enums (e.g., `DIVIDE`, `MULTIPLY`, `LOOKUP`, `MAX`) to satisfy JSON Schema rules.
4. **Table Cell Flattening:** Table B and Table C cell values were flattened into a 1D cell list using `row` and `column` numbers, mapping to row and column dimension members.
5. **Strict Constraint Mappings:** Added `constraints` to inputs and detailed `nullable_statuses` to outputs.

---

## 10. Final Approved Design

The final schema-conforming files have been verified using the validation script:
- Schema: [canonical-knowledge-model.schema.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemas/canonical-knowledge-model.schema.yaml)
- Registry of Concepts: [concepts.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/registries/concepts.yaml)
- Registry of Units: [units.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/registries/units.yaml)
- Precision Policies: [precision-policies.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/registries/precision-policies.yaml)
- Scheme 33(9) Package: [33-9.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/instruments/dcpr-2034/schemes/33-9.yaml)

All components are fully validated and approved.
