#!/usr/bin/env python3
"""
Runner script for Pitch to Shot List Pipeline
Generates content from initial pitch through to final shot lists
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add pipelines to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipelines.pitch_to_shotlist import PitchToShotlistPipeline

# Load environment variables
load_dotenv()


def main():
    """Main entry point for pitch to shot list pipeline"""
    parser = argparse.ArgumentParser(
        description="Pitch to Shot List Pipeline - 5-stage content generation"
    )
    parser.add_argument(
        "--config",
        default="configs/pitch_to_shotlist.yaml",
        help="Path to configuration file (default: configs/pitch_to_shotlist.yaml)"
    )
    parser.add_argument(
        "--start-from-stage",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="Start from specific stage (default: 1)"
    )

    args = parser.parse_args()

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("Please set it in your .env file or environment variables")
        print("\nExample .env file:")
        print("ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    # Check for config file
    if not Path(args.config).exists():
        print(f"❌ Error: Config file not found: {args.config}")
        print("\nExpected config file at: configs/pitch_to_shotlist.yaml")
        print("Please create the config file with your input variables")
        sys.exit(1)

    # Run pipeline
    try:
        pipeline = PitchToShotlistPipeline(args.config, args.start_from_stage)
        pipeline.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()