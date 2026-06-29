# DCPR Rule Engine Boundary Validation Report

This report details input validations, constraint triggers, and error-handling verification.

## 1. Input Constraints Verification (Scenario 4 & 5)

### Scenario 4: Validation Fail (Negative Value Check)
- **Expected Result:** Validation Error / Ineligible
- **Actual Result:** `INELIGIBLE`
- **Reported Validation Messages:**
  - `[VALIDATION FAIL]` Input parameter 'gross_cluster_area' cannot be negative (got -5000).
  - `[VALIDATION FAIL]` Gross cluster area must be positive.

### Scenario 5: Validation Fail (Missing Required Input)
- **Expected Result:** Validation Error / Ineligible
- **Actual Result:** `INELIGIBLE`
- **Reported Validation Messages:**
  - `[VALIDATION FAIL]` Required input parameter 'gross_cluster_area' is missing.

## 2. Table Boundary Edge Cases Checked
- **Lower & Upper Bound Mapping:** Table resolver checks basic ratios <= 2.0, between 2.0 and 4.0, between 4.0 and 6.0, and > 6.0.
- **Out-of-bound errors:** The engine successfully throws a clear error if inputs do not fall inside any mapped range.

## 3. Exception Bypass Verification (Scenario 3)
- **Scenario 3 Status:** Eligibility overridden via `override_road-access-eligibility` waiver flag.
- **Final Eligibility:** `ELIGIBLE` (Calculated FSI: `4.44`)
- **Trace Details:** Waiver mapped successfully to the evaluation state.
