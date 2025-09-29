# Giant Content Pipeline - Local

## Overview
A modular, extensible content pipeline system for generating video production assets. The system is designed to support multiple independent pipelines that can be run individually, with each pipeline handling a specific part of the content generation process.

## Implemented Pipelines

### 1. Pitch to Shot List Pipeline
Generates content from initial pitch through to final shot lists via 6 stages:
- Stage 1-5: Script generation and processing
- Stage 6: Character extraction for voice mapping

### 2. Audio Generation Pipeline (Planned)
Processes shot lists to generate dialogue and sound effects with refined timing:
- ElevenLabs TTS for dialogue (with 10-second limit enforcement)
- ElevenLabs Sound Effects generation
- Waveform-based timing refinement using Claude

## Architecture

### Modular Pipeline System
The system is built with a modular architecture that allows for:
- Multiple independent pipelines that can be run separately
- Each pipeline has its own configuration file
- Abstract base class for common functionality
- Easy addition of new pipelines for different content generation tasks

### Pitch to Shot List Pipeline
This pipeline consists of 6 stages, using Claude Opus (claude-opus-4-1-20250805):

1. **Pitch Generation** → Generates episode title and pitch paragraph
2. **Script Writing** → Creates full script from pitch
3. **Script SFX/Dialogue Tagging** → Adds sound effect annotations
4. **Script Blocking/Props** → Adds visual staging details in Fountain format
5. **Shot List Creation** → Breaks scenes into individual animated shots
6. **Character Extraction** → Extracts unique characters for voice mapping

### Data Flow
```
User Config (YAML)
    ↓
[Stage 1: Pitch] → outputs: episode_title, pitch_paragraph
    ↓
[Stage 2: Script] → outputs: script
    ↓
[Stage 3: SFX Tags] → outputs: script_tagged
    ↓
[Stage 4: Blocking] → outputs: script_blocking (Fountain format)
    ↓
[Stage 5: Shot Lists] → outputs: shot_list per scene + final compilation
```

## Configuration

### Pipeline-Specific Configuration
Each pipeline has its own YAML configuration file in the `configs/` directory.

For the Pitch to Shot List pipeline (`configs/pitch_to_shotlist.yaml`):
```yaml
# Core content inputs
bible: "Full project bible text..."
pitch_user_message: "User instructions for pitch"
script_user_message: "User instructions for script"

# Kiddo instruction modes (for both pitch and script)
kiddo_pitch_instruction:
  mode: "append"  # Options: "preset", "append", "null"
  append_text: "Additional instructions if mode is append"

kiddo_script_instruction:
  mode: "preset"  # Options: "preset", "append", "null"
  append_text: ""  # Only used if mode is "append"
```

### Kiddo Instruction Logic
Three modes for handling special instructions:
- **preset**: Use predefined instruction string from the system
- **append**: Use predefined string + append custom text
- **null**: No special instruction

## Implementation Details

### Technology Stack
- **Language**: Python
- **Config Format**: YAML (per pipeline)
- **Output Format**: JSON (with optional human-readable copies)
- **APIs**: Anthropic SDK (with support for other APIs in future pipelines)
- **Authentication**: .env file with API keys

### File Structure
```
giant-content-pipeline-local/
├── .env                              # API keys
├── .env.example                      # API key template
├── .gitignore                        # Git ignore rules
├── run_pitch_to_shotlist.py          # Runner for pitch->shotlist pipeline
├── pipelines/                        # Pipeline implementations
│   ├── __init__.py
│   ├── base_pipeline.py              # Abstract base class
│   └── pitch_to_shotlist.py          # 5-stage pipeline
├── configs/                          # Pipeline configurations
│   └── pitch_to_shotlist.yaml       # Config for 5-stage pipeline
├── outputs/                          # Generated content (gitignored)
│   └── pitch_to_shotlist_YYYY-MM-DD_HH-MM-SS/
│       ├── 01_pitch.json
│       ├── 02_script.json
│       ├── 03_script_tagged.json
│       ├── 04_script_blocking.json
│       ├── 05_shot_list_scene_01.json
│       ├── 05_shot_list_scene_02.json
│       ├── 05_shot_list_final.json
│       ├── config.yaml               # Copy of input config
│       └── summary.txt               # Human-readable overview
└── archive/                          # Reference materials (optional)
    └── llm-pipeline/                 # Original API call templates
```

## Special Processing: Shot List Stage

The shot list stage is the most complex, requiring special handling:

### Scene Splitting
1. Parse the Fountain-formatted script from Stage 4
2. Split by scene headings (regex pattern: `^(INT\.|EXT\.).*$`)
3. Process each scene individually

### Iterative API Calls
For each scene:
1. Pass the scene to the API along with:
   - The bible
   - Full script_blocking for context
   - Previous shot lists (for continuity)
2. Store individual scene shot list
3. Append to cumulative previous_shot_lists

### Final Output
- Individual shot list files per scene
- Consolidated shot list with all shots grouped by scene

## Variable Mapping

### Stage 1: Pitch
**Inputs:**
- `{{bible}}` - from config.yaml
- `{{kiddo_pitch_instruction}}` - computed from mode logic
- `{{pitch_user_message}}` - from config.yaml

**Outputs** (extracted from API response):
- `{{episode_title}}`
- `{{pitch_paragraph}}`

### Stage 2: Script
**Inputs:**
- `{{bible}}` - from config.yaml
- `{{kiddo_script_instruction}}` - computed from mode logic
- `{{episode_title}}` - from Stage 1
- `{{pitch_paragraph}}` - from Stage 1
- `{{script_user_message}}` - from config.yaml

**Outputs:**
- `{{script}}`

### Stage 3: Script SFX/Dialogue
**Inputs:**
- `{{bible}}` - from config.yaml
- `{{script}}` - from Stage 2

**Outputs:**
- `{{script_tagged}}`

### Stage 4: Script Blocking/Props
**Inputs:**
- `{{bible}}` - from config.yaml
- `{{script_tagged}}` - from Stage 3

**Outputs:**
- `{{script_blocking}}` - Fountain-formatted script

### Stage 5: Shot Lists
**Inputs** (per scene):
- `{{bible}}` - from config.yaml
- `{{script_blocking}}` - from Stage 4
- `{{previous_shot_lists}}` - accumulated from prior scenes
- `{{shot_list_scene}}` - current scene being processed

**Outputs:**
- `{{shot_list}}` - for each scene
- Final consolidated shot list

## Error Handling & Recovery

### Checkpoint System
- Each stage output is saved immediately
- Pipeline can resume from any failed stage
- Previous outputs are cached and reusable

### Validation
- Verify required variables are present before each stage
- Check API responses for expected output format
- Log all API calls and responses for debugging

## Running Pipelines

### Pitch to Shot List Pipeline

```bash
# Set up environment
cp .env.example .env
# Edit .env with your actual ANTHROPIC_API_KEY

# Configure your content
edit configs/pitch_to_shotlist.yaml

# Run the pipeline
python run_pitch_to_shotlist.py

# Or run from specific stage (if recovering from failure)
python run_pitch_to_shotlist.py --start-from-stage 3

# For help
python run_pitch_to_shotlist.py --help
```

### Adding New Pipelines

1. Create a new pipeline class in `pipelines/` that inherits from `BasePipeline`
2. Create a configuration file in `configs/`
3. Create a runner script in the root directory
4. Each pipeline runs independently with its own configuration

## Key Design Principles

1. **Modularity**: Each pipeline is independent and self-contained
2. **Extensibility**: Easy to add new pipelines without affecting existing ones
3. **Simplicity**: Minimal dependencies, straightforward flow
4. **Debuggability**: Clear file outputs, readable formats
5. **Recoverability**: Can restart from any stage
6. **Observability**: All inputs/outputs are inspectable
7. **Local-first**: Everything runs and stores locally

## Critical Constraints

### Audio Generation
- **10-Second Dialogue Limit**: Dialogue automatically compressed if exceeding 10 seconds
- **Voice Mapping**: Requires ElevenLabs voice IDs for each character
- **Timing Refinement**: Uses waveform analysis for precise SFX placement

## Notes

- The model specified (claude-opus-4-1-20250805) must be used for all API calls
- All prompts should remain unchanged from the template files
- Output parsing must handle the exact format returned by the API
- Scene splitting for shot lists uses Fountain screenplay format conventions