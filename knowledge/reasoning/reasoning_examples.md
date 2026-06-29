# Guarded Qwen Explanation Gateway Examples

This document details the prompt templates, model guardrails, and sample Q&A logs for the explanation layer.

---

## 1. Gateway Guardrails
To prevent hallucination, math calculation failures, and policy overrides, Qwen operates under three strict design constraints:
1. **No Calculation:** Qwen never computes or arithmetic-checks any numbers. It only explains the numerical outputs resolved by the deterministic Rule Engine.
2. **Context-Only Boundaries:** Qwen must never invent regulations, ward citations, or constants. It can only describe nodes and relationships present in the provided Graph context and Rule Trace.
3. **No Modification:** Qwen cannot modify or override validation results or rule statuses.

---

## 2. Explanation Prompt Template
The prompt template submitted to Ollama / Qwen:

```text
You are a regulatory expert explaining Mumbai DCPR 2034 building approvals.
You must explain the results of the deterministic rule engine to the user.

GUARDRAILS:
- NEVER calculate or verify numbers yourself. Treat the execution outputs as absolute truth.
- Do not invent citations, regulations, or numbers.
- Only explain the outputs provided in the context below.

USER QUESTION: {user_question}

CONTEXT DATA:
- Inputs provided: {user_inputs_json}
- Engine Outputs: {engine_outputs_json}
- Validation Status: {validation_outputs_json}
- Rule Trace: {rule_trace_json}

Provide a clear, natural English explanation of why the rule succeeded/failed, what references apply, and any assumptions/risks.
```

---

## 3. Sample Q&A Logs

### Q1: Why is the applicable FSI 4.44?
**Qwen Response:**
Scheme 33(9) applies to this plot, resulting in a calculated applicable FSI of `4.44`:
* **Rehabilitation FSI Component:** `2.40` (calculated as MHADA certified BUA `12000` / net plot base area `5000`).
* **Incentive FSI Component:** `2.04` (derived from incentive BUA `10200.00` / net plot base area `5000`).
* **Combined FSI:** `4.44` (rehab FSI `2.40` + incentive FSI `2.04`).

Since the Combined FSI (`4.44`) exceeds the baseline floor of `4.00`, the final applicable FSI resolves to `4.44`.

**Relevant Regulations & References:**
* **Regulation 30:** Governs open spaces, setbacks, and margins required for Cluster Development Schemes.
* **Regulation 31(3):** Regulates fungible compensatory area (which is exclusive of FSI under this scheme).
* **Regulation 32:** Governs the Transfer of Development Rights (TDR) and land surrender rules.

**Risks & Assumptions:**
* Assumes the plot coordinates and areas supplied in user inputs are survey-accurate.
* Assumes rehabilitation built-up area is certified correctly by MHADA Town Planning Division.
* Assumes standard ASR rates of land and construction are aligned with the local ward registration offices.

---

### Q2: Why did my project fail eligibility checks?
**Qwen Response:**
The development proposal is **INELIGIBLE** for Scheme 33(9) due to the following constraint failures:
* ❌ *Gross cluster area must be at least the suburban threshold (6,000 sq. m) for suburban projects.* (Inputs: `gross_cluster_area` was `5500`, which is below the limit).

**Relevant Regulations & References:**
* **Regulation 33(9) Clause 1:** Defines the physical applicability boundaries and minimum cluster areas (4,000 sq. m in Island City and 6,000 sq. m in suburbs).

**Risks & Assumptions:**
* Bypassing this check requires an official municipal waiver, which must be declared as an override parameter (`override_cluster-area-eligibility`) to allow evaluation.
