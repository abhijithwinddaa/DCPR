# DCPR Knowledge Graph Query Report

This report answers semantic verification queries for the loaded DCPR Knowledge Graph.

## 1. What regulations does Scheme 33(9) reference?
- `No direct regulation matches in graph`

## 2. What conditions apply to Scheme 33(9)?
- `dcpr:33-9:cluster-area-eligibility` (Message: *"Gross cluster area must be at least the suburban threshold (6,000 sq. m) for suburban projects."*)
- `dcpr:33-9:road-access-eligibility` (Message: *"Access road width must be at least 18 metres."*)

## 3. What formulae are used in Scheme 33(9)?
- `dcpr:33-9:basic-ratio`
- `dcpr:33-9:incentive-bua`
- `dcpr:33-9:rehabilitation-fsi`
- `dcpr:33-9:incentive-fsi`
- `dcpr:33-9:applicable-fsi`
- `dcpr:33-9:maximum-fsi-counted-bua`
- `dcpr:33-9:balance-bua`

## 4. What tables are used in Scheme 33(9)?
- `dcpr:33-9:table-b:incentive-rate`

## 5. What definitions are required?
- *No definitions registered directly under Scheme 33(9) node.*

## 6. Show all transitive dependencies of Scheme 33(9)
Below is the recursive dependency path resolved by the graph builder:
- `dcpr:33-9:cluster-area-eligibility` [Condition] (via `HAS_CONDITION` relationship)
- `input:gross_cluster_area` [InputParameter] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:suburbs-minimum-cluster-area` [Fact] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:road-access-eligibility` [Condition] (via `HAS_CONDITION` relationship)
- `input:access_road_width` [InputParameter] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:ordinary-access-road-width` [Fact] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:basic-ratio` [Formula] (via `USES_FORMULA` relationship)
- `input:weighted_land_rate` [InputParameter] (via `DEPENDS_ON` relationship)
- `input:construction_rate` [InputParameter] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:incentive-bua` [Formula] (via `USES_FORMULA` relationship)
- `input:certified_admissible_rehabilitation_bua` [InputParameter] (via `DEPENDS_ON` relationship)
- `basic_ratio` [Node] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:table-b:incentive-rate` [Table] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:rehabilitation-fsi` [Formula] (via `USES_FORMULA` relationship)
- `input:fsi_base_area` [InputParameter] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:incentive-fsi` [Formula] (via `USES_FORMULA` relationship)
- `incentive_bua` [Node] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:applicable-fsi` [Formula] (via `USES_FORMULA` relationship)
- `rehabilitation_fsi` [Node] (via `DEPENDS_ON` relationship)
- `incentive_fsi` [Node] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:base-fsi-floor` [Fact] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:maximum-fsi-counted-bua` [Formula] (via `USES_FORMULA` relationship)
- `applicable_fsi` [Node] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:balance-bua` [Formula] (via `USES_FORMULA` relationship)
- `maximum_fsi_counted_bua` [Node] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:table-b:incentive-rate` [Table] (via `HAS_TABLE` relationship)
- `input:gross_cluster_area` [InputParameter] (via `HAS_INPUT` relationship)
- `input:access_road_width` [InputParameter] (via `HAS_INPUT` relationship)
- `input:certified_admissible_rehabilitation_bua` [InputParameter] (via `HAS_INPUT` relationship)
- `input:weighted_land_rate` [InputParameter] (via `HAS_INPUT` relationship)
- `input:construction_rate` [InputParameter] (via `HAS_INPUT` relationship)
- `input:fsi_base_area` [InputParameter] (via `HAS_INPUT` relationship)
- `output:applicable_fsi` [OutputParameter] (via `HAS_OUTPUT` relationship)
- `dcpr:33-9:applicable-fsi` [Formula] (via `DEPENDS_ON` relationship)
- `output:maximum_fsi_counted_bua` [OutputParameter] (via `HAS_OUTPUT` relationship)
- `dcpr:33-9:maximum-fsi-counted-bua` [Formula] (via `DEPENDS_ON` relationship)
- `dcpr:33-9:base-fsi-floor` [Fact] (via `RELATED_TO` relationship)
- `dcpr:33-9:island-city-minimum-cluster-area` [Fact] (via `RELATED_TO` relationship)
- `dcpr:33-9:suburbs-minimum-cluster-area` [Fact] (via `RELATED_TO` relationship)
- `dcpr:33-9:ordinary-access-road-width` [Fact] (via `RELATED_TO` relationship)

## 7. Show all entities impacted if Regulation 52 changes
- `ref:33-10-dep-52` [Reference] (Relationship: `REFERENCES`)
- `dcpr:scheme:33-10` [Scheme] (Relationship: `TRANSITIVE_IMPACT`)
- `ref:33-7-dep-52` [Reference] (Relationship: `REFERENCES`)
- `dcpr:scheme:33-7` [Scheme] (Relationship: `TRANSITIVE_IMPACT`)

## 8. Complete Transitive Dependency Tree (Scheme 33(9))
```text
- dcpr:scheme:33-9 [Scheme] (Reconstruction or redevelopment of Cluster(s) of Buildings under Cluster Development Scheme)
  └─[:HAS_CONDITION]─→
    - dcpr:33-9:cluster-area-eligibility [Condition]
      └─[:DEPENDS_ON]─→
        - input:gross_cluster_area [InputParameter]
      └─[:DEPENDS_ON]─→
        - dcpr:33-9:suburbs-minimum-cluster-area [Fact]
  └─[:HAS_CONDITION]─→
    - dcpr:33-9:road-access-eligibility [Condition]
      └─[:DEPENDS_ON]─→
        - input:access_road_width [InputParameter]
      └─[:DEPENDS_ON]─→
        - dcpr:33-9:ordinary-access-road-width [Fact]
  └─[:USES_FORMULA]─→
    - dcpr:33-9:basic-ratio [Formula]
      └─[:DEPENDS_ON]─→
        - input:weighted_land_rate [InputParameter]
      └─[:DEPENDS_ON]─→
        - input:construction_rate [InputParameter]
  └─[:USES_FORMULA]─→
    - dcpr:33-9:incentive-bua [Formula]
      └─[:DEPENDS_ON]─→
        - input:certified_admissible_rehabilitation_bua [InputParameter]
      └─[:DEPENDS_ON]─→
        - basic_ratio [Node]
      └─[:DEPENDS_ON]─→
        - input:gross_cluster_area [InputParameter]
      └─[:DEPENDS_ON]─→
        - dcpr:33-9:table-b:incentive-rate [Table] (Table B: Incentive FSI Rate Table)
  └─[:USES_FORMULA]─→
    - dcpr:33-9:rehabilitation-fsi [Formula]
      └─[:DEPENDS_ON]─→
        - input:certified_admissible_rehabilitation_bua [InputParameter]
      └─[:DEPENDS_ON]─→
        - input:fsi_base_area [InputParameter]
  └─[:USES_FORMULA]─→
    - dcpr:33-9:incentive-fsi [Formula]
      └─[:DEPENDS_ON]─→
        - incentive_bua [Node]
      └─[:DEPENDS_ON]─→
        - input:fsi_base_area [InputParameter]
  └─[:USES_FORMULA]─→
    - dcpr:33-9:applicable-fsi [Formula]
      └─[:DEPENDS_ON]─→
        - rehabilitation_fsi [Node]
      └─[:DEPENDS_ON]─→
        - incentive_fsi [Node]
      └─[:DEPENDS_ON]─→
        - dcpr:33-9:base-fsi-floor [Fact]
  └─[:USES_FORMULA]─→
    - dcpr:33-9:maximum-fsi-counted-bua [Formula]
      └─[:DEPENDS_ON]─→
        - applicable_fsi [Node]
      └─[:DEPENDS_ON]─→
        - input:fsi_base_area [InputParameter]
  └─[:USES_FORMULA]─→
    - dcpr:33-9:balance-bua [Formula]
      └─[:DEPENDS_ON]─→
        - maximum_fsi_counted_bua [Node]
      └─[:DEPENDS_ON]─→
        - input:certified_admissible_rehabilitation_bua [InputParameter]
      └─[:DEPENDS_ON]─→
        - incentive_bua [Node]
  └─[:HAS_TABLE]─→
    - dcpr:33-9:table-b:incentive-rate [Table] (Table B: Incentive FSI Rate Table)
  └─[:HAS_INPUT]─→
    - input:gross_cluster_area [InputParameter]
  └─[:HAS_INPUT]─→
    - input:access_road_width [InputParameter]
  └─[:HAS_INPUT]─→
    - input:certified_admissible_rehabilitation_bua [InputParameter]
  └─[:HAS_INPUT]─→
    - input:weighted_land_rate [InputParameter]
  └─[:HAS_INPUT]─→
    - input:construction_rate [InputParameter]
  └─[:HAS_INPUT]─→
    - input:fsi_base_area [InputParameter]
  └─[:HAS_OUTPUT]─→
    - output:applicable_fsi [OutputParameter]
      └─[:DEPENDS_ON]─→
        - dcpr:33-9:applicable-fsi [Formula]
          └─[:DEPENDS_ON]─→
            - rehabilitation_fsi [Node]
          └─[:DEPENDS_ON]─→
            - incentive_fsi [Node]
          └─[:DEPENDS_ON]─→
            - dcpr:33-9:base-fsi-floor [Fact]
  └─[:HAS_OUTPUT]─→
    - output:maximum_fsi_counted_bua [OutputParameter]
      └─[:DEPENDS_ON]─→
        - dcpr:33-9:maximum-fsi-counted-bua [Formula]
          └─[:DEPENDS_ON]─→
            - applicable_fsi [Node]
          └─[:DEPENDS_ON]─→
            - input:fsi_base_area [InputParameter]
  └─[:RELATED_TO]─→
    - dcpr:33-9:base-fsi-floor [Fact]
  └─[:RELATED_TO]─→
    - dcpr:33-9:island-city-minimum-cluster-area [Fact]
  └─[:RELATED_TO]─→
    - dcpr:33-9:suburbs-minimum-cluster-area [Fact]
  └─[:RELATED_TO]─→
    - dcpr:33-9:ordinary-access-road-width [Fact]
```
