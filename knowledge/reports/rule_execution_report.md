# DCPR Rule Engine Execution Report

This report documents execution results for Scheme 33(9) under different development scenarios.

## Scenario 1: Standard Eligible Plot

### Inputs Provided:
```json
{
  "gross_cluster_area": 8000,
  "access_road_width": 18,
  "certified_admissible_rehabilitation_bua": 12000,
  "weighted_land_rate": 30000,
  "construction_rate": 20000,
  "fsi_base_area": 5000
}
```

### Outputs Obtained:
- **Eligibility Status:** `ELIGIBLE`
- **Calculated Applicable FSI:** `4.44`
- **Maximum Admissible BUA:** `22200.00 sq. m`

### Step-by-Step Rule Audit Trace:
| Step | Rule ID | Type | Expression / Operation | Result | Status | Message |
|---|---|---|---|---|---|---|
| 1 | `dcpr:33-9:cluster-area-eligibility` | CONDITION | `Evaluate APPLICABILITY Condition` | `True` | **PASS** | Passed APPLICABILITY Condition |
| 2 | `dcpr:33-9:road-access-eligibility` | CONDITION | `Evaluate APPLICABILITY Condition` | `True` | **PASS** | Passed APPLICABILITY Condition |
| 3 | `dcpr:33-9:basic-ratio` | FORMULA | `weighted_land_rate / construction_rate` | `1.5` | **RESOLVED** | Formula evaluated successfully. Output saved to context: basic_ratio |
| 4 | `dcpr:33-9:incentive-bua` | FORMULA | `certified_admissible_rehabilitation_bua * incentive_rate` | `10200.0` | **RESOLVED** | Formula evaluated successfully. Output saved to context: incentive_bua |
| 5 | `dcpr:33-9:rehabilitation-fsi` | FORMULA | `certified_admissible_rehabilitation_bua / fsi_base_area` | `2.4` | **RESOLVED** | Formula evaluated successfully. Output saved to context: rehabilitation_fsi |
| 6 | `dcpr:33-9:incentive-fsi` | FORMULA | `incentive_bua / fsi_base_area` | `2.04` | **RESOLVED** | Formula evaluated successfully. Output saved to context: incentive_fsi |
| 7 | `dcpr:33-9:applicable-fsi` | FORMULA | `max(4.00, rehabilitation_fsi + incentive_fsi)` | `4.4399999999999995` | **RESOLVED** | Formula evaluated successfully. Output saved to context: applicable_fsi |
| 8 | `dcpr:33-9:maximum-fsi-counted-bua` | FORMULA | `applicable_fsi * fsi_base_area` | `22199.999999999996` | **RESOLVED** | Formula evaluated successfully. Output saved to context: maximum_fsi_counted_bua |
| 9 | `dcpr:33-9:balance-bua` | FORMULA | `maximum_fsi_counted_bua - (certified_admissible_rehabilitation_bua + incentive_bua)` | `-3.637978807091713e-12` | **RESOLVED** | Formula evaluated successfully. Output saved to context: balance_bua |

---

## Scenario 2: Ineligible Plot (Narrow Access Road)

### Inputs Provided:
```json
{
  "gross_cluster_area": 8000,
  "access_road_width": 12,
  "certified_admissible_rehabilitation_bua": 12000,
  "weighted_land_rate": 30000,
  "construction_rate": 20000,
  "fsi_base_area": 5000
}
```

### Outputs Obtained:
- **Eligibility Status:** `INELIGIBLE`
- **Calculated Applicable FSI:** `0.00`
- **Maximum Admissible BUA:** `0.00 sq. m`
- **Triggered Constraints/Warnings:**
  - *"Access road width must be at least 18 metres."*

### Step-by-Step Rule Audit Trace:
| Step | Rule ID | Type | Expression / Operation | Result | Status | Message |
|---|---|---|---|---|---|---|
| 1 | `dcpr:33-9:cluster-area-eligibility` | CONDITION | `Evaluate APPLICABILITY Condition` | `True` | **PASS** | Passed APPLICABILITY Condition |
| 2 | `dcpr:33-9:road-access-eligibility` | CONDITION | `Evaluate APPLICABILITY Condition` | `False` | **FAIL** | Failed APPLICABILITY Condition: Access road width must be at least 18 metres. |

---

## Scenario 3: Exception Override (Waiver for Narrow Road)

### Inputs Provided:
```json
{
  "gross_cluster_area": 8000,
  "access_road_width": 12,
  "override_road-access-eligibility": true,
  "certified_admissible_rehabilitation_bua": 12000,
  "weighted_land_rate": 30000,
  "construction_rate": 20000,
  "fsi_base_area": 5000
}
```

### Outputs Obtained:
- **Eligibility Status:** `ELIGIBLE`
- **Calculated Applicable FSI:** `4.44`
- **Maximum Admissible BUA:** `22200.00 sq. m`
- **Applied Waivers/Exceptions:**
  - *"Override applied for dcpr:33-9:road-access-eligibility: Access road width must be at least 18 metres."*

### Step-by-Step Rule Audit Trace:
| Step | Rule ID | Type | Expression / Operation | Result | Status | Message |
|---|---|---|---|---|---|---|
| 1 | `dcpr:33-9:cluster-area-eligibility` | CONDITION | `Evaluate APPLICABILITY Condition` | `True` | **PASS** | Passed APPLICABILITY Condition |
| 2 | `dcpr:33-9:road-access-eligibility` | CONDITION | `Evaluate APPLICABILITY Condition` | `True` | **OVERRIDDEN** | Condition failed but overridden: Access road width must be at least 18 metres. |
| 3 | `dcpr:33-9:basic-ratio` | FORMULA | `weighted_land_rate / construction_rate` | `1.5` | **RESOLVED** | Formula evaluated successfully. Output saved to context: basic_ratio |
| 4 | `dcpr:33-9:incentive-bua` | FORMULA | `certified_admissible_rehabilitation_bua * incentive_rate` | `10200.0` | **RESOLVED** | Formula evaluated successfully. Output saved to context: incentive_bua |
| 5 | `dcpr:33-9:rehabilitation-fsi` | FORMULA | `certified_admissible_rehabilitation_bua / fsi_base_area` | `2.4` | **RESOLVED** | Formula evaluated successfully. Output saved to context: rehabilitation_fsi |
| 6 | `dcpr:33-9:incentive-fsi` | FORMULA | `incentive_bua / fsi_base_area` | `2.04` | **RESOLVED** | Formula evaluated successfully. Output saved to context: incentive_fsi |
| 7 | `dcpr:33-9:applicable-fsi` | FORMULA | `max(4.00, rehabilitation_fsi + incentive_fsi)` | `4.4399999999999995` | **RESOLVED** | Formula evaluated successfully. Output saved to context: applicable_fsi |
| 8 | `dcpr:33-9:maximum-fsi-counted-bua` | FORMULA | `applicable_fsi * fsi_base_area` | `22199.999999999996` | **RESOLVED** | Formula evaluated successfully. Output saved to context: maximum_fsi_counted_bua |
| 9 | `dcpr:33-9:balance-bua` | FORMULA | `maximum_fsi_counted_bua - (certified_admissible_rehabilitation_bua + incentive_bua)` | `-3.637978807091713e-12` | **RESOLVED** | Formula evaluated successfully. Output saved to context: balance_bua |

---

## Scenario 4: Validation Fail (Negative Value Check)

### Inputs Provided:
```json
{
  "gross_cluster_area": -5000,
  "access_road_width": 18,
  "certified_admissible_rehabilitation_bua": 12000,
  "weighted_land_rate": 30000,
  "construction_rate": 20000,
  "fsi_base_area": 5000
}
```

### Outputs Obtained:
- **Eligibility Status:** `INELIGIBLE`
- **Calculated Applicable FSI:** `0.00`
- **Maximum Admissible BUA:** `0.00 sq. m`
- **Triggered Constraints/Warnings:**
  - *"Input parameter 'gross_cluster_area' cannot be negative (got -5000)."*
  - *"Gross cluster area must be positive."*

### Step-by-Step Rule Audit Trace:
| Step | Rule ID | Type | Expression / Operation | Result | Status | Message |
|---|---|---|---|---|---|---|
| 1 | `input:gross_cluster_area` | INPUT_VALIDATION | `Validate input:gross_cluster_area` | `False` | **NEGATIVE_VALUE** | Input parameter 'gross_cluster_area' cannot be negative (got -5000). |
| 2 | `input:gross_cluster_area` | INPUT_VALIDATION | `Validate input:gross_cluster_area` | `False` | **CONSTRAINT_VIOLATION** | Gross cluster area must be positive. |

---

## Scenario 5: Validation Fail (Missing Required Input)

### Inputs Provided:
```json
{
  "access_road_width": 18,
  "certified_admissible_rehabilitation_bua": 12000,
  "weighted_land_rate": 30000,
  "construction_rate": 20000,
  "fsi_base_area": 5000
}
```

### Outputs Obtained:
- **Eligibility Status:** `INELIGIBLE`
- **Calculated Applicable FSI:** `0.00`
- **Maximum Admissible BUA:** `0.00 sq. m`
- **Triggered Constraints/Warnings:**
  - *"Required input parameter 'gross_cluster_area' is missing."*

### Step-by-Step Rule Audit Trace:
| Step | Rule ID | Type | Expression / Operation | Result | Status | Message |
|---|---|---|---|---|---|---|
| 1 | `input:gross_cluster_area` | INPUT_VALIDATION | `Validate input:gross_cluster_area` | `False` | **MISSING_INPUT** | Required input parameter 'gross_cluster_area' is missing. |

---

