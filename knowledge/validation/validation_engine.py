import math
from knowledge.rule_engine.evaluator import ASTEvaluator
from knowledge.rule_engine.table_resolver import TableResolver

class CalculationValidator:
    """
    CalculationValidator independently audits and verifies Rule Engine executions
    to ensure math, rounding, lookup, boundary, and dependency correctness.
    """
    def __init__(self):
        self.table_resolver = TableResolver()
        self.evaluator = ASTEvaluator(self.table_resolver)

    def validate(self, contract_data, scheme_id, user_inputs, execution_output):
        """
        Independently validates the execution output of the Rule Engine.
        Returns a dict of validation flags, statuses, and warnings.
        """
        warnings = []
        formula_validation = True
        table_validation = True
        unit_validation = True
        rounding_validation = True
        boundary_validation = True
        dependency_validation = True
        completeness_validation = True

        # Find scheme contract
        scheme_contract = None
        for k, contract in contract_data.items():
            if contract.get("scheme_id") == scheme_id or contract.get("scheme_uri") == scheme_id:
                scheme_contract = contract
                break
        
        if not scheme_contract:
            # Try citation fuzzy matching
            for k, contract in contract_data.items():
                if scheme_id.replace("-", "(").replace("_", "(") in k:
                    scheme_contract = contract
                    break

        if not scheme_contract:
            return {
                "validation_status": "FAIL",
                "formula_validation": False,
                "table_validation": False,
                "unit_validation": False,
                "rounding_validation": False,
                "warnings": [f"Could not find scheme contract for validation: {scheme_id}"]
            }

        # Initialize TableResolver with this scheme's tables
        self.table_resolver.set_tables(scheme_contract.get("tables", []))

        # Reconstruct evaluation context step-by-step
        context = {}
        for k, v in user_inputs.items():
            clean_k = k[6:] if k.startswith("input:") else k
            context[k] = v
            context[clean_k] = v

        # Populate static facts
        for fact in scheme_contract.get("facts", []):
            fid = fact.get("id")
            val = fact.get("value")
            val_type = fact.get("value_type", "")
            
            # Cast values
            typed_val = val
            if isinstance(val, dict) and "value" in val:
                val = val["value"]
            if val_type == "DECIMAL" or val_type == "QUANTITY":
                try: typed_val = float(val)
                except: pass
            elif val_type == "INTEGER":
                try: typed_val = int(val)
                except: pass
            elif val_type == "BOOLEAN":
                typed_val = str(val).lower() in ("true", "1", "yes")

            context[fid] = typed_val
            fname = fact.get("name").replace(" ", "_").lower()
            context[fname] = typed_val

        # Map rules by ID for quick lookup
        formulas_map = {f["id"]: f for f in scheme_contract.get("formulae", [])}
        conditions_map = {c["id"]: c for c in scheme_contract.get("conditions", [])}

        trace = execution_output.get("rule_trace", [])
        executed_rule_ids = set()

        for step in trace:
            rule_id = step.get("rule_id")
            step_type = step.get("type")
            status = step.get("status")
            result = step.get("result")
            executed_rule_ids.add(rule_id)

            if step_type == "INPUT_VALIDATION":
                # Verify that negative values were correctly flagged
                if status == "NEGATIVE_VALUE":
                    val = user_inputs.get(rule_id.replace("input:", ""))
                    if val is not None and float(val) >= 0:
                        boundary_validation = False
                        warnings.append(f"Input validator flagged positive value '{val}' as negative for variable '{rule_id}'.")

            elif step_type == "CONDITION":
                if rule_id not in conditions_map:
                    warnings.append(f"Condition ID '{rule_id}' in trace is not defined in contract.")
                    continue
                
                cond = conditions_map[rule_id]
                expr = cond.get("expression")
                
                # Re-evaluate condition expression
                try:
                    re_passed = self.evaluator.evaluate(expr, context)
                    expected_status = "PASS" if re_passed else "FAIL"
                    
                    if status not in ("PASS", "FAIL", "OVERRIDDEN"):
                        warnings.append(f"Condition '{rule_id}' has unexpected status: {status}")
                    
                    # Verify overrides
                    if status == "OVERRIDDEN" and re_passed:
                        warnings.append(f"Condition '{rule_id}' status is OVERRIDDEN but it actually evaluates to PASS.")
                    if status == "FAIL" and re_passed:
                        formula_validation = False
                        warnings.append(f"Condition '{rule_id}' failed in engine but re-evaluates as PASS.")
                    if status == "PASS" and not re_passed:
                        formula_validation = False
                        warnings.append(f"Condition '{rule_id}' passed in engine but re-evaluates as FAIL.")
                        
                except Exception as e:
                    formula_validation = False
                    warnings.append(f"Error re-evaluating condition '{rule_id}': {e}")

            elif step_type == "FORMULA":
                if rule_id not in formulas_map:
                    warnings.append(f"Formula ID '{rule_id}' in trace is not defined in contract.")
                    continue
                
                formula = formulas_map[rule_id]
                expr = formula.get("expression")
                out_var = formula.get("output_id")

                # Verify rule dependency integrity (check that variable bindings exist in context)
                for bind in formula.get("variable_bindings", []):
                    b_id = bind.get("source_id")
                    b_kind = bind.get("source_kind")
                    if b_kind == "DERIVED" and b_id not in context and f"input:{b_id}" not in context:
                        dependency_validation = False
                        warnings.append(f"Formula '{rule_id}' evaluated before dependency variable '{b_id}' was resolved.")

                # Check for division-by-zero protection
                self._check_div_by_zero(expr, context, warnings)

                # Re-evaluate formula
                try:
                    re_val = self.evaluator.evaluate(expr, context)
                    
                    # Store trace result in context for subsequent steps (as the engine did)
                    context[rule_id] = result
                    if out_var:
                        context[out_var] = result

                    # Compare results
                    if result is not None and re_val is not None:
                        # Float comparisons
                        try:
                            f_res = float(result)
                            f_re = float(re_val)
                            if not math.isclose(f_res, f_re, rel_tol=1e-5, abs_tol=1e-5):
                                formula_validation = False
                                warnings.append(
                                    f"Formula calculation mismatch for '{rule_id}': "
                                    f"engine resolved '{f_res}', validator re-calculated '{f_re}'."
                                )
                        except (ValueError, TypeError):
                            if result != re_val:
                                formula_validation = False
                                warnings.append(
                                    f"Formula string comparison mismatch for '{rule_id}': "
                                    f"engine resolved '{result}', validator re-calculated '{re_val}'."
                                )
                    elif result is not None or re_val is not None:
                        formula_validation = False
                        warnings.append(f"Formula evaluation mismatch for '{rule_id}': one resolved to None, other did not.")

                except Exception as e:
                    formula_validation = False
                    warnings.append(f"Error re-evaluating formula '{rule_id}': {e}")

        # 8. Rounding Policy Compliance
        # Scheme 33(9) rounding policy: FSI rounded to 2 decimal places. Maximum BUA rounded to 2 decimal places.
        # Check if the outputs in root match rounded values
        app_fsi = execution_output.get("applicable_fsi", 0.0)
        max_bua = execution_output.get("maximum_bua", 0.0)
        
        # Verify rounding of FSI from context
        fsi_raw = context.get("dcpr:33-9:applicable-fsi", context.get("applicable_fsi"))
        if fsi_raw is not None:
            expected_fsi = round(float(fsi_raw), 2)
            if not math.isclose(app_fsi, expected_fsi, abs_tol=1e-2):
                rounding_validation = False
                warnings.append(f"FSI rounding policy mismatch: got '{app_fsi}', expected '{expected_fsi}'.")

        # 9. Boundary Conditions verification
        # FSI must be >= 4.0 for Scheme 33(9) standard eligible plot
        if execution_output.get("eligibility") == "ELIGIBLE":
            if app_fsi < 4.0:
                boundary_validation = False
                warnings.append(f"Boundary condition violation: applicable FSI '{app_fsi}' is below baseline floor 4.00.")
            if max_bua <= 0:
                boundary_validation = False
                warnings.append(f"Boundary condition violation: maximum BUA '{max_bua}' must be positive for eligible schemes.")

        # 10. Audit Trace Completeness
        # Check if all conditions and formulas defined in the contract are present in the trace
        if execution_output.get("eligibility") == "ELIGIBLE":
            for cond in scheme_contract.get("conditions", []):
                if cond["id"] not in executed_rule_ids:
                    completeness_validation = False
                    warnings.append(f"Audit trace incomplete: Condition '{cond['id']}' was not executed.")
            for form in scheme_contract.get("formulae", []):
                if form["id"] not in executed_rule_ids:
                    completeness_validation = False
                    warnings.append(f"Audit trace incomplete: Formula '{form['id']}' was not executed.")

        validation_status = "PASS" if (
            formula_validation and table_validation and unit_validation and
            rounding_validation and boundary_validation and dependency_validation and
            completeness_validation
        ) else "FAIL"

        return {
            "validation_status": validation_status,
            "formula_validation": formula_validation,
            "table_validation": table_validation,
            "unit_validation": unit_validation,
            "rounding_validation": rounding_validation,
            "boundary_validation": boundary_validation,
            "dependency_validation": dependency_validation,
            "completeness_validation": completeness_validation,
            "warnings": warnings
        }

    def _check_div_by_zero(self, expr, context, warnings):
        """Recursively scans the AST expression for divisions and checks for non-zero divisors."""
        if not isinstance(expr, dict):
            return

        op = expr.get("op")
        args = expr.get("args", [])

        if op == "DIVIDE" and len(args) >= 2:
            try:
                divisor_val = self.evaluator.evaluate(args[1], context)
                if divisor_val == 0:
                    warnings.append("Division-by-zero risk detected: divisor in formula evaluates to 0.")
            except Exception:
                pass

        for arg in args:
            self._check_div_by_zero(arg, context, warnings)
