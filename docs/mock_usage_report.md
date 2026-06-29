# Mock Usage Report - DCPR Knowledge Engine

This report documents every location where mock text, fallback transcriptions, sample regulation text, hardcoded content, or manually injected scheme parameters are used in the Mumbai DCPR 2034 Knowledge Engine. 

---

## 1. Mock and Hardcoded Data Inventory

### 1. Ingestion Pipeline Fallback (OCR Bypass)
* **File:** [docling_adapter.py](file:///f:/FullStack%20Projects/DCPR/knowledge/pipeline/docling_adapter.py)
* **Function:** `_extract_with_pymupdf`
* **Purpose:** Provided layout-aware text and table fallback arrays for scanned pages 188, 189, 194, 195, and 196 in `MUMBAI-DCPR.pdf` because PyMuPDF (fitz) does not extract text from scanned images and Tesseract was not installed.
* **Data Injected:** Mock text strings (e.g., `"The minimum area of cluster shall be 4000 sq. m in Island City..."`), bounding boxes, and multi-dimensional string grids representing Table B and Table C.
* **Risk Level:** 🔴 **HIGH** (Prevented real, dynamic parsing of other PDF documents or revised page ranges; bound the pipeline to static inputs).
* **Current Status:** **REPLACED**. Replaced with live OCR at runtime using the Windows OCR API (`winocr`) to render pages to images, extract text lines, reconstruct layout blocks, and rebuild tables dynamically when OCR strings are detected.

---

### 2. Manual Schema Injections (Parsing Constraints)
* **File:** [parsers.py](file:///f:/FullStack%20Projects/DCPR/knowledge/pipeline/parsers.py)
* **Function:** `_parse_facts`, `_parse_inputs_outputs`, `_generate_approvals_and_coverage`
* **Purpose:** Manually maps parsed structural fields to their respective YAML output arrays to compile with the Canonical Knowledge Model (CKM) schema.
* **Data Injected:** 
  * Concept type IDs (e.g. `concept:gross-cluster-area`).
  * Inputs and output bounds definitions (e.g., `gross_cluster_area`, `applicable_fsi`).
  * Provisional approval records and coverage mappings.
* **Risk Level:** 🟡 **MEDIUM** (Hardcodes metadata mapping conventions, though necessary to bootstrap unstructured text into structured CKM entities).
* **Current Status:** **ACTIVE**. Maintained as standard semantic mapping logic.

---

### 3. Citation Registry Mappings
* **File:** [reference_resolver.py](file:///f:/FullStack%20Projects/DCPR/knowledge/pipeline/reference_resolver.py)
* **Function:** `__init__`
* **Purpose:** Resolves parsed cross-references to stable corpus IDs.
* **Data Injected:** Global corpus target maps matching text citations to target IDs:
  * `regulation:31:subregulation:3` -> `dcpr:regulation:31-3`
  * `regulation:32` -> `dcpr:regulation:32`
  * `regulation:30` -> `dcpr:regulation:30`
* **Risk Level:** 🟢 **LOW** (Standard practice for resolving statutory references; provides a deterministic lookup table for unmodeled regulations).
* **Current Status:** **ACTIVE**.

---

### 4. Graph Stubs (Multi-Scheme Validation)
* **File:** [generator.py](file:///f:/FullStack%20Projects/DCPR/knowledge/graph_builder/generator.py)
* **Function:** `generate_stubs` & `extract`
* **Purpose:** Creates mock YAML packages and target nodes for unmodeled schemes 33(7), 33(10), 33(11), 58, and Regulation 52.
* **Data Injected:** Basic metadata configurations, simple formulas (e.g. `FSI = 3.0` for 33(7)), and dependency connections (`DEPENDS_ON Regulation 52`).
* **Risk Level:** 🟢 **LOW** (Required to validate graph builder query execution and traversal paths before the entire 510-page DCPR corpus is digitized).
* **Current Status:** **ACTIVE**.

---

### 5. Local Explanation Gateway Fallbacks
* **File:** [reasoning_engine.py](file:///f:/FullStack%20Projects/DCPR/knowledge/reasoning/reasoning_engine.py)
* **Function:** `_generate_local_explanation`
* **Purpose:** Provides a resilient fallback explanation compiler when the local Ollama reasoning model (`qwen3:8b`) is offline.
* **Data Injected:** Hardcoded descriptions of statutory regulations (e.g. explaining that *"Regulation 30 governs open spaces, setbacks, and margins..."*).
* **Risk Level:** 🟢 **LOW** (Guarantees system availability and avoids runtime crashes).
* **Current Status:** **ACTIVE**.

---

## 2. Summary Table

| Component | Injected Data | Source / Mechanism | Risk Level | Mitigation Status |
|---|---|---|---|---|
| **docling_adapter.py** | Pages 188-196 Mock OCR text & tables | hardcoded dict mapping | 🔴 **HIGH** | **RESOLVED** (Replaced with live Windows OCR `winocr` and runtime block/table reconstruction). |
| **parsers.py** | CKM concept types & metadata | Manual schema mapper | 🟡 **MEDIUM** | **ACCEPTED** (Required for converting OCR lines into semantic schema structures). |
| **reference_resolver.py**| Cross-reference citations mapping | hardcoded lookup registry | 🟢 **LOW** | **ACCEPTED** (Essential for mapping plain-text citations to unique corpus URIs). |
| **generator.py** | Multi-scheme stubs (33(7), 58) | Automated stub generator | 🟢 **LOW** | **ACCEPTED** (Required to test multi-scheme dependency traversals in graph). |
| **reasoning_engine.py** | Regulation description templates | local explanation compiler | 🟢 **LOW** | **ACCEPTED** (Provides failover resiliency when LLM service is offline). |
