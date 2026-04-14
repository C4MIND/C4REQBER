"""
TURBO-CDI v7.0 - Output Formatters
Multiple output formats for CLI results

This module provides:
- JSON output with proper serialization
- CSV output for tabular data
- YAML output (if PyYAML available)
- Pretty-printed tables
"""

import json
import csv
import io
from typing import Dict, List, Any, Optional
from datetime import datetime


class OutputFormatter:
    """
    Multi-format output formatter for TURBO-CDI results.
    
    Supports JSON, CSV, and human-readable table formats.
    """
    
    @staticmethod
    def to_json(data: Any, indent: int = 2) -> str:
        """
        Convert data to JSON string.
        
        Args:
            data: Data to serialize
            indent: Indentation level for pretty printing
            
        Returns:
            JSON formatted string
        """
        def default_serializer(obj):
            """Handle non-serializable types"""
            if hasattr(obj, 'value'):
                return obj.value
            if hasattr(obj, 'name'):
                return obj.name
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            if hasattr(obj, '__str__'):
                return str(obj)
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        
        return json.dumps(data, indent=indent, default=default_serializer)
    
    @staticmethod
    def to_csv(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
        """
        Convert list of dicts to CSV string.
        
        Args:
            data: List of dictionaries to convert
            headers: Optional column headers (auto-detected if not provided)
            
        Returns:
            CSV formatted string
        """
        if not data:
            return ""
        
        # Auto-detect headers from first row
        if headers is None:
            headers = list(data[0].keys())
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    
    @staticmethod
    def to_yaml(data: Any) -> str:
        """
        Convert data to YAML string (if PyYAML is available).
        
        Args:
            data: Data to serialize
            
        Returns:
            YAML formatted string, or JSON fallback
        """
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            # Fallback to JSON if PyYAML not installed
            return f"# YAML output requires PyYAML. Using JSON fallback:\n{OutputFormatter.to_json(data)}"
    
    @staticmethod
    def to_table(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
        """
        Convert data to a formatted ASCII table.
        
        Args:
            data: List of dictionaries to display
            columns: Specific columns to include
            
        Returns:
            Formatted table string
        """
        if not data:
            return "(no data)"
        
        # Determine columns
        if columns is None:
            columns = list(data[0].keys())
        
        # Calculate column widths
        widths = {}
        for col in columns:
            header_len = len(str(col))
            max_data_len = max(len(str(row.get(col, ''))) for row in data)
            widths[col] = max(header_len, max_data_len) + 2
        
        lines = []
        
        # Header row
        header = '|'.join(f" {str(col):<{widths[col]-1}}" for col in columns)
        lines.append(header)
        lines.append('-' * len(header))
        
        # Data rows
        for row in data:
            row_str = '|'.join(
                f" {str(row.get(col, '')):<{widths[col]-1}}" 
                for col in columns
            )
            lines.append(row_str)
        
        return '\n'.join(lines)


class ValidationReportFormatter:
    """Specialized formatter for LambdaValidator results"""
    
    @staticmethod
    def to_json(validation_result: Dict[str, Any]) -> str:
        """Format validation result as JSON"""
        return OutputFormatter.to_json(validation_result)
    
    @staticmethod
    def to_text(validation_result: Dict[str, Any]) -> str:
        """Format validation result as human-readable text"""
        lines = []
        
        # Overall status
        if validation_result.get('valid'):
            lines.append("✅ VALID")
        else:
            lines.append("❌ INVALID")
        
        lines.append("")
        
        # Individual checks
        lines.append("Checks:")
        for check_name, passed in validation_result.get('checks', {}).items():
            status = "✓" if passed else "✗"
            lines.append(f"  [{status}] {check_name}")
        
        # Errors
        errors = validation_result.get('errors', [])
        if errors:
            lines.append("")
            lines.append("Errors:")
            for error in errors:
                lines.append(f"  • {error}")
        
        # Warnings
        warnings = validation_result.get('warnings', [])
        if warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in warnings:
                lines.append(f"  • {warning}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def to_csv(validation_result: Dict[str, Any]) -> str:
        """Format validation result as CSV"""
        rows = []
        
        # Add overall validity
        rows.append({
            'category': 'overall',
            'check': 'valid',
            'passed': validation_result.get('valid', False),
            'message': ''
        })
        
        # Add individual checks
        for check_name, passed in validation_result.get('checks', {}).items():
            rows.append({
                'category': 'check',
                'check': check_name,
                'passed': passed,
                'message': ''
            })
        
        # Add errors
        for error in validation_result.get('errors', []):
            rows.append({
                'category': 'error',
                'check': '',
                'passed': False,
                'message': error
            })
        
        # Add warnings
        for warning in validation_result.get('warnings', []):
            rows.append({
                'category': 'warning',
                'check': '',
                'passed': True,
                'message': warning
            })
        
        return OutputFormatter.to_csv(rows)


class NavigationReportFormatter:
    """Specialized formatter for navigation/planning results"""
    
    @staticmethod
    def to_json(result: Dict[str, Any]) -> str:
        """Format navigation result as JSON"""
        return OutputFormatter.to_json(result)
    
    @staticmethod
    def to_text(result: Dict[str, Any]) -> str:
        """Format navigation result as human-readable text"""
        lines = []
        
        # Header
        lines.append("🧭 Navigation Plan")
        lines.append("")
        
        # Transformation details
        trans = result.get('transformation')
        if trans:
            lines.append(f"Operation: {trans.operation.name if hasattr(trans.operation, 'name') else trans.operation}")
            lines.append(f"Target: {trans.target.value if hasattr(trans.target, 'value') else trans.target}")
            lines.append(f"Reversibility: {trans.reversibility:.2%}")
            lines.append(f"Resonance: {trans.resonance:.2f}")
            lines.append("")
        
        # Path
        path = result.get('path', [])
        if path:
            lines.append(f"Path ({len(path)} steps):")
            for i, step in enumerate(path, 1):
                op_name = step.operator.name if hasattr(step.operator, 'name') else step.operator
                lines.append(f"  {i}. {op_name}")
                lines.append(f"     Resonance: {step.resonance_coefficient:.2f}")
        
        # Effectiveness
        effectiveness = result.get('estimated_effectiveness')
        if effectiveness is not None:
            lines.append("")
            lines.append(f"Estimated Effectiveness: {effectiveness:.2%}")
        
        return '\n'.join(lines)


def format_output(data: Any, format_type: str, **kwargs) -> str:
    """
    Generic output formatting dispatcher.
    
    Args:
        data: Data to format
        format_type: One of 'json', 'csv', 'yaml', 'table', 'text'
        **kwargs: Additional format-specific arguments
        
    Returns:
        Formatted string
    """
    formatters = {
        'json': lambda d, **kw: OutputFormatter.to_json(d),
        'csv': lambda d, **kw: OutputFormatter.to_csv(d, kw.get('headers')),
        'yaml': lambda d, **kw: OutputFormatter.to_yaml(d),
        'table': lambda d, **kw: OutputFormatter.to_table(d, kw.get('columns')),
        'text': lambda d, **kw: str(d),
    }
    
    formatter = formatters.get(format_type.lower(), formatters['text'])
    return formatter(data, **kwargs)
