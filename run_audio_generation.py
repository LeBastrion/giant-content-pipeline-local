#!/usr/bin/env python3
"""
Audio Generation Pipeline Runner
Processes shot lists to generate dialogue and sound effects
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pipelines.audio_generation import AudioGenerationPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Generate audio (dialogue + SFX) from shot lists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate audio from latest pitch_to_shotlist run:
  python run_audio_generation.py --shot-list outputs/pitch_to_shotlist_*/05_shot_list_final.json

  # Use specific config:
  python run_audio_generation.py --shot-list path/to/shots.json --config configs/audio_generation.yaml

  # Resume from specific stage:
  python run_audio_generation.py --shot-list path/to/shots.json --start-from-stage 2

Notes:
  - Requires ELEVENLABS_API_KEY in .env or config
  - Requires voice_mappings in config for character voices
  - Enforces 10-second dialogue limit through compression
        """
    )

    parser.add_argument(
        "--shot-list",
        required=False,
        default=None,
        help="Path to shot list JSON (overrides config file setting)"
    )

    parser.add_argument(
        "--config",
        default="configs/audio_generation.yaml",
        help="Path to audio generation config file (default: configs/audio_generation.yaml)"
    )

    parser.add_argument(
        "--start-from-stage",
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
        help="Start from a specific stage (1: audio generation, 2: waveforms, 3: timing refinement, 4: audio mixing)"
    )

    args = parser.parse_args()

    # Load config to get shot_list_path if not provided via CLI
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        print("\nPlease create configs/audio_generation.yaml")
        sys.exit(1)

    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Determine shot list path (CLI flag overrides config)
    if args.shot_list:
        shot_list_pattern = args.shot_list
    elif config.get('shot_list_path'):
        shot_list_pattern = config['shot_list_path']
    else:
        print("ERROR: No shot list path specified")
        print("Provide via --shot-list flag or set shot_list_path in config file")
        sys.exit(1)

    # Handle wildcard patterns
    from glob import glob
    matching_files = glob(shot_list_pattern)

    if not matching_files:
        print(f"ERROR: No shot list found matching: {shot_list_pattern}")

        # Try to find the latest shot list
        outputs_dir = Path("outputs")
        if outputs_dir.exists():
            shot_lists = list(outputs_dir.glob("pitch_to_shotlist_*/05_shot_list_final.json"))
            if shot_lists:
                latest = max(shot_lists, key=lambda p: p.stat().st_mtime)
                print(f"\nLatest available shot list: {latest}")
                print(f"Update your config or use: --shot-list {latest}")
        sys.exit(1)

    # Use the most recent file if multiple matches
    shot_list_path = Path(max(matching_files, key=lambda p: Path(p).stat().st_mtime))

    if not shot_list_path.exists():
        print(f"ERROR: Shot list not found: {shot_list_path}")
        sys.exit(1)

    print(f"Using shot list: {shot_list_path}")

    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not found in environment")
        print("Please add to .env file")
        sys.exit(1)

    if not os.getenv("ELEVENLABS_API_KEY"):
        print("WARNING: ELEVENLABS_API_KEY not found in environment")
        print("Will try to use key from config file if provided")

    # Run the pipeline
    try:
        pipeline = AudioGenerationPipeline(
            config_path=str(config_path),
            shot_list_path=str(shot_list_path),
            start_stage=args.start_from_stage
        )

        pipeline.run()

    except Exception as e:
        print(f"\nERROR: Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()