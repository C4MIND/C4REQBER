"""
TURBO-CDI v7.0 - Lambda Validator
Formal verification using type theory and lambda calculus principles

This module provides:
- Type compatibility checking between Pentad operations and Septet objects
- Context validity verification
- Transformation composition with safety checks
- Detailed validation reports
"""

from typing import Dict, List, Optional, Any
from core.meta_prime_engine import Transformation, PentadOperation, SeptetObject, C4State
from core.logger import setup_logger


class LambdaValidator:
    """Formal verification using type theory"""
    
    def __init__(self):
        self.logger = setup_logger('validator')
        
        # Define operation-target compatibility matrix
        self._compatibility_matrix = {
            PentadOperation.ACTIVATE: [
                SeptetObject.STATE, 
                SeptetObject.FUNCTION, 
                SeptetObject.CONTENT
            ],
            PentadOperation.INHIBIT: [
                SeptetObject.STATE, 
                SeptetObject.FUNCTION, 
                SeptetObject.RELATIONS
            ],
            PentadOperation.MODULATE: [
                SeptetObject.STATE, 
                SeptetObject.STRUCTURE, 
                SeptetObject.FUNCTION, 
                SeptetObject.CONTENT
            ],
            PentadOperation.REGULATE: [
                SeptetObject.STRUCTURE, 
                SeptetObject.FUNCTION, 
                SeptetObject.RELATIONS, 
                SeptetObject.BOUNDARY
            ],
            PentadOperation.DISRUPT: [
                SeptetObject.STRUCTURE, 
                SeptetObject.STATE, 
                SeptetObject.MEMORY
            ],
        }
    
    def verify(self, transformation: Transformation) -> Dict[str, Any]:
        """
        Verify a transformation is well-formed and valid.
        
        Returns a detailed result dictionary with:
        - valid: Overall boolean validity
        - checks: Individual check results
        - errors: List of error messages
        - warnings: List of warning messages
        """
        result = {
            'valid': True, 
            'checks': {}, 
            'errors': [],
            'warnings': []
        }
        
        # Check 1: Type compatibility (Operation can be applied to Target)
        valid_targets = self._compatibility_matrix.get(transformation.operation, [])
        type_check = transformation.target in valid_targets
        result['checks']['type_compatible'] = type_check
        if not type_check:
            result['errors'].append(
                f"{transformation.operation.name} not applicable to {transformation.target.value}"
            )
            self.logger.warning(
                f"Type incompatibility: {transformation.operation.name} → {transformation.target.value}"
            )
        
        # Check 2: Context validity (C4 state is valid)
        context_check = isinstance(transformation.context, C4State)
        result['checks']['context_valid'] = context_check
        if not context_check:
            result['errors'].append("Invalid C4 context state")
        
        # Check 3: Reversibility bounds (must be in [0.0, 1.0])
        rev_bounds_check = 0.0 <= transformation.reversibility <= 1.0
        result['checks']['reversibility_in_bounds'] = rev_bounds_check
        if not rev_bounds_check:
            result['errors'].append(
                f"Reversibility {transformation.reversibility} out of bounds [0.0, 1.0]"
            )
        
        # Check 4: Reversibility computable (for practical applications)
        rev_computable = transformation.reversibility >= 0.0
        result['checks']['reversibility_computable'] = rev_computable
        
        # Check 5: Resonance bounds
        resonance_check = 0.0 <= transformation.resonance <= 1.0
        result['checks']['resonance_valid'] = resonance_check
        if not resonance_check:
            result['errors'].append(
                f"Resonance {transformation.resonance} out of bounds [0.0, 1.0]"
            )
        
        # Check 6: Composition safety (reversibility > 0 for safe composition)
        comp_check = transformation.reversibility > 0.0
        result['checks']['composition_safe'] = comp_check
        if not comp_check:
            result['warnings'].append(
                "Transformation is irreversible (reversibility = 0)"
            )
        
        # Check 7: Effectiveness threshold
        effectiveness = transformation.reversibility * transformation.resonance
        eff_check = effectiveness >= 0.1  # Minimum 10% effectiveness
        result['checks']['effectiveness_threshold'] = eff_check
        if not eff_check:
            result['warnings'].append(
                f"Low effectiveness ({effectiveness:.2%}) - consider adjusting parameters"
            )
        
        # Determine overall validity
        result['valid'] = all(result['checks'].values())
        
        if result['valid']:
            self.logger.info(f"Transformation validated: {transformation.signature()}")
        else:
            self.logger.error(f"Transformation failed validation: {result['errors']}")
        
        return result
    
    def compose(self, t1: Transformation, t2: Transformation) -> Dict[str, Any]:
        """
        Compose two transformations if compatible.
        
        Composition follows: t1 ∘ t2 (apply t2 first, then t1)
        
        Returns:
            - success: Whether composition succeeded
            - result: The composed transformation (or None)
            - explanation: Human-readable explanation
            - verification: Validation result for the composed transformation
        """
        # Check target compatibility (t2's output must match t1's input domain)
        if t2.target != t1.target:
            explanation = (
                f"Target mismatch: {t2.operation.name}→{t2.target.value} "
                f"cannot compose with {t1.operation.name}→{t1.target.value}"
            )
            self.logger.error(explanation)
            return {
                'success': False, 
                'result': None, 
                'explanation': explanation,
                'verification': None
            }
        
        # Check context compatibility
        if t2.context != t1.context:
            self.logger.warning(
                f"Composing transformations with different contexts: "
                f"{t2.context} → {t1.context}"
            )
        
        # Compose the transformations
        composed = Transformation(
            operation=t1.operation,
            target=t1.target,
            context=t2.context,  # Carry forward t2's context
            reversibility=min(t1.reversibility, t2.reversibility),
            resonance=min(t1.resonance, t2.resonance)
        )
        
        # Verify the composed transformation
        verification = self.verify(composed)
        
        explanation = (
            f"Composed {t2.operation.name}({t2.target.value}) → "
            f"{t1.operation.name}({t1.target.value}) | "
            f"R* = {composed.reversibility:.2f}"
        )
        
        self.logger.info(explanation)
        
        return {
            'success': verification['valid'],
            'result': composed if verification['valid'] else None,
            'explanation': explanation,
            'verification': verification
        }
    
    def chain(self, *transformations: Transformation) -> Dict[str, Any]:
        """
        Chain multiple transformations together.
        
        Returns:
            - success: Whether entire chain is valid
            - chain: List of composition results
            - final: The final composed transformation (or None)
            - errors: List of any errors encountered
        """
        if len(transformations) < 2:
            return {
                'success': False,
                'chain': [],
                'final': None,
                'errors': ["At least 2 transformations required for chaining"]
            }
        
        chain_results = []
        current = transformations[0]
        errors = []
        
        for i, next_trans in enumerate(transformations[1:], 1):
            result = self.compose(current, next_trans)
            chain_results.append({
                'step': i,
                **result
            })
            
            if not result['success']:
                errors.append(f"Step {i}: {result['explanation']}")
                return {
                    'success': False,
                    'chain': chain_results,
                    'final': None,
                    'errors': errors
                }
            
            current = result['result']
        
        return {
            'success': True,
            'chain': chain_results,
            'final': current,
            'errors': errors
        }
