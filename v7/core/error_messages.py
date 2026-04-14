"""
TURBO-CDI v7.0 - Error Messages & Suggestions
User-friendly error handling with intelligent suggestions

This module provides:
- Domain name suggestions for misspelled inputs
- Context-aware error messages
- Recovery hints for common mistakes
"""

from difflib import get_close_matches
from typing import List, Optional


# Common domain aliases and variations
DOMAIN_ALIASES = {
    'cs': 'computer_science',
    'comp sci': 'computer_science',
    'psych': 'psychology',
    'math': 'mathematics',
    'stats': 'statistics',
    'bio': 'biology',
    'chem': 'chemistry',
    'phys': 'physics',
    'phil': 'philosophy',
    'econ': 'economics',
    'soc': 'sociology',
    'anthro': 'anthropology',
    'ling': 'linguistics',
    'hist': 'history',
    'lit': 'literature',
    'eng': 'engineering',
    'med': 'medicine',
    'law': 'jurisprudence',
    'art': 'art_theory',
    'music': 'music_theory',
    'arch': 'architecture',
}


class ErrorMessenger:
    """Centralized error message handler with suggestions"""
    
    def __init__(self, available_domains: Optional[List[str]] = None):
        self.available_domains = available_domains or []
        self._setup_error_catalog()
    
    def _setup_error_catalog(self):
        """Define standard error messages"""
        self.catalog = {
            'domain_not_found': {
                'message': "Domain '{domain}' not found",
                'hint': "Check spelling or use 'turbo-cdi list --category all'"
            },
            'invalid_c4_format': {
                'message': "Invalid C4 state format: '{input}'",
                'hint': "Use format '(P,0,0)' or compact 'P00'"
            },
            'invalid_operation': {
                'message': "Invalid operation: '{operation}'",
                'hint': "Valid operations: ACTIVATE, INHIBIT, MODULATE, REGULATE, DISRUPT"
            },
            'invalid_target': {
                'message': "Invalid target: '{target}'",
                'hint': "Valid targets: STATE, STRUCTURE, CONTENT, FUNCTION, RELATIONS, MEMORY, BOUNDARY"
            },
            'type_incompatible': {
                'message': "Cannot apply {operation} to {target}",
                'hint': "Check operation-target compatibility"
            },
            'validation_failed': {
                'message': "Transformation validation failed",
                'hint': "Check reversibility and resonance values are in [0.0, 1.0]"
            },
        }
    
    def suggest_domain(self, user_input: str) -> str:
        """
        Suggest similar domain names for misspelled inputs.
        
        Args:
            user_input: The domain name entered by user
            
        Returns:
            Suggestion message with close matches or help text
        """
        # Normalize input
        normalized = user_input.lower().strip().replace(' ', '_')
        
        # Check aliases first
        if normalized in DOMAIN_ALIASES:
            alias_target = DOMAIN_ALIASES[normalized]
            return f"Did you mean '{alias_target}'? (alias: '{user_input}')"
        
        # Get fuzzy matches
        suggestions = get_close_matches(
            normalized, 
            self.available_domains, 
            n=3, 
            cutoff=0.6
        )
        
        if suggestions:
            formatted = [f"'{s}'" for s in suggestions]
            return f"Did you mean: {', '.join(formatted)}?"
        
        return "Use `turbo-cdi list --category all` to see available domains"
    
    def format_error(self, error_type: str, **kwargs) -> str:
        """
        Format an error message with suggestions.
        
        Args:
            error_type: Key from error catalog
            **kwargs: Values to interpolate into message
            
        Returns:
            Formatted error message with hint
        """
        if error_type not in self.catalog:
            return f"Unknown error: {error_type}"
        
        entry = self.catalog[error_type]
        message = entry['message'].format(**kwargs)
        hint = entry['hint']
        
        return f"❌ {message}\n   💡 {hint}"
    
    def domain_error(self, domain: str) -> str:
        """Generate domain not found error with suggestions"""
        suggestion = self.suggest_domain(domain)
        return (
            f"❌ Domain '{domain}' not found\n"
            f"   💡 {suggestion}"
        )
    
    def validation_errors(self, validation_result: dict) -> str:
        """Format validation errors from LambdaValidator"""
        if validation_result.get('valid'):
            return "✅ Transformation is valid"
        
        lines = ["❌ Validation failed:"]
        
        for error in validation_result.get('errors', []):
            lines.append(f"   • {error}")
        
        for warning in validation_result.get('warnings', []):
            lines.append(f"   ⚠️  {warning}")
        
        return '\n'.join(lines)


def suggest_domain(user_input: str, available_domains: List[str]) -> str:
    """
    Standalone function to suggest domain names.
    
    Args:
        user_input: The domain name entered by user
        available_domains: List of valid domain names
        
    Returns:
        Suggestion message
    """
    messenger = ErrorMessenger(available_domains)
    return messenger.suggest_domain(user_input)


def format_validation_report(validation_result: dict) -> str:
    """
    Format a validation result into a readable report.
    
    Args:
        validation_result: Result from LambdaValidator.verify()
        
    Returns:
        Formatted report string
    """
    lines = []
    
    # Header
    if validation_result['valid']:
        lines.append("✅ Validation Passed")
    else:
        lines.append("❌ Validation Failed")
    
    lines.append("")
    
    # Checks
    lines.append("📋 Checks:")
    for check_name, passed in validation_result['checks'].items():
        status = "✅" if passed else "❌"
        lines.append(f"   {status} {check_name}")
    
    # Errors
    if validation_result.get('errors'):
        lines.append("")
        lines.append("🚫 Errors:")
        for error in validation_result['errors']:
            lines.append(f"   • {error}")
    
    # Warnings
    if validation_result.get('warnings'):
        lines.append("")
        lines.append("⚠️  Warnings:")
        for warning in validation_result['warnings']:
            lines.append(f"   • {warning}")
    
    return '\n'.join(lines)
