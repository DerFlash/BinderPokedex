"""
Base class for pipeline steps.

Each step in the pipeline inherits from BaseStep and implements
the execute() method to perform its specific transformation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class PipelineContext:
    """
    Context object passed between pipeline steps.
    Contains the data and metadata for the current pipeline run.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.data: Dict[str, Any] = {}  # Initialize as empty dict instead of None
        self.target_file = config.get('target_file')  # Final pipeline output for documentation
        self.metadata: Dict[str, Any] = {}
        self.storage: Dict[str, Any] = {}  # For storing enrichment data like metadata, translations, etc.
    
    def set_data(self, data: Dict[str, Any]):
        """Set the current data."""
        self.data = data
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get the current data."""
        return self.data
    
    def set_metadata(self, key: str, value: Any):
        """Store metadata about the pipeline execution."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str) -> Any:
        """Retrieve metadata."""
        return self.metadata.get(key)


class BaseStep(ABC):
    """
    Base class for all pipeline steps.
    
    Each step receives a context and parameters, performs its operation,
    and updates the context with the result.
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the step.
        
        Args:
            context: The pipeline context with current data
            params: Step-specific parameters from config
        
        Returns:
            Updated context with transformed data
        """
        pass
    
    def __str__(self):
        return f"{self.__class__.__name__}('{self.name}')"
