class TableResolver:
    """
    TableResolver maps lookups to specific cell outputs in multidimensional tables.
    """
    def __init__(self, tables_list=None):
        # Store tables by their IDs
        self.tables = {}
        if tables_list:
            for table in tables_list:
                self.tables[table["id"]] = table

    def set_tables(self, tables_list):
        self.tables = {t["id"]: t for t in tables_list}

    def resolve(self, table_id, *args, context=None):
        """
        Resolves the value of a table cell based on dimension lookup values.
        *args lists the dimension coordinates in order (e.g., basic_ratio, gross_cluster_area).
        """
        if table_id not in self.tables:
            raise ValueError(f"Table not found in contract: {table_id}")

        table = self.tables[table_id]
        dimensions = table.get("dimensions", [])
        cells = table.get("cells", [])

        if len(args) != len(dimensions):
            raise ValueError(
                f"Lookup dimension mismatch for table {table_id}: "
                f"expected {len(dimensions)} arguments, got {len(args)}"
            )

        # Map each lookup value to its corresponding member index
        indices = []
        for i, val in enumerate(args):
            dim = dimensions[i]
            matched_idx = self._find_matching_member_index(dim, val)
            if matched_idx is None:
                raise ValueError(
                    f"Lookup value {val} does not fall within any range defined for "
                    f"dimension '{dim['id']}' in table {table_id}"
                )
            indices.append(matched_idx)

        # Find the matching cell by row/col coordinates
        # In a 2D table, indices = [row_idx, col_idx]
        row_idx = indices[0]
        col_idx = indices[1] if len(indices) > 1 else 0

        for cell in cells:
            if cell.get("row") == row_idx and cell.get("column") == col_idx:
                val = cell.get("normalized_value")
                # Convert percentage values to decimals (e.g. 55% -> 0.55)
                if cell.get("value_type") == "PERCENTAGE" or cell.get("unit") == "percentage":
                    try:
                        return float(val) / 100.0
                    except (ValueError, TypeError):
                        pass
                return val

        raise ValueError(
            f"No cell found at coordinates (row: {row_idx}, column: {col_idx}) "
            f"in table {table_id}"
        )

    def _find_matching_member_index(self, dimension, value):
        """
        Scans a dimension's members to find which bin the value falls into.
        Returns the index of the matching member, or None.
        """
        try:
            val = float(value)
        except (ValueError, TypeError):
            # If value cannot be cast to float, do string comparison or return None
            return None

        for idx, member in enumerate(dimension.get("members", [])):
            low = member.get("lower_bound")
            low_inc = member.get("lower_inclusive", True)
            high = member.get("upper_bound")
            high_inc = member.get("upper_inclusive", True)

            # Check lower bound
            if low is not None and low != "":
                try:
                    low_f = float(low)
                    if low_inc:
                        if val < low_f:
                            continue
                    else:
                        if val <= low_f:
                            continue
                except ValueError:
                    pass

            # Check upper bound
            if high is not None and high != "":
                try:
                    high_f = float(high)
                    if high_inc:
                        if val > high_f:
                            continue
                    else:
                        if val >= high_f:
                            continue
                except ValueError:
                    pass

            # If both bounds passed, we have a match
            return idx

        return None
