# Build Log

## Initial Setup
- Created basic folder structure for LLM pipeline with 5 stages
- Each stage has TypeScript API call structures and example files
- Created system description document outlining the video production pipeline
- Defined variables structure for pipeline inputs
- Initialized git repository and connected to GitHub remote
- Pushed initial commit to origin/main

## Architecture Planning
- Created comprehensive README as single source of truth
- Defined 5-stage pipeline architecture (Pitch → Script → SFX Tags → Blocking → Shot Lists)
- Established YAML config structure for user inputs
- Planned output folder structure with timestamped runs
- Decided on Python implementation with JSON outputs
- Defined special handling for shot list scene splitting

## Pipeline Implementation
- Built main pipeline.py orchestration script
- Created config.yaml template with all user variables
- Implemented 5-stage processing with exact prompt preservation
- Added scene splitting logic for shot lists
- Created .env.example and .gitignore files
- Documented files for archival to clean repository

## Modular Architecture Refactor
- Restructured to support multiple independent pipelines
- Created abstract BasePipeline class for common functionality
- Moved pitch-to-shotlist logic to pipelines/pitch_to_shotlist.py
- Created separate configs/ directory for pipeline configurations
- Built run_pitch_to_shotlist.py as individual runner script
- Updated README to reflect modular architecture
- Each pipeline now runs independently with own config

## Streaming & Scene Detection Fixes
- Added streaming support to prevent timeout warnings
- Fixed scene splitting logic to properly detect INT./EXT. headings
- Added cleaned text outputs for each script stage
- Added debugging outputs for scene detection
- Note: Generated scripts may have single scenes based on prompts

## Audio Pipeline Planning
- Designed separate audio generation pipeline for ElevenLabs integration
- Added character extraction to pitch_to_shotlist pipeline (stage 6)
- Created requirements.txt with audio processing dependencies
- Planned architecture for TTS and SFX generation with timing refinement
- Structured as independent pipeline to process shot list outputs
- Includes waveform visualization for Claude-based timing adjustment
- Added dialogue compression step to enforce 10-second limit
- Duration capture for all audio files using librosa
- Iterative compression until dialogue meets time constraint

## Audio Pipeline Implementation
- Using ElevenLabs model "eleven_v3" (not v2_5 as initially planned)
- Added ELEVENLABS_API_KEY to .env.example
- Implemented parenthetical stripping (remove () but keep [])
- Built modular components: compressor, waveform, timing
- Created separate pipeline inheriting from BasePipeline
- Enforcing 10-second dialogue limit with iterative compression
- Created pipelines/audio_generation.py with 3 stages:
  - Stage 1: Audio generation with dialogue compression
  - Stage 2: Waveform generation (40 Unicode chars)
  - Stage 3: SFX timing refinement via Claude
- Created run_audio_generation.py runner script
- Created configs/audio_generation.yaml template with voice mappings
- Integrated all components: dialogue compressor, waveform processor, timing refiner
- Audio files saved as: shot_XXX_dialogue.mp3, shot_XXX_sfx_N.mp3
- Outputs enhanced_shot_list.json with all metadata

## Repository Cleanup & Testing
- Archived reference implementations to archive/reference_implementations/
  - generate-sfx-dialogue-timing/ directory
  - dialogue_compression_example.py
  - test_scene_split.py
  - AUDIO_PIPELINE_ARCHITECTURE.md
  - MEMORY_COMPACTION_2.md
- Repository now contains only active pipeline code
- Clean structure with pipelines/, configs/, outputs/, and archive/
- Fixed audio_generation.py to handle actual shot list structure
- Added get_stage_count() method for BasePipeline compliance
- Fixed SFX extraction to handle sound_effects key format
- Tested both pipelines - all imports and syntax checks pass
- Successfully loads 52 shots from 4 scenes in test data

## Configuration Improvements
- Added shot_list_path to audio_generation.yaml config
- Made --shot-list flag optional in run_audio_generation.py
- Config value used by default, CLI flag overrides if provided
- Supports wildcards to auto-select most recent shot list
- Can now run simply: python3 run_audio_generation.py

## Audio Pipeline Bug Fixes & Enhancements
- **Fixed compression bug**: Audio files were being deleted prematurely, now properly saves compressed audio
- **Skip "none" character**: No longer generates dialogue for character="none", saves API calls
- **Added retry logic**: SFX generation retries up to 3 times on timeout
- **Error resilience**: Handles missing/empty audio files gracefully in waveform generation
- **Set prompt_influence=0.9**: Better SFX adherence to text descriptions
- **Enhanced shot list**: Updates dialogue with compressed versions for lip-sync
- **Debug logging**: Added debug_log.json with compression attempts and statistics
- **Testing config**: Added scene_limit and max_shots for faster testing
- **File verification**: Checks file exists and size > 0 before processing

## Audio Pipeline Stage 4 - Mixing Implementation
- **Removed SFX duration limit**: Let ElevenLabs determine natural SFX length
- **Updated SFX format**: Now handles simple array of strings from new shot list format
- **Timing generation**: Only generate timing in audio pipeline, not shot list
- **Added Stage 4**: Audio mixing and trimming to create combined 10-second clips
- **Mixing features**:
  - Centers dialogue in 10-second window (configurable)
  - SFX at 70% volume (configurable)
  - Handles negative timing (SFX before dialogue)
  - Trims SFX to fit within 10-second limit
  - Preserves dialogue integrity (never cut)
- **Output files**: shot_XXX_combined.mp3 with dialogue + SFX properly mixed
- **Added pydub dependency** for audio mixing capabilities