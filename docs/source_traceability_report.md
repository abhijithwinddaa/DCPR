# Source Traceability Report - Scheme 33(9)

This report details the end-to-end traceability for every static fact, parameter, and threshold modeled under **Scheme 33(9) (Cluster Development Scheme)** in the Mumbai DCPR 2034 Knowledge Engine. It maps each fact from its physical location in the source PDF (`MUMBAI-DCPR.pdf`), to its Canonical Knowledge Model (CKM) representation, and finally to its application within the deterministic evaluation logic.

---

## Fact-by-Fact Source Mapping

### 1. Base FSI Floor
* **Fact ID:** `dcpr:33-9:base-fsi-floor`
* **Source PDF Page:** Page 195 (0-indexed Page Index 194)
* **Source Coordinates (BBox):** Printed Page 178, approximate coordinates `[50, 100, 550, 250]` (Clause 6.a)
* **Source Text:** 
  > *"The total permissible FSI for an CDS shall be 4.00 on gross plot area..."*
* **YAML Package Location:** [33-9.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-9.yaml#L61-L78)
* **Rule Engine Usage:** Evaluated in formula `dcpr:33-9:applicable-fsi` (calculates `max(base-fsi-floor, rehab_fsi + incentive_fsi)` to enforce the minimum baseline FSI of `4.00` for eligible cluster plots).

---

### 2. Island City Minimum Cluster Area
* **Fact ID:** `dcpr:33-9:island-city-minimum-cluster-area`
* **Source PDF Page:** Page 189 (0-indexed Page Index 188)
* **Source Coordinates (BBox):** Printed Page 172, approximate coordinates `[50, 220, 550, 300]` (Clause 1.1)
* **Source Text:** 
  > *"...minimum area of 4000 sq. m in the Island City of Mumbai..."*
* **YAML Package Location:** [33-9.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-9.yaml#L79-L98)
* **Rule Engine Usage:** Checked during pre-flight eligibility conditions when evaluating proposals marked with regional tenure as `ISLAND_CITY`.

---

### 3. Suburbs Minimum Cluster Area
* **Fact ID:** `dcpr:33-9:suburbs-minimum-cluster-area`
* **Source PDF Page:** Page 189 (0-indexed Page Index 188)
* **Source Coordinates (BBox):** Printed Page 172, approximate coordinates `[50, 220, 550, 300]` (Clause 1.1)
* **Source Text:** 
  > *"...and 6000 sq. m in the Mumbai Suburbs & Extended Suburbs..."*
* **YAML Package Location:** [33-9.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-9.yaml#L99-L118)
* **Rule Engine Usage:** Evaluated inside condition `dcpr:33-9:cluster-area-eligibility` (`gross_cluster_area >= suburbs-minimum-cluster-area`) for suburban development proposals.

---

### 4. Ordinary Access Road Width
* **Fact ID:** `dcpr:33-9:ordinary-access-road-width`
* **Source PDF Page:** Page 189 (0-indexed Page Index 188)
* **Source Coordinates (BBox):** Printed Page 172, approximate coordinates `[50, 220, 550, 300]` (Clause 1.1)
* **Source Text:** 
  > *"...accessible by an existing or proposed D.P. road which is at least 18m wide..."*
* **YAML Package Location:** [33-9.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-9.yaml#L119-L138)
* **Rule Engine Usage:** Evaluated inside condition `dcpr:33-9:road-access-eligibility` (`access_road_width >= ordinary-access-road-width` to check road width clearance).

---

### 5. Exception Override Access Road Width (Dead-End Waiver)
* **Fact ID:** `dcpr:33-9:waiver-access-road-width`
* **Source PDF Page:** Page 189 (0-indexed Page Index 188)
* **Source Coordinates (BBox):** Printed Page 172, approximate coordinates `[50, 300, 550, 350]` (Clause 1.1 Proviso)
* **Source Text:** 
  > *"...allow CDS on a plot having access from existing minimum 12m. wide dead end road originating from 18 m. wide public road."*
* **YAML Package Location:** [33-9.yaml](file:///f:/FullStack%20Projects/DCPR/knowledge/schemes/33-9.yaml) (defined under conditional bypass triggers).
* **Rule Engine Usage:** Applied as an exception waiver parameter `override_road-access-eligibility` to permit projects abutting narrow 12m dead-end roads to pass eligibility checks, provided the parent road is at least 18m wide.

---

## Traceability Data Flow Summary Table

| Fact ID | Source PDF Page | Bounding Box | Statutory Text Source | YAML Node Path | Rule Engine Logic / Formula |
|---|---|---|---|---|---|
| `base-fsi-floor` | Page 195 | `[50, 100, 550, 250]` | *"FSI ... shall be 4.00"* | `/facts/dcpr:33-9:base-fsi-floor` | `max(4.00, rehab_fsi + incentive_fsi)` |
| `island-city-min-area` | Page 189 | `[50, 220, 550, 300]` | *"minimum area of 4000 sq. m"* | `/facts/dcpr:33-9:island-city-minimum-cluster-area` | Eligibility area check for Island City plots. |
| `suburbs-min-area` | Page 189 | `[50, 220, 550, 300]` | *"and 6000 sq. m in the Mumbai Suburbs"* | `/facts/dcpr:33-9:suburbs-minimum-cluster-area` | `gross_cluster_area >= 6000` |
| `ordinary-road-width` | Page 189 | `[50, 220, 550, 300]` | *"accessible by ... road ... at least 18m wide"* | `/facts/dcpr:33-9:ordinary-access-road-width` | `access_road_width >= 18` |
| `waiver-road-width` | Page 189 | `[50, 300, 550, 350]` | *"access from ... dead end road ... minimum 12m"* | `/conditions/dcpr:33-9:road-access-eligibility` | Overrides 18m block constraint if waiver dead-end parameter is set. |
