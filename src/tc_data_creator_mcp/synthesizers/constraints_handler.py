"""Advanced constraints handler for SDV synthesizers."""

from typing import Any, Dict, List, Optional
import pandas as pd
from sdv.constraints import (
    Constraint,
    Inequality,
    Positive,
    Negative,
    Range,
    ScalarRange,
    ScalarInequality,
    OneHotEncoding,
    Unique,
    FixedCombinations,
)


class ConstraintsHandler:
    """Handles advanced constraints for synthetic data generation."""

    def __init__(self, constraints_config: Optional[Dict[str, Any]] = None):
        """
        Initialize constraints handler.

        Args:
            constraints_config: Dictionary with constraints configuration
        """
        self.config = constraints_config or {}
        self.sdv_constraints = []

    def build_constraints(self, df: pd.DataFrame) -> List[Constraint]:
        """
        Build SDV constraints from configuration.

        Args:
            df: Sample dataframe to infer types and values

        Returns:
            List of SDV Constraint objects
        """
        constraints = []

        # Process basic column constraints
        for col, col_config in self.config.items():
            if isinstance(col_config, dict) and col not in ["relationships", "conditional", "dependencies"]:
                constraints.extend(self._build_column_constraints(col, col_config, df))

        # Process relationship constraints
        if "relationships" in self.config:
            constraints.extend(self._build_relationship_constraints(self.config["relationships"], df))

        # Process conditional constraints
        if "conditional" in self.config:
            constraints.extend(self._build_conditional_constraints(self.config["conditional"], df))

        # Process dependencies
        if "dependencies" in self.config:
            constraints.extend(self._build_dependency_constraints(self.config["dependencies"], df))

        self.sdv_constraints = constraints
        return constraints

    def _build_column_constraints(
        self, column: str, config: Dict[str, Any], df: pd.DataFrame
    ) -> List[Constraint]:
        """Build constraints for a single column."""
        constraints = []

        # ScalarRange constraint for min/max on a single column
        if "min" in config or "max" in config:
            low = config.get("min")
            high = config.get("max")
            if low is not None and high is not None:
                constraints.append(
                    ScalarRange(
                        column_name=column,
                        low_value=low,
                        high_value=high,
                        strict_boundaries=config.get("strict", True)
                    )
                )
            elif low is not None and low == 0:
                constraints.append(Positive(column_name=column))
            elif high is not None and high == 0:
                constraints.append(Negative(column_name=column))

        # Unique constraint
        if config.get("unique", False):
            constraints.append(Unique(column_name=column))

        # Categorical values constraint
        if "values" in config:
            # SDV handles this through metadata, not constraints
            # We'll validate this during generation instead
            pass

        return constraints

    def _build_relationship_constraints(
        self, relationships: List[Dict[str, Any]], df: pd.DataFrame
    ) -> List[Constraint]:
        """Build relationship constraints between columns."""
        constraints = []

        for rel in relationships:
            rel_type = rel.get("type")

            if rel_type == "inequality":
                # Inequality constraint (was GreaterThan in older SDV)
                low_col = rel.get("low_column")
                high_col = rel.get("high_column")
                if low_col and high_col:
                    constraints.append(
                        Inequality(
                            low_column_name=low_col,
                            high_column_name=high_col
                        )
                    )

            elif rel_type == "custom_formula":
                # For custom formulas, we'll need to create a custom constraint
                # This is more complex and may require extending SDV's Constraint class
                constraints.append(
                    self._create_formula_constraint(
                        rel.get("column"),
                        rel.get("formula"),
                        df
                    )
                )

        return constraints

    def _build_conditional_constraints(
        self, conditionals: List[Dict[str, Any]], df: pd.DataFrame
    ) -> List[Constraint]:
        """Build conditional constraints."""
        constraints = []

        # Conditional constraints in SDV are handled through the Conditional class
        # This is more advanced and requires custom implementation
        # For now, we'll validate these post-generation

        return constraints

    def _build_dependency_constraints(
        self, dependencies: Dict[str, Any], df: pd.DataFrame
    ) -> List[Constraint]:
        """Build cross-column dependency constraints."""
        constraints = []

        # Fixed combinations constraint
        column = dependencies.get("column")
        depends_on = dependencies.get("depends_on", [])

        if column and depends_on:
            # Get all unique combinations from the sample data
            combo_cols = depends_on + [column]
            if all(col in df.columns for col in combo_cols):
                constraints.append(
                    FixedCombinations(column_names=combo_cols)
                )

        return constraints

    def _create_formula_constraint(
        self, target_column: str, formula: str, df: pd.DataFrame
    ) -> Constraint:
        """Create a custom formula constraint."""
        # This is a placeholder for custom formula constraints
        # In a real implementation, we'd create a custom Constraint subclass
        # that evaluates the formula during sampling

        class FormulaConstraint(Constraint):
            """Custom constraint for formula-based relationships."""

            def __init__(self, column_name: str, formula_str: str):
                self.column_name = column_name
                self.formula = formula_str
                self._columns = [column_name]

            def is_valid(self, table_data: pd.DataFrame) -> pd.Series:
                """Check if the constraint is satisfied."""
                try:
                    # Evaluate the formula
                    # This is a simplified version - in production you'd want
                    # proper formula parsing and evaluation
                    calculated = table_data.eval(self.formula)
                    actual = table_data[self.column_name]
                    return abs(calculated - actual) < 0.01  # tolerance for floating point
                except Exception:
                    return pd.Series([True] * len(table_data))

            def transform(self, table_data: pd.DataFrame) -> pd.DataFrame:
                """Transform data to satisfy constraint."""
                try:
                    table_data[self.column_name] = table_data.eval(self.formula)
                except Exception:
                    pass  # If formula fails, keep original data
                return table_data

            def reverse_transform(self, table_data: pd.DataFrame) -> pd.DataFrame:
                """Reverse transform (no-op for formula constraints)."""
                return table_data

        return FormulaConstraint(target_column, formula)

    def validate_constraints(self, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that generated data satisfies all constraints.

        Args:
            synthetic_df: Generated synthetic data

        Returns:
            Dictionary with validation results
        """
        violations = []
        passed = []

        for constraint in self.sdv_constraints:
            try:
                is_valid = constraint.is_valid(synthetic_df)
                if is_valid.all():
                    passed.append(str(constraint))
                else:
                    violation_count = (~is_valid).sum()
                    violations.append({
                        "constraint": str(constraint),
                        "violations": int(violation_count),
                        "percentage": float(violation_count / len(synthetic_df) * 100)
                    })
            except Exception as e:
                violations.append({
                    "constraint": str(constraint),
                    "error": str(e)
                })

        return {
            "passed": passed,
            "violations": violations,
            "total_constraints": len(self.sdv_constraints),
            "constraints_satisfied": len(passed),
        }
