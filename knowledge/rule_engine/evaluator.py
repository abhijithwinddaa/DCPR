class ASTEvaluator:
    """
    ASTEvaluator recursively evaluates arithmetic, logical, and relational expressions
    from the canonical schema.
    """
    def __init__(self, table_resolver=None):
        self.table_resolver = table_resolver

    def evaluate(self, expr, context):
        """
        Evaluates the expression dictionary under the given context.
        context maps variable/node IDs to python scalar values.
        """
        if not isinstance(expr, dict):
            # Assume it's a literal value directly
            return expr

        # 1. Resolve variable or literal references
        kind = expr.get("kind")
        if kind:
            val_id = expr.get("id")
            if kind == "LITERAL":
                val = expr.get("value")
                try:
                    # Convert to float or int if possible
                    if "." in str(val):
                        return float(val)
                    return int(val)
                except ValueError:
                    return val
            elif kind in ("INPUT", "FACT", "DERIVED"):
                # Normalize keys (strip prefixes)
                clean_id = val_id
                if clean_id.startswith("input:"):
                    clean_id = clean_id[6:]
                
                # Check for exact matches first
                if val_id in context:
                    return context[val_id]
                if clean_id in context:
                    return context[clean_id]
                
                # Fallback: check if the value is a number or defined in constants
                raise KeyError(f"Missing context value for variable: {val_id} (normalized as {clean_id})")

        # 2. Resolve operations
        op = expr.get("op")
        if not op:
            # If no op and no kind, maybe it's empty
            return None

        if op == "LOOKUP":
            if not self.table_resolver:
                raise ValueError("Table resolver is required to evaluate LOOKUP operations")
            # First argument is the table reference (holds the table ID)
            # Do NOT evaluate it recursively, just extract the table ID
            table_ref = expr["args"][0]
            table_id = table_ref.get("id") if isinstance(table_ref, dict) else table_ref
            # Evaluate only index dimensions arguments recursively
            lookup_args = [self.evaluate(arg, context) for arg in expr["args"][1:]]
            return self.table_resolver.resolve(table_id, *lookup_args, context=context)

        # Recursively evaluate all args for other ops
        args = [self.evaluate(arg, context) for arg in expr.get("args", [])]

        if op == "ADD":
            return sum(args)
        elif op == "SUBTRACT":
            if len(args) < 2:
                raise ValueError("SUBTRACT operator requires at least 2 arguments")
            return args[0] - sum(args[1:])
        elif op == "MULTIPLY":
            prod = 1
            for a in args:
                prod *= a
            return prod
        elif op == "DIVIDE":
            if len(args) < 2:
                raise ValueError("DIVIDE operator requires at least 2 arguments")
            if args[1] == 0:
                raise ZeroDivisionError("Division by zero in formula evaluation")
            return args[0] / args[1]
        elif op == "MAX":
            return max(args)
        elif op == "GTE":
            return args[0] >= args[1]
        elif op == "LTE":
            return args[0] <= args[1]
        elif op == "GT":
            return args[0] > args[1]
        elif op == "LT":
            return args[0] < args[1]
        elif op == "EQ":
            return args[0] == args[1]
        elif op == "AND":
            return all(args)
        elif op == "OR":
            return any(args)
        elif op == "NOT":
            return not args[0]
        else:
            raise ValueError(f"Unknown AST operator: {op}")
