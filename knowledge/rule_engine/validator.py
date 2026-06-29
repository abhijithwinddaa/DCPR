from knowledge.rule_engine.evaluator import ASTEvaluator

class InputValidator:
    """
    InputValidator runs type checks, negative values constraints,
    and parses/evaluates input validation rules from the contract.
    """
    def __init__(self):
        self.evaluator = ASTEvaluator()

    def validate(self, inputs_schema, user_inputs):
        """
        Validates user_inputs against the scheme's input parameter schemas.
        Returns a list of validation errors. If empty, validation passes.
        """
        errors = []

        # Convert user inputs to context dict
        context = {k: v for k, v in user_inputs.items()}

        # 1. Check for missing required inputs
        for inp in inputs_schema:
            name = inp.get("name")
            inp_id = inp.get("id")
            required = inp.get("required", False)
            
            # Find in user inputs (checking both with and without prefix)
            val = None
            if name in user_inputs:
                val = user_inputs[name]
            elif inp_id in user_inputs:
                val = user_inputs[inp_id]
                
            if val is None:
                if required:
                    errors.append({
                        "id": inp_id,
                        "type": "MISSING_INPUT",
                        "message": f"Required input parameter '{name}' is missing."
                    })
                continue

            # 2. Check for negative value edge case (applicable to numeric types)
            value_type = inp.get("value_type", "")
            if value_type in ("QUANTITY", "DECIMAL", "INTEGER", "NUMBER"):
                try:
                    num_val = float(val)
                    if num_val < 0:
                        errors.append({
                            "id": inp_id,
                            "type": "NEGATIVE_VALUE",
                            "message": f"Input parameter '{name}' cannot be negative (got {val})."
                        })
                except (ValueError, TypeError):
                    errors.append({
                        "id": inp_id,
                        "type": "TYPE_MISMATCH",
                        "message": f"Input parameter '{name}' expected numeric type, got '{type(val).__name__}'."
                    })

            # 3. Evaluate custom AST validation constraints
            constraints = inp.get("constraints", [])
            for const in constraints:
                expr = const.get("expression")
                msg = const.get("message", f"Constraint validation failed for {name}.")
                if expr:
                    try:
                        res = self.evaluator.evaluate(expr, context)
                        if not res:
                            errors.append({
                                "id": inp_id,
                                "type": "CONSTRAINT_VIOLATION",
                                "message": msg
                            })
                    except Exception as e:
                        errors.append({
                            "id": inp_id,
                            "type": "CONSTRAINT_ERROR",
                            "message": f"Error evaluating constraint for '{name}': {e}"
                        })

        return errors
