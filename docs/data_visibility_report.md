# DCPR Knowledge Engine - Data Visibility & Source Audit Report

This report provides 100% visibility into the data sources, calculations, tables, regulations, and references utilized across the Mumbai DCPR 2034 Knowledge Engine. It classifies the information sources into three distinct tiers:
1. **REAL DATA:** Mapped directly from the statutory DCPR 2034 text or evaluated dynamically at runtime.
2. **MOCK DATA:** Placeholders, stub files, or simulated elements used to compile dependencies or test functionality.
3. **HARDCODED DATA:** Static constants, preset configurations, citation registries, or local fallback templates.

---

## Component-by-Component Visibility Map

### 1. Ingestion & Extraction Pipeline

* **Component Location:** [docling_adapter.py](file:///f:/FullStack%20Projects/DCPR/knowledge/pipeline/docling_adapter.py), [parsers.py](file:///f:/FullStack%20Projects/DCPR/knowledge/pipeline/parsers.py), [reference_resolver.py](file:///f:/FullStack%20Projects/DCPR/knowledge/pipeline/reference_resolver.py)
* **Status:**
  * 🔴 **MOCK DATA (Fallback Transcriptions):**
    * **OCR Fallbacks:** Because `MUMBAI-DCPR.pdf` is a scanned document and Tesseract/OCR endpoints are offline in the local workspace sandbox, `DoclingAdapter._extract_with_pymupdf` (lines 47-108) intercepts pages 188, 189, 194, 195, and 196 and extracts them from a **pre-transcribed mock dictionary**. This simulated layout text mimics layout blocks and table grids for test automation.
  * 🟡 **HARDCODED DATA:**
    * **Package Metadata:** `package_id` (`dcpr:package:33-9`), `instrument_id` (`dcpr:instrument:2034`), and `extraction_run_id` (`run:33-9:extraction`) are hardcoded inside the `SemanticParser` class constructor in `parsers.py` (lines 13-15).
    * **Reference Citation Mappings:** The mappings of unstructured text references to stable target entity IDs (e.g. mapping `regulation:31:subregulation:3` to `dcpr:regulation:31-3`) are hardcoded in the `corpus_registry` dictionary in `ReferenceResolver` (lines 8-29).
  * 🟢 **REAL DATA:**
    * **General Ingestion:** Non-scanned text pages are extracted dynamically from `MUMBAI-DCPR.pdf` via PyMuPDF block extractors. PDF file hashing is performed dynamically.

---

### 2. Canonical Knowledge Packages (YAML)

* **Component Location:** [33-9.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-9.yaml), [33-7.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-7.yaml), [33-10.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-10.yaml), [33-11.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-11.yaml), [58.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/58.yaml)
* **Status:**
  * 🟢 **REAL DATA (Modeled Regulations):**
    * **Scheme 33(9) Rules:** The conditions, equations, inputs, and tables (Table B & Table C) in `33-9.yaml` are fully modeled from the statutory Mumbai DCPR 2034 text and are evaluated dynamically.
  * 🔴 **MOCK DATA (Structural Stubs):**
    * **Multi-Scheme Stubs:** To test cross-referencing and validation across multiple regulations, `33-7.yaml`, `33-10.yaml`, `33-11.yaml`, and `58.yaml` are generated as **structural stubs** (containing minor checks, minimal inputs, and basic dependencies) rather than fully modeled statutory logic.
  * 🟡 **HARDCODED DATA:**
    * **Static Facts:** Statutory thresholds such as suburban minimum cluster area (`6000`), Island City minimum cluster area (`4000`), and FSI baseline floor (`4.00`) are stored as hardcoded facts inside the YAML files.

---

### 3. Neo4j Knowledge Graph

* **Component Location:** [generator.py](file:///f:/FullStack%20Projects/DCPR/knowledge/graph_builder/generator.py), [loader.py](file:///f:/FullStack%20Projects/DCPR/knowledge/graph_builder/loader.py)
* **Status:**
  * 🟢 **REAL DATA:**
    * **Graph Structure:** Node definitions and dependency edges (such as `DEPENDS_ON`, `USES_FORMULA`, `REFERENCES`) are constructed dynamically at runtime by scanning the YAML configuration files.
  * 🔴 **MOCK DATA (Unmodeled Target Nodes):**
    * **Stub Regulations:** To prevent broken relationship links, target regulations referenced by stubs (such as `dcpr:regulation:52` in [generator.py:L97](file:///f:/FullStack%20Projects/DCPR/knowledge/graph_builder/generator.py#L97) or unmodeled targets like Regulations 30, 31(3), and 32) are initialized as stub nodes with property `modeling_status: "STUB"`.
  * 🟡 **HARDCODED DATA:**
    * **Graph Metadata:** Schema version (`1.0`) and knowledge model version (`1.0`) are hardcoded in the generator metadata dictionary.

---

### 4. Rule Evaluation Engine

* **Component Location:** [engine.py](file:///f:/FullStack%20Projects/DCPR/knowledge/rule_engine/engine.py), [evaluator.py](file:///f:/FullStack%20Projects/DCPR/knowledge/rule_engine/evaluator.py), [table_resolver.py](file:///f:/FullStack%20Projects/DCPR/knowledge/rule_engine/table_resolver.py)
* **Status:**
  * 🟢 **REAL DATA:**
    * **Calculations:** Mathematical calculations (such as basic ratio, rehab FSI, incentive FSI, applicable FSI, maximum BUA, and balance BUA) are computed **100% dynamically** at runtime from user inputs via AST compilation.
    * **Table Resolvers:** Bins and coordinates in Table B are resolved dynamically against float values.
  * 🟡 **HARDCODED DATA (Scenario Testing):**
    * **Test Suite Scenarios:** In [run_validation.py](file:///f:/FullStack%20Projects/DCPR/knowledge/validation/run_validation.py#L33) and [run_final_demo.py](file:///f:/FullStack%20Projects/DCPR/knowledge/run_final_demo.py#L16), the user inputs for the five testing scenarios (e.g. gross area `8000`, road width `18`, rehab BUA `12000`) are hardcoded sample test parameters.

---

### 5. Calculation Validation Layer

* **Component Location:** [validation_engine.py](file:///f:/FullStack%20Projects/DCPR/knowledge/validation/validation_engine.py)
* **Status:**
  * 🟢 **REAL DATA:**
    * **Double Calculation Check:** Performs dynamic parallel recalculations, tolerance matching, division-by-zero scans, and rule completeness checks.
  * 🟡 **HARDCODED DATA:**
    * **Validation Rules:** The audit checks (such as verifying that an eligible plot's applicable FSI is `>= 4.0` in [validation_engine.py:L210](file:///f:/FullStack%20Projects/DCPR/knowledge/validation/validation_engine.py#L210)) contain hardcoded verification thresholds.

---

### 6. Guarded Reasoning Layer

* **Component Location:** [reasoning_engine.py](file:///f:/FullStack%20Projects/DCPR/knowledge/reasoning/reasoning_engine.py)
* **Status:**
  * 🟢 **REAL DATA:**
    * **Live Qwen Prompting:** When Ollama is active on port 11434, the engine sends a dynamically built prompt containing structured rules and context to generate text explanations.
  * 🟡 **HARDCODED DATA (Local Fallback Templates):**
    * **Local Compilation:** If Ollama is offline, `_generate_local_explanation` (lines 86-189) falls back to string templates containing hardcoded descriptions of statutory regulations (e.g., explaining that "Regulation 30 governs open spaces, setbacks, and margins...") to ensure continuous service uptime.

---

## Summary Summary Table

| Pipeline Component | Real Data Elements | Mock Data / Stubs | Hardcoded / Fallback Elements |
|---|---|---|---|
| **Ingestion Pipeline** | PDF file hashing; text block layout parsing (non-scanned pages). | Pre-transcribed page text and tables for scanned PDF pages 188, 189, 194, 195, and 196. | Package and instrument metadata IDs; citation targets mapping registry. |
| **Knowledge packages** | Scheme 33(9) constraints, tables, and AST equations. | Schemes 33(7), 33(10), 33(11), and 58 structural stubs. | Threshold constants (e.g., suburb cluster size = 6000) inside YAML. |
| **Knowledge Graph** | Nodes and dependency edges mapped dynamically. | Stub nodes for Regulation 52 and external target regulations. | Graph schema version and source document hashes. |
| **Rule Engine** | Relational, mathematical, and table lookup evaluations. | None. | Hardcoded sample parameters for test scenarios. |
| **Validator Layer** | Recalculation math and completeness checking. | None. | Verification thresholds (e.g., FSI >= 4.0). |
| **Reasoning Layer** | Live LLM prompts matching trace outputs. | None. | Regulatory description templates for offline fallback. |
