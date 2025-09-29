# Memory Compaction - Audio Pipeline Development

## Current Focus: Building Audio Generation Pipeline
We're implementing the second major pipeline that takes shot lists from `pitch_to_shotlist` and generates audio (dialogue + SFX) with refined timing for video production.

## System Architecture Overview

### Complete Pipeline Flow
```
1. pitch_to_shotlist (COMPLETE)
   └─> 6 stages: pitch → script → SFX tags → blocking → shot lists → character extraction
   └─> Outputs: shot lists + character list for voice mapping

2. audio_generation (IN PROGRESS - THIS IS WHERE WE ARE)
   └─> Takes shot list JSON from pipeline 1
   └─> Generates audio files with ElevenLabs
   └─> Enforces 10-second dialogue limit
   └─> Refines SFX timing using waveform analysis

3. [Future pipelines for video generation]
```

## Audio Pipeline - Detailed Current Work

### Critical Requirements We're Implementing
1. **10-SECOND HARD LIMIT on dialogue** (for video generation compatibility)
2. **Two audio sources**: ElevenLabs TTS for dialogue, ElevenLabs SFX for sound effects
3. **Waveform-based timing refinement** using Claude to analyze visual representations

### The Audio Pipeline Process (What We're Building Now)

#### Stage 1: Audio Generation with Compression
```python
For each shot:
  1. Generate dialogue with ElevenLabs TTS (model: eleven_turbo_v2_5)
  2. Check duration with librosa
  3. If > 10 seconds:
     - Send to Claude dialogue compressor API
     - Regenerate with compressed text
     - Repeat until ≤ 10 seconds (max 5 iterations)
  4. Generate SFX with ElevenLabs Sound Effects API
  5. Save: shot_001_dialogue.mp3, shot_001_sfx_1.mp3, etc.
  6. Store duration metadata
```

#### Stage 2: Waveform Generation
- Convert audio to Unicode visualization: ▁▂▃▄▅▆▇█
- 40 characters representing amplitude over time
- Used for visual timing analysis by Claude

#### Stage 3: Timing Refinement
- Send waveforms + dialogue text to Claude
- Claude analyzes where words occur in waveform
- Returns refined timing percentages for SFX placement
- Updates shot list with new timings

### Key Files & APIs We're Working With

#### ElevenLabs Integration
- **TTS**: `elevenlabs.text_to_speech.convert()` with voice_id mapping
- **SFX**: `elevenlabs.text_to_sound_effects.convert()` with text descriptions
- **Model**: Always using `eleven_turbo_v2_5` for TTS

#### Claude APIs
1. **Dialogue Compressor** (`dialogue-compressor-api-call.py`)
   - Input: `{"shot_number": X, "dialogue": "text"}`
   - Output: `{"shot_number": X, "rewritten_dialogue": "shorter text"}`
   - Preserves [bracketed] TTS annotations

2. **SFX Timing Refiner** (`sfx_timing_updater_api_call.py`)
   - Input: Dialogue waveform + SFX waveforms + text
   - Output: Refined timing percentages for each SFX
   - Analyzes visual waveform patterns to place sounds naturally

### Configuration Structure
```yaml
# configs/audio_generation.yaml (needs to be created)
voice_mappings:
  MILO: "voice_id_here"
  SEBBY: "voice_id_here"
  COMPUTER: "voice_id_here"
  DEFAULT: "default_voice_id"

model_id: "eleven_turbo_v2_5"
dialogue_output_format: "mp3_44100_128"
max_dialogue_duration: 10  # seconds - HARD LIMIT
```

### Character Extraction (Added to pitch_to_shotlist)
- Stage 6 now extracts unique characters
- Outputs `06_character_list.json` with character names
- Creates `06_voice_config_template.yaml` for easy voice ID mapping

## Implementation Status

### ✅ Completed
- Modular pipeline architecture (base class + implementations)
- pitch_to_shotlist pipeline (6 stages)
- Character extraction for voice mapping
- Requirements.txt with all dependencies
- Architecture documentation

### 🚧 In Progress (Current Task)
- Audio generation pipeline implementation
- Dialogue compression logic with retry
- Waveform processor using librosa
- Integration with ElevenLabs APIs

### 📋 Next Steps
1. Create `pipelines/audio_generation.py` main pipeline
2. Implement `dialogue_compressor.py` with iteration logic
3. Build `waveform_processor.py` for audio → Unicode
4. Set up `timing_refiner.py` for Claude analysis
5. Create runner script `run_audio_generation.py`

## Critical Details to Preserve

### Dialogue Compression Logic
```python
while duration > 10 and iterations < 5:
    1. Call Claude compressor API
    2. Get compressed text
    3. Regenerate audio
    4. Check duration again
    5. Store both original and final text
```

### Waveform Processing
- 40 Unicode characters per audio file
- Consistent time scale across dialogue and SFX
- Characters: ▁▂▃▄▅▆▇█ (quiet to loud)

### File Naming Convention
- `shot_XXX_dialogue.mp3` (3-digit shot number)
- `shot_XXX_sfx_N.mp3` (multiple SFX per shot)
- Duration and compression status stored in JSON

## Key Decisions Made
1. **Separate pipeline** (not extending pitch_to_shotlist) for clean separation
2. **Iterative compression** to handle 10-second limit gracefully
3. **Waveform visualization** for Claude to understand audio spatially
4. **Character extraction** as Stage 6 of first pipeline (not separate)

## Dependencies Added
- elevenlabs (TTS + SFX)
- librosa (audio analysis + duration)
- soundfile, numpy (audio processing)

## Project Structure Context
```
pipelines/
  pitch_to_shotlist.py (COMPLETE - 6 stages)
  audio_generation.py (BUILDING NOW)
  dialogue_compression_example.py (reference implementation)

configs/
  pitch_to_shotlist.yaml (user's content config)
  audio_generation.yaml (TO CREATE - voice mappings)

generate-sfx-dialogue-timing/ (reference files)
  eleven-labs-docs-*.md
  dialogue-compressor-api-call.py
  sfx_timing_updater_api_call.py
  waveform-step-instruction.txt
```

## IMPORTANT: Continue From Here
We're actively building the audio generation pipeline. The architecture is designed, character extraction is added to pipeline 1, and we need to implement the actual audio generation with dialogue compression, waveform processing, and timing refinement. The 10-second limit is CRITICAL and must be enforced through iterative compression.