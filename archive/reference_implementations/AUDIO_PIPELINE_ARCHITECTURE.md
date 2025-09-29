# Audio Generation Pipeline Architecture

## Overview
This is a separate pipeline that takes the shot list output from `pitch_to_shotlist` and generates audio (dialogue + SFX) with refined timing.

## Why a Separate Pipeline?
1. **Different APIs**: Uses ElevenLabs instead of Anthropic
2. **Complex Processing**: Audio waveform analysis and timing refinement
3. **Configurable Voices**: Requires character-to-voice-ID mapping
4. **Independence**: Can re-run audio generation without re-generating scripts

## Pipeline Flow

### Stage 1: Character Extraction (Added to pitch_to_shotlist)
- Extract unique characters from final shot list
- Save as `06_character_list.json`
- Format:
```json
{
  "characters": [
    {"name": "MILO", "voice_id": null},
    {"name": "SEBBY", "voice_id": null},
    {"name": "COMPUTER", "voice_id": null}
  ]
}
```

### Stage 2: Audio Generation Pipeline (New Pipeline)

#### Input Requirements
1. Shot list JSON from pitch_to_shotlist pipeline
2. Character voice mapping config:
```yaml
# configs/audio_generation.yaml
elevenlabs_api_key: "your_key_here"  # Or use .env
model_id: "eleven_turbo_v2_5"  # Using v3 as specified

voice_mappings:
  MILO: "voice_id_1"
  SEBBY: "voice_id_2"
  COMPUTER: "voice_id_3"
  DEFAULT: "default_voice_id"  # For unnamed characters

sfx_duration_limit: 5  # Max seconds for SFX
dialogue_output_format: "mp3_44100_128"
```

#### Processing Stages

**Stage 1: Audio Generation with Dialogue Compression**
- For each shot in shot list:
  - Generate dialogue audio via ElevenLabs TTS (if dialogue exists)
  - **Check dialogue duration:**
    - If > 10 seconds:
      1. Send to Claude dialogue compressor API
      2. Get compressed dialogue text
      3. Regenerate audio with compressed text
      4. Repeat until ≤ 10 seconds
    - Store final dialogue text (may differ from original)
  - Generate SFX audio via ElevenLabs SFX (for each sound effect)
  - Save files: `shot_001_dialogue.mp3`, `shot_001_sfx_1.mp3`, etc.
  - **Capture and store audio durations**

**Stage 2: Waveform Generation**
- Convert each audio file to waveform representation
- Use librosa to:
  - Load audio → mono
  - Get audio duration in seconds
  - Segment into 40 chunks (consistent time scale)
  - Calculate RMS amplitude per chunk
  - Map to Unicode characters: ▁▂▃▄▅▆▇█

**Stage 3: Timing Refinement**
- For each shot with SFX:
  - Create alignment view with waveforms
  - Call Claude API to analyze and refine timing
  - Update timing percentages

**Stage 4: Output Generation**
- Enhanced shot list with:
  - Audio file paths
  - Audio durations (seconds)
  - Final dialogue text (potentially compressed)
  - Refined SFX timings
  - Waveform representations

## File Structure
```
audio_generation/
  ├── __init__.py
  ├── audio_generator.py       # Main pipeline
  ├── dialogue_compressor.py   # Claude-based dialogue compression
  ├── waveform_processor.py    # Audio → waveform conversion
  └── timing_refiner.py        # Claude-based timing refinement

configs/
  └── audio_generation.yaml    # Voice mappings & settings

outputs/
  └── audio_generation_YYYY-MM-DD/
      ├── audio/
      │   ├── shot_001_dialogue.mp3
      │   ├── shot_001_sfx_1.mp3
      │   └── ...
      ├── 01_audio_generated.json     # Includes durations & compression status
      ├── 02_waveforms.json
      ├── 03_refined_timings.json
      └── enhanced_shot_list.json      # Final output with all metadata
```

## Integration Points

### Option 1: Extend pitch_to_shotlist (NOT RECOMMENDED)
- Pros: Single pipeline
- Cons: Mixes concerns, harder to maintain, can't re-run audio separately

### Option 2: Separate Pipeline (RECOMMENDED)
- Pros: Clean separation, independent execution, easier testing
- Cons: Requires passing data between pipelines

### Character List Generation
Add to `pitch_to_shotlist.py` after stage 5:
```python
def extract_characters(self):
    """Extract unique characters from shot lists"""
    characters = set()
    for scene in self.variables.get("all_shot_lists", []):
        for shot in scene.get("shot_list", {}).get("shots", []):
            if shot.get("character") and shot["character"] != "none":
                characters.add(shot["character"])

    return [{"name": char, "voice_id": None} for char in sorted(characters)]
```

## Critical Constraints

### 10-Second Dialogue Limit
- **Hard requirement**: No dialogue can exceed 10 seconds
- **Reason**: Video generation pipeline limitation
- **Solution**: Automatic dialogue compression via Claude
- **Process**:
  1. Generate initial audio
  2. Check duration using librosa
  3. If > 10 seconds → compress text → regenerate
  4. Iterate until ≤ 10 seconds
  5. Store both original and compressed versions

## Next Steps
1. ✓ Add character extraction to pitch_to_shotlist pipeline
2. Create audio_generation pipeline module
3. Implement dialogue compressor with retry logic
4. Implement waveform processor with duration capture
5. Set up ElevenLabs integration
6. Create timing refinement with Claude