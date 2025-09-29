# Memory Compaction - Complete Pipeline State & Implementation Details

## Project Overview
**Giant Content Pipeline** - A modular video production pipeline system that generates content from pitch to final mixed audio, designed for automated short-form video creation with strict 10-second shot limits.

## Architecture: Two Independent Pipelines

### Pipeline 1: pitch_to_shotlist (COMPLETE)
Transforms initial pitch into shot lists through 6 stages:
1. **Pitch Generation** → episode title + pitch paragraph
2. **Script Writing** → full script from pitch
3. **SFX Tagging** → adds sound effect annotations
4. **Blocking/Props** → Fountain format with staging
5. **Shot Lists** → breaks into individual shots per scene
6. **Character Extraction** → unique characters for voice mapping

**Critical Details:**
- Uses Claude Opus (claude-opus-4-1-20250805)
- Scene splitting: regex `^(INT\.|EXT\.).*$`
- Outputs to `outputs/pitch_to_shotlist_YYYY-MM-DD_HH-MM-SS/`
- NEW FORMAT: `sound_effects` is now array of strings, NOT objects with timing

### Pipeline 2: audio_generation (COMPLETE with 4 stages)
Processes shot lists to generate mixed audio:

#### Stage 1: Audio Generation
- **Dialogue**: ElevenLabs TTS using model "eleven_v3"
- **10-SECOND LIMIT**: Iterative compression via Claude if >10s (max 5 attempts)
- **Parenthetical Stripping**: Removes `()` but KEEPS `[]` for TTS
- **Skips "none" character** - no API call if character="none"
- **SFX Generation**: NO duration_seconds parameter - let ElevenLabs decide
- `prompt_influence=0.9` for better adherence
- **Retry logic**: 3 attempts with 2s delay on timeout

#### Stage 2: Waveform Generation
- 40 Unicode characters: ▁▂▃▄▅▆▇█
- Handles missing/empty files gracefully
- Returns flat waveform on error

#### Stage 3: Timing Refinement
- Claude analyzes waveforms to place SFX
- **NO timing from shot list** - only generated here
- Default 50% if refinement fails
- Output: `refined_timing_percentage` for each SFX

#### Stage 4: Audio Mixing (NEW)
- **Target**: 10-second clips MAXIMUM
- **Dialogue centered** in 10s window (configurable)
- **SFX at 70% volume** (configurable)
- **Percentage-based timing**:
  - 50% = SFX starts at dialogue midpoint
  - -50% = SFX starts 50% of dialogue duration BEFORE dialogue
- **Trimming logic**:
  - Trim SFX head if starts < 0
  - Trim SFX tail if extends > 10s
  - NEVER cut dialogue
- Output: `shot_XXX_combined.mp3`

## Critical Bug Fixes Implemented

### 1. Compression File Saving Bug (FIXED)
**Problem**: Wrong audio file saved after compression - showed 7.4s in JSON but actual file was 1.1s
**Cause**: Temp files deleted before moving
**Solution**: Track `successful_temp_path` and only move at end

### 2. SFX Format Change (IMPLEMENTED)
**Old format**: `[{sfx: "text", timing: 50}]`
**New format**: `["{{SFX: text}}"]` - simple string array
**Handling**: Strip `{{SFX: }}` wrapper, no timing expected from shot list

### 3. Configuration Structure
```yaml
# configs/audio_generation.yaml
shot_list_path: "outputs/pitch_to_shotlist_*/05_shot_list_final.json"  # Wildcards work!

voice_mappings:
  CHARACTER_NAME: "elevenlabs_voice_id"
  DEFAULT: "default_voice_id"

model_id: "eleven_v3"  # NOT eleven_turbo_v2_5!
max_dialogue_duration: 10

testing:
  scene_limit: 2  # Process only first N scenes
  max_shots: 10   # Or first N shots total

mixing:
  sfx_volume: 0.7
  target_duration: 10
  center_dialogue: true

sfx_settings:
  prompt_influence: 0.9  # NOT 0.3!
```

## File Structure
```
pipelines/
  audio_generation.py  # 4-stage pipeline with mixing
  pitch_to_shotlist.py # 6-stage pipeline
configs/
  audio_generation.yaml  # Voice mappings + settings
  pitch_to_shotlist.yaml # Content configuration
outputs/
  audio_generation_*/
    audio/
      shot_XXX_dialogue.mp3
      shot_XXX_sfx_N.mp3
      shot_XXX_combined.mp3  # NEW: Mixed audio
    01_audio_generated.json
    02_waveforms.json
    03_refined_timings.json
    04_mixed_audio.json  # NEW
    debug_log.json  # Compression attempts + stats
    enhanced_shot_list.json  # Updated dialogue for lip-sync
```

## Key Implementation Details

### Audio Mixing Math (Stage 4)
```python
# Dialogue centered in 10s:
dialogue_start_ms = (10000 - dialogue_duration_ms) / 2

# SFX placement:
sfx_start_relative_ms = (timing_pct / 100.0) * dialogue_duration_ms
sfx_start_absolute_ms = dialogue_start_ms + sfx_start_relative_ms

# Negative timing example:
# -50% on 4s dialogue = starts 2s before dialogue
```

### Error Recovery
- Can restart from any stage: `--start-from-stage N`
- Missing files handled gracefully
- Default timings if refinement fails
- Debug log tracks all operations

### API Keys Required
- `ANTHROPIC_API_KEY` in .env
- `ELEVENLABS_API_KEY` in .env

## Current State
- Both pipelines COMPLETE and tested
- Audio mixing (Stage 4) just added
- Ready for full pipeline run
- All bugs fixed:
  - Compression file saving ✓
  - "none" character handling ✓
  - SFX retry logic ✓
  - New shot list format ✓
  - Mixing implementation ✓

## Running the Pipelines
```bash
# Pitch to shot list:
python run_pitch_to_shotlist.py

# Audio generation (reads shot_list_path from config):
python run_audio_generation.py

# Or with limits for testing:
# Edit configs/audio_generation.yaml:
# testing:
#   scene_limit: 2
#   max_shots: 10
```

## Critical Things to Remember
1. **Model is "eleven_v3"** not eleven_turbo_v2_5
2. **SFX have NO duration limit** - natural length
3. **Timing ONLY from audio pipeline** - not shot list
4. **10-second HARD LIMIT** on final mixed audio
5. **Dialogue compression is ITERATIVE** - up to 5 attempts
6. **Enhanced shot list** contains compressed dialogue for lip-sync
7. **Debug log** has all compression attempts and file sizes
8. **Mixed audio** in Stage 4 creates shot_XXX_combined.mp3

## Next Conversation Context
User is about to run full pipeline. Expecting:
- Possible timeout issues with many shots
- Need to verify mixed audio works correctly
- May need to adjust timing percentages
- Watch for any edge cases in mixing logic

## Dependencies
- pydub (NEW for mixing)
- librosa, soundfile, numpy
- elevenlabs, anthropic
- ffmpeg (system - for pydub)

This system generates complete audio tracks for video production with precise timing and 10-second limits.