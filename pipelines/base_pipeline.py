"""
Base Pipeline Class
Abstract base class for all content generation pipelines
"""

import os
import json
import yaml
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class BasePipeline(ABC):
    """
    Abstract base class for all pipelines.
    Provides common functionality for configuration, output management, and execution flow.
    """

    def __init__(self, config_path: str, pipeline_name: str, start_stage: int = 1):
        """
        Initialize base pipeline with common setup.

        Args:
            config_path: Path to YAML configuration file
            pipeline_name: Name of the pipeline (used for output directory)
            start_stage: Stage number to start from (for recovery)
        """
        self.config = self._load_config(config_path)
        self.pipeline_name = pipeline_name
        self.start_stage = start_stage
        self.run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Create output directory for this pipeline run
        self.output_dir = Path(f"outputs/{pipeline_name}_{self.run_timestamp}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Copy config to output directory for reference
        with open(self.output_dir / "config.yaml", "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

        # Storage for pipeline variables (data passed between stages)
        self.variables = {}

        # Track stage outputs for summary
        self.stage_outputs = []

    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration file"""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _save_output(self, stage_num: int, stage_name: str, data: Dict):
        """
        Save stage output to JSON file.

        Args:
            stage_num: Stage number for file naming
            stage_name: Name of the stage
            data: Data to save
        """
        filename = f"{stage_num:02d}_{stage_name}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  → Saved output to {filename}")

        # Track for summary
        self.stage_outputs.append({
            "stage": stage_num,
            "name": stage_name,
            "file": filename
        })

    def _load_previous_output(self, filepath: str) -> Dict:
        """
        Load output from a previous pipeline run.
        Useful for chaining pipelines manually.

        Args:
            filepath: Path to previous output JSON file

        Returns:
            Loaded JSON data
        """
        with open(filepath, "r") as f:
            return json.load(f)

    def create_summary(self):
        """
        Create a human-readable summary of the pipeline run.
        Can be overridden by specific pipelines for custom summaries.
        """
        summary = f"""{self.pipeline_name.upper()} Pipeline Run Summary
Generated: {self.run_timestamp}

Configuration File: config.yaml

Stages Completed:
"""

        for stage in self.stage_outputs:
            summary += f"  {stage['stage']}. {stage['name']} → {stage['file']}\n"

        summary += f"\nAll outputs saved to: {self.output_dir}\n"

        summary_path = self.output_dir / "summary.txt"
        with open(summary_path, "w") as f:
            f.write(summary)

        print(f"  ✓ Created summary.txt")

    @abstractmethod
    def run(self):
        """
        Execute the pipeline.
        Must be implemented by each specific pipeline.
        """
        pass

    @abstractmethod
    def get_stage_count(self) -> int:
        """
        Return the total number of stages in this pipeline.
        Used for validation and progress tracking.
        """
        pass

    def validate_config(self, required_fields: list) -> bool:
        """
        Validate that all required configuration fields are present.

        Args:
            required_fields: List of required field names

        Returns:
            True if all fields present, raises exception otherwise
        """
        missing_fields = []
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"Missing required config fields: {', '.join(missing_fields)}")

        return True

    def print_header(self, message: str):
        """Print a formatted header for pipeline stages"""
        print(f"\n{'='*50}")
        print(message)
        print(f"{'='*50}")

    def print_stage_header(self, stage_num: int, stage_name: str):
        """Print a formatted stage header"""
        print(f"\n=== Stage {stage_num}: {stage_name} ===")

    def print_success(self):
        """Print success message"""
        self.print_header(f"✅ {self.pipeline_name} Pipeline completed successfully!")
        print(f"Output saved to: {self.output_dir}")
        print(f"{'='*50}\n")

    def print_error(self, error: Exception):
        """Print error message"""
        print(f"\n❌ Pipeline failed: {str(error)}")
        print(f"Check {self.output_dir} for partial outputs")
        print(f"You can restart from the failed stage using --start-from-stage\n")