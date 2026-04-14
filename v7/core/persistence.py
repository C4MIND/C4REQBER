import json
from pathlib import Path
from typing import Dict, Optional
from data.domain_profiles import DomainProfile, PentadDistribution, SeptetDistribution


class DomainStorage:
    """Persistent storage for domain profiles"""
    
    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path.home() / '.turbo-cdi' / 'domains.json'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, DomainProfile] = {}
        self._load()
    
    def _load(self):
        if self.path.exists():
            with open(self.path) as f:
                data = json.load(f)
                self._cache = self._deserialize(data)
    
    def _save(self):
        data = self._serialize(self._cache)
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _serialize(self, profiles):
        return {
            name: {
                'name': p.name, 'category': p.category, 'subdomain': p.subdomain,
                'total_processes': p.total_processes,
                'pentad': {'ACTIVATE': p.pentad.ACTIVATE, 'INHIBIT': p.pentad.INHIBIT, 
                          'MODULATE': p.pentad.MODULATE, 'REGULATE': p.pentad.REGULATE, 
                          'DISRUPT': p.pentad.DISRUPT},
                'septet': {'STATE': p.septet.STATE, 'STRUCTURE': p.septet.STRUCTURE,
                          'CONTENT': p.septet.CONTENT, 'FUNCTION': p.septet.FUNCTION,
                          'RELATIONS': p.septet.RELATIONS, 'MEMORY': p.septet.MEMORY, 
                          'BOUNDARY': p.septet.BOUNDARY},
                'reversibility_yes': p.reversibility_yes,
                'reversibility_conditional': p.reversibility_conditional,
                'reversibility_no': p.reversibility_no,
                'signature': p.signature
            }
            for name, p in profiles.items()
        }
    
    def _deserialize(self, data):
        profiles = {}
        for name, d in data.items():
            profiles[name] = DomainProfile(
                name=d['name'], category=d['category'], subdomain=d['subdomain'],
                total_processes=d['total_processes'],
                pentad=PentadDistribution(**d['pentad']),
                septet=SeptetDistribution(**d['septet']),
                reversibility_yes=d['reversibility_yes'],
                reversibility_conditional=d['reversibility_conditional'],
                reversibility_no=d['reversibility_no'],
                signature=d['signature']
            )
        return profiles
    
    def get(self, name: str) -> Optional[DomainProfile]:
        return self._cache.get(name)
    
    def set(self, name: str, profile: DomainProfile):
        self._cache[name] = profile
        self._save()
    
    def list_all(self) -> Dict[str, DomainProfile]:
        return self._cache.copy()
