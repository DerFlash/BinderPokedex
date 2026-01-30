"""
Pipeline Engine for executing step-based data transformations.

The engine loads a configuration, executes pipeline steps in sequence,
and handles errors gracefully.
"""

import sys
from typing import Dict, List, Type
from pathlib import Path

from steps.base import BaseStep, PipelineContext


class StepRegistry:
    """Registry for all available pipeline steps."""
    
    def __init__(self):
        self._steps: Dict[str, Type[BaseStep]] = {}
    
    def register(self, step_name: str, step_class: Type[BaseStep]):
        """Register a step class with a name."""
        self._steps[step_name] = step_class
    
    def get(self, step_name: str) -> Type[BaseStep]:
        """Get a step class by name."""
        if step_name not in self._steps:
            raise ValueError(f"Unknown step: {step_name}")
        return self._steps[step_name]
    
    def list_steps(self) -> List[str]:
        """List all registered step names."""
        return list(self._steps.keys())


class PipelineEngine:
    """
    Executes a pipeline of steps defined in a config.
    
    Each step is executed sequentially, passing the context between steps.
    If a step fails, the pipeline stops and an error is reported.
    """
    
    def __init__(self, config: dict, registry: StepRegistry):
        self.config = config
        self.registry = registry
        self.context = PipelineContext(config)
    
    def execute(self) -> bool:
        """
        Execute the entire pipeline.
        
        Returns:
            True if successful, False if any step failed
        """
        pipeline_steps = self.config.get('pipeline', [])
        
        if not pipeline_steps:
            print("⚠️  No pipeline steps defined")
            return False
        
        print(f"\n🚀 Starting pipeline with {len(pipeline_steps)} steps\n")
        
        for i, step_config in enumerate(pipeline_steps, 1):
            step_name = step_config.get('step')
            params = step_config.get('params', {})
            
            if not step_name:
                print(f"❌ Step {i}: Missing 'step' field in config")
                return False
            
            try:
                # Get step class from registry
                step_class = self.registry.get(step_name)
                
                # Create step instance
                step = step_class(step_name)
                
                # Execute step with params
                print(f"[{i}/{len(pipeline_steps)}] Executing: {step_name}")
                self.context = step.execute(self.context, params)
                print(f"    ✅ Completed\n")
                
            except ValueError as e:
                print(f"❌ Step {i} ({step_name}): {e}")
                return False
            except Exception as e:
                print(f"❌ Step {i} ({step_name}) failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Note: Steps are responsible for writing their own output files
        # The engine only saves to target_file if explicitly needed
        # (e.g., for backward compatibility with pokedex scope)
        if self.config.get('save_final_output', False) and self.context.target_file and self.context.get_data():
            import json
            from pathlib import Path
            
            target_path = Path(self.context.target_file)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self.context.get_data(), f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved final output to: {self.context.target_file}")
        
        print("✅ Pipeline completed successfully!")
        return True
    
    def get_context(self) -> PipelineContext:
        """Get the current pipeline context."""
        return self.context
