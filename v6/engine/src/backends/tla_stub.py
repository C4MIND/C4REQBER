"""
TLA+ Backend Stub
Generates TLA+ specs (full integration requires TLC model checker)
"""

import asyncio
import tempfile
from typing import Dict, Any
from datetime import datetime


class TlaBackend:
    """Stub for TLA+ model checking backend"""
    
    async def model_check(self, spec: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run TLC model checker on TLA+ spec"""
        # Generate .tla file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tla', delete=False) as f:
            f.write(spec)
            tla_file = f.name
        
        # Generate .cfg file
        cfg_content = self._generate_cfg(config)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            f.write(cfg_content)
            cfg_file = f.name
        
        # Try to run TLC (requires TLA+ tools installed)
        try:
            proc = await asyncio.create_subprocess_exec(
                'tlc', tla_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            
            output = stdout.decode()
            
            if 'Model checking completed' in output:
                # Parse results
                states = self._parse_states(output)
                return {
                    'success': True,
                    'checked': True,
                    'states_generated': states,
                    'spec_file': tla_file,
                    'config_file': cfg_file,
                    'logs': output.split('\n')[:50]
                }
            else:
                return {
                    'success': False,
                    'checked': False,
                    'error': stderr.decode() or output[-500:],
                    'spec_file': tla_file
                }
                
        except FileNotFoundError:
            return {
                'success': True,  # Spec generated
                'checked': False,  # Not actually checked
                'states_generated': 0,
                'spec_file': tla_file,
                'config_file': cfg_file,
                'note': 'TLC not installed - TLA+ spec generated only',
                'install': 'Download TLA+ Toolbox from https://lamport.azurewebsites.net/tla/toolbox.html'
            }
        except asyncio.TimeoutError:
            return {
                'success': False,
                'checked': False,
                'error': 'Model checking timeout (300s)',
                'spec_file': tla_file
            }
    
    def _generate_cfg(self, config: Dict[str, Any]) -> str:
        """Generate TLC configuration"""
        cfg = 'INIT Init\nNEXT Next\n'
        
        if 'invariants' in config:
            for inv in config['invariants']:
                cfg += f'INVARIANT {inv}\n'
        
        if 'properties' in config:
            for prop in config['properties']:
                cfg += f'PROPERTY {prop}\n'
        
        if 'constants' in config:
            for name, value in config['constants'].items():
                cfg += f'CONSTANT {name} = {value}\n'
        
        return cfg
    
    def _parse_states(self, output: str) -> int:
        """Parse number of states from TLC output"""
        for line in output.split('\n'):
            if 'states generated' in line.lower():
                try:
                    return int(line.split()[0])
                except:
                    pass
        return 0
    
    def generate_spec_template(self, hypothesis) -> str:
        """Generate TLA+ spec from hypothesis"""
        return f"""---- MODULE HypothesisSpec ----
(* Auto-generated TLA+ specification
   Hypothesis: {hypothesis.title}
   Generated: {datetime.now().isoformat()}
*)

EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS
  Parameters

VARIABLES
  state

(* Hypothesis state *)
Init ==
  state = [k \\in DOMAIN Parameters |-> Parameters[k]]

(* State transitions *)
Next ==
  UNCHANGED state

(* Safety properties *)
TypeInvariant ==
  state \\in [DOMAIN Parameters -> Nat]

(* Liveness properties *)
Termination ==
  <>(state = state)  (* Placeholder *)

(* Main specification *)
Spec == Init /\\ [][Next]_state

====
"""


# Singleton instance
_tla_backend = None

def get_tla_backend() -> TlaBackend:
    global _tla_backend
    if _tla_backend is None:
        _tla_backend = TlaBackend()
    return _tla_backend