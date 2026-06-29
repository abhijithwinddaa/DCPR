import time
from knowledge.rule_engine.evaluator import ASTEvaluator
from knowledge.rule_engine.table_resolver import TableResolver
from knowledge.rule_engine.validator import InputValidator

class RuleEngine:
    """
    RuleEngine executes the deterministic logic for a scheme:
    validating inputs, evaluating eligibility, executing formulas,
    performing lookups, and generating the rule trace.
    """
    def __init__(self, contract_data):
        self.contract_data = contract_data
        self.table_resolver = TableResolver()
        self.evaluator = ASTEvaluator(self.table_resolver)
        self.validator = InputValidator()

    def _get_scheme_contract(self, scheme_id):
        """Finds the contract sub-block for a given scheme ID or citation."""
        if scheme_id in self.contract_data:
            return self.contract_data[scheme_id]
            
        # Try citation or normalized citation matching
        for k, contract in self.contract_data.items():
            if contract.get("scheme_id") == scheme_id or contract.get("scheme_uri") == scheme_id:
                return contract
            if scheme_id.replace("-", "(").replace("_", "(") in k:
                return contract
                
        raise KeyError(f"Scheme contract not found for ID: {scheme_id}")

    def evaluate(self, scheme_id, user_inputs):
        """
        Executes the rule engine on user_inputs for the specified scheme.
        Returns a dict conforming to the Phase 4 Output requirements.
        """
        start_time = time.time()
        rule_trace = []
        context = {}
        outputs = {}
        eligibility = "UNKNOWN"
        failed_constraints = []
        active_exceptions = []

        try:
            # 1. Fetch contract
            contract = self._get_scheme_contract(scheme_id)
        except KeyError as e:
            return {
                "applicable_fsi": 0.0,
                "maximum_bua": 0.0,
                "eligibility": "ERROR",
                "constraints": [],
                "exceptions": [],
                "rule_trace": [{
                    "step": 1,
                    "rule_id": "system:init",
                    "type": "SYSTEM",
                    "result": str(e),
                    "status": "ERROR",
                    "message": "Scheme initialization failed."
                }]
            }

        # Setup TableResolver with this scheme's tables
        self.table_resolver.set_tables(contract.get("tables", []))

        # 2. Populate initial context from user inputs
        for k, v in user_inputs.items():
            clean_k = k[6:] if k.startswith("input:") else k
            context[k] = v
            context[clean_k] = v

        # 3. Populate static facts in context
        for fact in contract.get("facts", []):
            fid = fact.get("id")
            val = fact.get("value")
            val_type = fact.get("value_type", "")
            
            # Cast values appropriately
            if isinstance(val, dict) and "value" in val:
                val = val["value"]
            typed_val = val
            if val_type == "DECIMAL" or val_type == "QUANTITY":
                try:
                    typed_val = float(val)
                except (ValueError, TypeError):
                    pass
            elif val_type == "INTEGER":
                try:
                    typed_val = int(val)
                except (ValueError, TypeError):
                    pass
            elif val_type == "BOOLEAN":
                typed_val = str(val).lower() in ("true", "1", "yes")

            context[fid] = typed_val
            # Also store by simple name if possible
            fname = fact.get("name").replace(" ", "_").lower()
            context[fname] = typed_val

        # 4. Input Validation Step
        errors = self.validator.validate(contract.get("inputs", []), user_inputs)
        if errors:
            for idx, err in enumerate(errors):
                rule_trace.append({
                    "step": idx + 1,
                    "rule_id": err["id"],
                    "type": "INPUT_VALIDATION",
                    "expression": f"Validate {err['id']}",
                    "result": False,
                    "status": err["type"],
                    "message": err["message"]
                })
            return {
                "applicable_fsi": 0.0,
                "maximum_bua": 0.0,
                "eligibility": "INELIGIBLE",
                "constraints": [err["message"] for err in errors],
                "exceptions": [],
                "rule_trace": rule_trace
            }

        # 5. Pre-flight Eligibility & Applicability Phase
        step_counter = len(rule_trace) + 1
        eligibility = "ELIGIBLE"
        
        for cond in contract.get("conditions", []):
            cond_id = cond.get("id")
            expr = cond.get("expression")
            msg = cond.get("message", f"Eligibility check failed for {cond_id}")
            phase = cond.get("phase", "APPLICABILITY")
            
            # Run condition
            passed = False
            eval_error = None
            if expr:
                try:
                    passed = self.evaluator.evaluate(expr, context)
                except Exception as e:
                    eval_error = str(e)
                    passed = False

            if not passed:
                # Check for Exception Override
                # If user passed a bypass flag or matching override parameter, let it pass
                override_key = f"override_{cond_id.split(':')[-1]}"
                user_override = user_inputs.get(override_key, False) or user_inputs.get("bypass_all_eligibility", False)
                
                if user_override:
                    rule_trace.append({
                        "step": step_counter,
                        "rule_id": cond_id,
                        "type": "CONDITION",
                        "expression": f"Evaluate {phase} Condition",
                        "result": True,
                        "status": "OVERRIDDEN",
                        "message": f"Condition failed but overridden: {msg}"
                    })
                    active_exceptions.append(f"Override applied for {cond_id}: {msg}")
                else:
                    rule_trace.append({
                        "step": step_counter,
                        "rule_id": cond_id,
                        "type": "CONDITION",
                        "expression": f"Evaluate {phase} Condition",
                        "result": False,
                        "status": "FAIL",
                        "message": f"Failed {phase} Condition: {msg}" + (f" (Error: {eval_error})" if eval_error else "")
                    })
                    eligibility = "INELIGIBLE"
                    failed_constraints.append(msg)
            else:
                rule_trace.append({
                    "step": step_counter,
                    "rule_id": cond_id,
                    "type": "CONDITION",
                    "expression": f"Evaluate {phase} Condition",
                    "result": True,
                    "status": "PASS",
                    "message": f"Passed {phase} Condition"
                })
            step_counter += 1

        # Halt if ineligible
        if eligibility == "INELIGIBLE":
            return {
                "applicable_fsi": 0.0,
                "maximum_bua": 0.0,
                "eligibility": "INELIGIBLE",
                "constraints": failed_constraints,
                "exceptions": active_exceptions,
                "rule_trace": rule_trace
            }

        # 6. Evaluation Phase (Topological formula evaluation)
        # Build DAG representation to evaluate formulas in order
        formulas = contract.get("formulae", [])
        sorted_formulas = self._topological_sort_formulas(formulas)

        for formula in sorted_formulas:
            fid = formula["id"]
            expr = formula.get("expression")
            raw_expr = formula.get("raw_expression", "")
            out_var = formula.get("output_id")

            try:
                res_val = self.evaluator.evaluate(expr, context)
                # Store resolved value in context
                context[fid] = res_val
                if out_var:
                    context[out_var] = res_val
                
                rule_trace.append({
                    "step": step_counter,
                    "rule_id": fid,
                    "type": "FORMULA",
                    "expression": raw_expr,
                    "result": res_val,
                    "status": "RESOLVED",
                    "message": f"Formula evaluated successfully. Output saved to context: {out_var}"
                })
            except Exception as e:
                rule_trace.append({
                    "step": step_counter,
                    "rule_id": fid,
                    "type": "FORMULA",
                    "expression": raw_expr,
                    "result": None,
                    "status": "ERROR",
                    "message": f"Failed to evaluate formula: {e}"
                })
                return {
                    "applicable_fsi": 0.0,
                    "maximum_bua": 0.0,
                    "eligibility": "ERROR",
                    "constraints": failed_constraints + [f"Formula evaluation error: {fid}"],
                    "exceptions": active_exceptions,
                    "rule_trace": rule_trace
                }
            step_counter += 1

        # 7. Bind Outputs
        # Extract output parameters from context
        # Standard variables requested: applicable_fsi, maximum_bua
        applicable_fsi = context.get("applicable_fsi", 0.0)
        maximum_bua = context.get("maximum_fsi_counted_bua", context.get("maximum_bua", 0.0))

        # Check output constraints
        for out in contract.get("outputs", []):
            out_id = out.get("id")
            name = out.get("name")
            val_constraints = out.get("validation_constraints", [])
            
            for vc in val_constraints:
                expr = vc.get("expression")
                msg = vc.get("message", f"Output validation constraint failed for {name}.")
                if expr:
                    try:
                        res = self.evaluator.evaluate(expr, context)
                        if not res:
                            failed_constraints.append(msg)
                            rule_trace.append({
                                "step": step_counter,
                                "rule_id": out_id,
                                "type": "OUTPUT_VALIDATION",
                                "expression": f"Validate Output {out_id}",
                                "result": False,
                                "status": "FAIL",
                                "message": msg
                            })
                            step_counter += 1
                    except Exception as e:
                        print(f"Warning: Failed to evaluate output validation constraint: {e}")

        return {
            "applicable_fsi": applicable_fsi,
            "maximum_bua": maximum_bua,
            "eligibility": eligibility,
            "constraints": failed_constraints,
            "exceptions": active_exceptions,
            "rule_trace": rule_trace
        }

    def _topological_sort_formulas(self, formulas):
        """
        Sorts the formulas topologically based on their DERIVED dependencies.
        Returns a sorted list of formula dicts.
        """
        # Map output variable names to formula objects
        outputs_map = {}
        for f in formulas:
            out_id = f.get("output_id")
            fid = f.get("id")
            if out_id:
                outputs_map[out_id] = f
            outputs_map[fid] = f

        # Build dependency adjacency list
        # formula -> list of formulas it depends on
        adj = {f["id"]: [] for f in formulas}
        
        for f in formulas:
            fid = f["id"]
            bindings = f.get("variable_bindings", [])
            for bind in bindings:
                if bind.get("source_kind") == "DERIVED":
                    dep_id = bind.get("source_id")
                    # If this dependency is produced by one of our formulas
                    if dep_id in outputs_map:
                        producer = outputs_map[dep_id]
                        adj[fid].append(producer["id"])

        # Run topological sort DFS
        visited = {} # id -> state (0 = unvisited, 1 = visiting, 2 = visited)
        order = []

        def dfs(node_id):
            visited[node_id] = 1 # visiting
            for neighbor in adj.get(node_id, []):
                state = visited.get(neighbor, 0)
                if state == 1:
                    # Circular dependency detected!
                    raise ValueError(f"Circular dependency detected in formulas at node: {node_id}")
                elif state == 0:
                    dfs(neighbor)
            visited[node_id] = 2 # visited
            # Find the formula object
            for f in formulas:
                if f["id"] == node_id:
                    order.append(f)
                    break

        for f in formulas:
            fid = f["id"]
            if visited.get(fid, 0) == 0:
                dfs(fid)

        return order
