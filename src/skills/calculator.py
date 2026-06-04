"""
TURBO-CDI: Calculator Skill
Advanced calculator with scientific functions
"""

import json
import math
from typing import Any, Dict

from .registry import Skill


class CalculatorSkill(Skill):
    """Scientific calculator skill."""

    name = "calc"
    description = "Advanced calculator with scientific functions"
    usage = "calc <expression>"

    def __init__(self):
        # Safe math namespace
        self.safe_dict = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "exp": math.exp,
            "log": math.log,
            "log10": math.log10,
            "sqrt": math.sqrt,
            "pow": math.pow,
            "pi": math.pi,
            "e": math.e,
            "abs": abs,
            "round": round,
            "ceil": math.ceil,
            "floor": math.floor,
            "factorial": math.factorial,
            "gcd": math.gcd,
            "degrees": math.degrees,
            "radians": math.radians,
        }

    def execute(self, args: str) -> str:
        """Execute calculation."""
        if not args.strip():
            return (
                "Usage: calc <expression>\nExamples: calc sin(pi/2), calc sqrt(16) + 5"
            )

        try:
            # Evaluate with safe namespace
            result = eval(args, {"__builtins__": {}}, self.safe_dict)

            # Format result
            if isinstance(result, float):
                if result == int(result):
                    return str(int(result))
                return f"{result:.10g}"

            return str(result)

        except Exception as e:
            return f"Error: {e}"


class UnitConverterSkill(Skill):
    """Unit conversion skill."""

    name = "convert"
    description = "Convert between units"
    usage = "convert <value> <from_unit> <to_unit>"

    # Conversion factors to base units
    CONVERSIONS = {
        # Length (to meters)
        "m": 1.0,
        "km": 1000.0,
        "cm": 0.01,
        "mm": 0.001,
        "um": 1e-6,
        "nm": 1e-9,
        "ft": 0.3048,
        "in": 0.0254,
        "yd": 0.9144,
        "mi": 1609.344,
        "ly": 9.461e15,
        "au": 1.496e11,
        "pc": 3.086e16,
        # Mass (to kg)
        "kg": 1.0,
        "g": 0.001,
        "mg": 1e-6,
        "ton": 1000.0,
        "lb": 0.453592,
        "oz": 0.0283495,
        # Time (to seconds)
        "s": 1.0,
        "sec": 1.0,
        "min": 60.0,
        "h": 3600.0,
        "hr": 3600.0,
        "day": 86400.0,
        "week": 604800.0,
        "year": 31536000.0,
        "yr": 31536000.0,
        # Temperature (special handling)
        "K": "temp",
        "C": "temp",
        "F": "temp",
        # Energy (to Joules)
        "J": 1.0,
        "kJ": 1000.0,
        "cal": 4.184,
        "kcal": 4184.0,
        "eV": 1.602e-19,
        "keV": 1.602e-16,
        "MeV": 1.602e-13,
        "GeV": 1.602e-10,
        "Wh": 3600.0,
        "kWh": 3.6e6,
        # Pressure (to Pascals)
        "Pa": 1.0,
        "kPa": 1000.0,
        "MPa": 1e6,
        "GPa": 1e9,
        "bar": 1e5,
        "mbar": 100.0,
        "atm": 101325.0,
        "torr": 133.322,
        "psi": 6894.76,
        # Power (to Watts)
        "W": 1.0,
        "kW": 1000.0,
        "MW": 1e6,
        "GW": 1e9,
        "hp": 745.7,
        # Frequency (to Hz)
        "Hz": 1.0,
        "kHz": 1000.0,
        "MHz": 1e6,
        "GHz": 1e9,
        "THz": 1e12,
        # Data (to bytes)
        "B": 1.0,
        "KB": 1024.0,
        "MB": 1048576.0,
        "GB": 1073741824.0,
        "TB": 1099511627776.0,
        "PB": 1.1259e15,
    }

    def execute(self, args: str) -> str:
        """Execute conversion."""
        parts = args.split()

        if len(parts) != 3:
            return "Usage: convert <value> <from_unit> <to_unit>\nExamples: convert 100 m km, convert 25 C F"

        try:
            value = float(parts[0])
            from_unit = parts[1]
            to_unit = parts[2]

            result = self._convert(value, from_unit, to_unit)

            if isinstance(result, str):
                return result

            return f"{value} {from_unit} = {result:.6g} {to_unit}"

        except Exception as e:
            return f"Error: {e}"

    def _convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Perform conversion."""
        # Check if units exist
        if from_unit not in self.CONVERSIONS:
            return f"Unknown unit: {from_unit}"
        if to_unit not in self.CONVERSIONS:
            return f"Unknown unit: {to_unit}"

        from_factor = self.CONVERSIONS[from_unit]
        to_factor = self.CONVERSIONS[to_unit]

        # Temperature special handling
        if from_factor == "temp" and to_factor == "temp":
            return self._convert_temp(value, from_unit, to_unit)

        if from_factor == "temp" or to_factor == "temp":
            return "Cannot convert between temperature and other units"

        # Standard conversion: value * from_factor / to_factor
        return value * from_factor / to_factor

    def _convert_temp(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature."""
        # Convert to Kelvin first
        if from_unit == "C":
            kelvin = value + 273.15
        elif from_unit == "F":
            kelvin = (value - 32) * 5 / 9 + 273.15
        elif from_unit == "K":
            kelvin = value
        else:
            raise ValueError(f"Unknown temperature unit: {from_unit}")

        # Convert from Kelvin to target
        if to_unit == "C":
            return kelvin - 273.15
        elif to_unit == "F":
            return (kelvin - 273.15) * 9 / 5 + 32
        elif to_unit == "K":
            return kelvin
        else:
            raise ValueError(f"Unknown temperature unit: {to_unit}")


class DataAnalyzerSkill(Skill):
    """Data analysis skill."""

    name = "analyze"
    description = "Analyze data sets (mean, median, std, etc.)"
    usage = "analyze <comma-separated values>"

    def execute(self, args: str) -> str:
        """Analyze data."""
        if not args.strip():
            return "Usage: analyze 1,2,3,4,5,6,7,8,9,10"

        try:
            # Parse numbers
            values = [float(x.strip()) for x in args.split(",")]

            if not values:
                return "No data provided"

            # Calculate statistics
            n = len(values)
            mean = sum(values) / n

            # Median
            sorted_vals = sorted(values)
            mid = n // 2
            if n % 2 == 0:
                median = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
            else:
                median = sorted_vals[mid]

            # Standard deviation
            variance = sum((x - mean) ** 2 for x in values) / n
            std_dev = variance**0.5

            # Min/max
            min_val = min(values)
            max_val = max(values)

            # Range
            range_val = max_val - min_val

            # Quartiles
            q1 = sorted_vals[n // 4] if n >= 4 else sorted_vals[0]
            q3 = sorted_vals[3 * n // 4] if n >= 4 else sorted_vals[-1]
            iqr = q3 - q1

            result = f"""Data Analysis ({n} values)
{"─" * 40}
Mean:       {mean:.4f}
Median:     {median:.4f}
Std Dev:    {std_dev:.4f}
Variance:   {variance:.4f}
{"─" * 40}
Min:        {min_val:.4f}
Max:        {max_val:.4f}
Range:      {range_val:.4f}
{"─" * 40}
Q1 (25%):   {q1:.4f}
Q3 (75%):   {q3:.4f}
IQR:        {iqr:.4f}"""

            return result

        except Exception as e:
            return f"Error analyzing data: {e}"


class CodeExecutorSkill(Skill):
    """Execute Python code safely."""

    name = "code"
    description = "Execute Python code"
    usage = "code <python_code>"

    def execute(self, args: str) -> str:
        """Execute code."""
        if not args.strip():
            return "Usage: code print('Hello') or code x = 5; print(x**2)"

        # Capture output
        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            # Create safe namespace
            safe_namespace = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "pow": pow,
                    "divmod": divmod,
                    "isinstance": isinstance,
                    "type": type,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "sorted": sorted,
                    "reversed": reversed,
                    "any": any,
                    "all": all,
                }
            }

            # Add math functions
            import math

            safe_namespace.update(
                {
                    "math": math,
                    "pi": math.pi,
                    "e": math.e,
                }
            )

            # Execute
            exec(args, safe_namespace)

            # Get output
            sys.stdout = old_stdout
            output = captured_output.getvalue()

            if output.strip():
                return output.strip()
            else:
                return "[Code executed successfully - no output]"

        except Exception as e:
            sys.stdout = old_stdout
            return f"Error: {type(e).__name__}: {e}"
