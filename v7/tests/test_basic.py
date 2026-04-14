"""
TURBO-CDI v7.0 Basic Smoke Tests
Validation of core infrastructure
"""

import pytest
from pathlib import Path


class TestErrorFramework:
    """Test custom error classes"""
    
    def test_base_error_exists(self):
        """TurboCDIError can be imported and raised"""
        from core.errors import TurboCDIError
        with pytest.raises(TurboCDIError):
            raise TurboCDIError("test error")
    
    def test_invalid_c4_state_error(self):
        """InvalidC4StateError is a TurboCDIError subclass"""
        from core.errors import InvalidC4StateError, TurboCDIError
        assert issubclass(InvalidC4StateError, TurboCDIError)
        with pytest.raises(InvalidC4StateError):
            raise InvalidC4StateError("invalid state")
    
    def test_domain_not_found_error(self):
        """DomainNotFoundError is a TurboCDIError subclass"""
        from core.errors import DomainNotFoundError, TurboCDIError
        assert issubclass(DomainNotFoundError, TurboCDIError)
    
    def test_navigation_error(self):
        """NavigationError is a TurboCDIError subclass"""
        from core.errors import NavigationError, TurboCDIError
        assert issubclass(NavigationError, TurboCDIError)
    
    def test_validation_error(self):
        """ValidationError is a TurboCDIError subclass"""
        from core.errors import ValidationError, TurboCDIError
        assert issubclass(ValidationError, TurboCDIError)


class TestLogger:
    """Test logging system"""
    
    def test_logger_imports(self):
        """Logger module can be imported"""
        from core.logger import setup_logger
        assert callable(setup_logger)
    
    def test_logger_creates_logger(self):
        """setup_logger returns a logger instance"""
        from core.logger import setup_logger
        import logging
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
    
    def test_logger_creates_log_directory(self):
        """Logger creates ~/.turbo-cdi/logs/ directory"""
        from core.logger import setup_logger
        log_dir = Path.home() / '.turbo-cdi' / 'logs'
        assert log_dir.exists()
    
    def test_logger_has_handlers(self):
        """Logger has both console and file handlers"""
        from core.logger import setup_logger
        logger = setup_logger("test_handlers")
        assert len(logger.handlers) >= 2  # Console + File


class TestCoreImports:
    """Test core module imports"""
    
    def test_meta_prime_engine_imports(self):
        """MetaPrimeEngine classes can be imported"""
        from core.meta_prime_engine import (
            MetaPrimeAPI, C4State, TimeAxis, ScaleAxis, AgencyAxis,
            PentadOperation, SeptetObject
        )
        assert MetaPrimeAPI is not None
    
    def test_domain_profiles_import(self):
        """Domain profiles can be imported"""
        from data.domain_profiles import ALL_DOMAINS, get_profile
        assert isinstance(ALL_DOMAINS, dict)
        assert callable(get_profile)


class TestCLI:
    """Test CLI functionality"""
    
    def test_cli_imports(self):
        """CLI module exists and is executable"""
        cli_path = Path(__file__).parent.parent / "turbo-cdi"
        assert cli_path.exists()
        assert cli_path.stat().st_mode & 0o111  # Executable
