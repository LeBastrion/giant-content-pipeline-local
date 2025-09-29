"""
Audio Generation Pipeline
Processes shot lists to generate dialogue and sound effects with refined timing
"""

import os
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml
import anthropic
from elevenlabs import ElevenLabs
import librosa
import numpy as np
import soundfile as sf
import time
from pydub import AudioSegment
from pydub.generators import Sine

from .base_pipeline import BasePipeline


class AudioGenerationPipeline(BasePipeline):
    """
    Pipeline for generating audio from shot lists
    Includes dialogue compression, SFX generation, and timing refinement
    """

    def __init__(self, config_path: str, shot_list_path: str, start_stage: int = 1):
        """
        Initialize audio generation pipeline

        Args:
            config_path: Path to audio_generation.yaml config
            shot_list_path: Path to shot list JSON from pitch_to_shotlist pipeline
            start_stage: Which stage to start from (for recovery)
        """
        super().__init__(config_path, "audio_generation", start_stage)

        self.shot_list_path = shot_list_path
        self.shot_list_data = None

        # Initialize clients
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.elevenlabs_client = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY") or self.config.get("elevenlabs_api_key")
        )

        # Audio settings
        self.model_id = self.config.get("model_id", "eleven_v3")
        self.dialogue_output_format = self.config.get("dialogue_output_format", "mp3_44100_128")
        self.max_dialogue_duration = self.config.get("max_dialogue_duration", 10)
        self.voice_mappings = self.config.get("voice_mappings", {})

        # Testing settings
        self.scene_limit = self.config.get("scene_limit", None)  # Limit scenes for testing
        self.max_shots = self.config.get("max_shots", None)  # Limit total shots for testing

        # Create audio subdirectory
        self.audio_dir = self.output_dir / "audio"
        self.audio_dir.mkdir(exist_ok=True)

        # Debug tracking
        self.debug_log = []

    def get_stage_count(self) -> int:
        """Return the total number of stages in this pipeline"""
        return 4  # Added Stage 4 for audio mixing

    def _load_shot_list(self):
        """Load shot list data from the provided path"""
        with open(self.shot_list_path, 'r') as f:
            raw_data = json.load(f)

        # Extract shots from the nested structure
        all_shots = []
        scenes_processed = 0

        for scene_data in raw_data.get('all_shot_lists', []):
            # Apply scene limit if configured
            if self.scene_limit and scenes_processed >= self.scene_limit:
                print(f"Scene limit ({self.scene_limit}) reached, stopping shot list loading")
                break

            scene_shots = scene_data.get('shot_list', {}).get('shots', [])
            all_shots.extend(scene_shots)
            scenes_processed += 1

            # Apply shot limit if configured
            if self.max_shots and len(all_shots) >= self.max_shots:
                all_shots = all_shots[:self.max_shots]
                print(f"Shot limit ({self.max_shots}) reached")
                break

        self.shot_list_data = {'shots': all_shots}
        print(f"Loaded shot list with {len(all_shots)} shots from {scenes_processed} scenes")

        if self.scene_limit or self.max_shots:
            print(f"  (Limited by config - scene_limit: {self.scene_limit}, max_shots: {self.max_shots})")

    def _strip_parentheticals(self, dialogue: str) -> str:
        """
        Remove parentheticals (text in parentheses) but keep square brackets

        Args:
            dialogue: Original dialogue text

        Returns:
            Dialogue with parentheticals removed
        """
        # Remove anything in parentheses but keep square brackets
        cleaned = re.sub(r'\([^)]*\)', '', dialogue)
        # Clean up extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _check_audio_duration(self, audio_path: str) -> float:
        """
        Get duration of audio file in seconds

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        try:
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            return duration
        except Exception as e:
            print(f"  Warning: Could not check duration of {audio_path}: {e}")
            return 0.0

    def _compress_dialogue(self, dialogue: str, shot_number: int) -> str:
        """
        Use Claude to compress dialogue text

        Args:
            dialogue: Original dialogue text
            shot_number: Shot number for context

        Returns:
            Compressed dialogue text
        """
        message = self.anthropic_client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=32000,
            temperature=0.4,
            stream=True,
            system="""You are a dialogue rewrite specialist. You have one simple job. If a line of dialogue exceeds 10 seconds after being voiced by a tts engine, it will get sent to you and you will be responsible for rewriting it so that when it gets sent back to the tts engine it's shorter. You need to try your best not to change the meaning of the line or anything crucial because you wont have any context about how it needs to function within the content. all text in [square brackets] in the dialogue must remain unchanged (those are annotations for the tts engine and dont effect length).

Your input will the dialogue will come in as json like this:

```json
{
  "shot_number": 42,
  "dialogue": "This is the character's line of dialogue that would be spoken in the scene."
}
```

and you will respond with the rewritten dialogue like this:

```json
{
  "shot_number": 42,
  "rewritten_dialogue": "This is the character's line of dialogue that would be spoken in the scene."
}
```""",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "shot_number": shot_number,
                                "dialogue": dialogue
                            })
                        }
                    ]
                }
            ]
        )

        # Collect streamed response
        content = ""
        for event in message:
            if event.type == "content_block_delta":
                content += event.delta.text
            elif event.type == "message_stop":
                break

        # Parse the compressed dialogue from response
        try:
            # Extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(content)
            return result.get("rewritten_dialogue", dialogue)
        except Exception as e:
            print(f"  Warning: Failed to parse compressed dialogue: {e}")
            return dialogue

    def _generate_dialogue_with_compression(
        self,
        dialogue: str,
        shot_number: int,
        voice_id: str
    ) -> Tuple[str, str, float, int]:
        """
        Generate dialogue audio with compression if needed

        Args:
            dialogue: Original dialogue text
            shot_number: Shot number
            voice_id: ElevenLabs voice ID

        Returns:
            Tuple of (audio_path, final_dialogue, duration, compression_iterations)
        """
        compression_iterations = 0
        current_dialogue = dialogue
        successful_temp_path = None
        successful_duration = None

        while compression_iterations < 5:  # Max 5 attempts
            # Strip parentheticals before sending to TTS
            tts_dialogue = self._strip_parentheticals(current_dialogue)

            # Generate audio with ElevenLabs
            print(f"    Generating audio (attempt {compression_iterations + 1})...")

            try:
                audio = self.elevenlabs_client.text_to_speech.convert(
                    text=tts_dialogue,
                    voice_id=voice_id,
                    model_id=self.model_id,
                    output_format=self.dialogue_output_format
                )

                # Save audio to temp file
                temp_path = self.audio_dir / f"temp_shot_{shot_number:03d}_iter_{compression_iterations}.mp3"
                with open(temp_path, "wb") as f:
                    for chunk in audio:
                        f.write(chunk)

                # Check duration
                duration = self._check_audio_duration(str(temp_path))

                # Log for debugging
                self.debug_log.append({
                    "shot": shot_number,
                    "iteration": compression_iterations + 1,
                    "dialogue": current_dialogue[:100],
                    "duration": duration,
                    "file_size": temp_path.stat().st_size
                })

                if duration <= self.max_dialogue_duration:
                    # Success! Under 10 seconds
                    successful_temp_path = temp_path
                    successful_duration = duration
                    break
                else:
                    # Need to compress
                    print(f"    Dialogue too long ({duration:.1f}s), compressing...")

                    # Clean up this iteration's temp file since it's too long
                    if temp_path.exists():
                        os.remove(temp_path)

                    compression_iterations += 1
                    if compression_iterations < 5:
                        current_dialogue = self._compress_dialogue(current_dialogue, shot_number)

            except Exception as e:
                print(f"    Error generating dialogue: {e}")
                if 'temp_path' in locals() and temp_path.exists():
                    os.remove(temp_path)
                raise

        # Move successful file to final location
        if successful_temp_path and successful_temp_path.exists():
            final_path = self.audio_dir / f"shot_{shot_number:03d}_dialogue.mp3"
            shutil.move(successful_temp_path, final_path)

            if compression_iterations > 0:
                print(f"    ✓ Compressed to {successful_duration:.1f}s after {compression_iterations} iteration(s)")
            else:
                print(f"    ✓ Generated ({successful_duration:.1f}s)")

            return str(final_path), current_dialogue, successful_duration, compression_iterations
        else:
            # Failed to compress under 10 seconds
            raise ValueError(f"Could not compress dialogue under 10 seconds after {compression_iterations} attempts")

    def _generate_sfx_with_retry(self, sfx_description: str, shot_number: int, sfx_index: int, max_retries: int = 3) -> Tuple[str, float]:
        """
        Generate sound effect audio with retry logic

        Args:
            sfx_description: Description of the sound effect
            shot_number: Shot number
            sfx_index: Index of this SFX in the shot
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (audio_path, duration)
        """
        for attempt in range(max_retries):
            try:
                print(f"    Generating SFX {sfx_index}: {sfx_description[:50]}... (attempt {attempt + 1})")

                audio = self.elevenlabs_client.text_to_sound_effects.convert(
                    text=sfx_description,
                    prompt_influence=0.9  # Higher influence for better prompt adherence
                    # No duration_seconds - let ElevenLabs decide
                )

                # Save SFX audio
                sfx_path = self.audio_dir / f"shot_{shot_number:03d}_sfx_{sfx_index}.mp3"
                with open(sfx_path, "wb") as f:
                    for chunk in audio:
                        f.write(chunk)

                # Verify file was created and has content
                if not sfx_path.exists() or sfx_path.stat().st_size == 0:
                    raise ValueError("SFX file was not created or is empty")

                # Get duration
                duration = self._check_audio_duration(str(sfx_path))
                print(f"    ✓ SFX generated ({duration:.1f}s)")

                return str(sfx_path), duration

            except Exception as e:
                print(f"    Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"    Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    raise

    def _generate_waveform(self, audio_path: str, num_chars: int = 40) -> str:
        """
        Convert audio to Unicode waveform visualization

        Args:
            audio_path: Path to audio file
            num_chars: Number of Unicode characters (default 40)

        Returns:
            Unicode string representation of waveform
        """
        try:
            # Check if file exists and has content
            if not Path(audio_path).exists():
                print(f"    Warning: Audio file does not exist: {audio_path}")
                return "▁" * num_chars  # Return flat waveform

            if Path(audio_path).stat().st_size == 0:
                print(f"    Warning: Audio file is empty: {audio_path}")
                return "▁" * num_chars  # Return flat waveform

            # Load audio
            y, sr = librosa.load(audio_path, sr=None, mono=True)

            # Split into chunks
            chunk_size = len(y) // num_chars
            if chunk_size == 0:
                chunk_size = 1

            # Calculate RMS for each chunk
            waveform_chars = []
            unicode_chars = "▁▂▃▄▅▆▇█"

            for i in range(num_chars):
                start = i * chunk_size
                end = min((i + 1) * chunk_size, len(y))
                chunk = y[start:end]

                if len(chunk) > 0:
                    rms = np.sqrt(np.mean(chunk**2))
                    # Normalize to 0-7 for character selection
                    char_index = min(int(rms * len(unicode_chars) / 0.1), len(unicode_chars) - 1)
                    waveform_chars.append(unicode_chars[char_index])
                else:
                    waveform_chars.append(unicode_chars[0])

            return ''.join(waveform_chars)

        except Exception as e:
            print(f"    Error generating waveform for {audio_path}: {e}")
            return "▁" * num_chars  # Return flat waveform on error

    def _refine_sfx_timing(self, shot_data: Dict) -> Dict:
        """
        Use Claude to refine SFX timing based on waveforms

        Args:
            shot_data: Shot data with waveforms

        Returns:
            Updated shot data with refined timings
        """
        if not shot_data.get("sfx") or len(shot_data["sfx"]) == 0:
            return shot_data

        # Build waveform analysis prompt
        waveform_text = f"Shot {shot_data['shot_number']}:\n"
        waveform_text += f"Dialogue: {shot_data.get('dialogue_waveform', 'N/A')}\n"
        waveform_text += f"Dialogue text: \"{shot_data.get('final_dialogue', shot_data.get('dialogue', ''))}\"\n\n"

        for i, sfx in enumerate(shot_data["sfx"]):
            waveform_text += f"SFX {i+1}: {sfx.get('waveform', 'N/A')}\n"
            waveform_text += f"Description: {sfx['description']}\n"
            waveform_text += f"Current timing: 50% (default)\n\n"

        # Call Claude for timing refinement
        message = self.anthropic_client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=8000,
            temperature=0.3,
            stream=True,
            system="""You are an expert audio-visual alignment specialist. Your task is to precisely place sound effects within dialogue clips by analyzing waveform representations and understanding the natural timing of speech and sound.\n\nYour Core Task\nYou receive dialogue audio and sound effect audio represented as text-based waveforms. You must determine where the sound effect should START within the dialogue timeline to achieve natural, realistic placement.\n\nInput Structure\nYou will receive YAML formatted input:\n\n```json\n{\n  "shot": "[number]",\n  "dialogue_text": "[the spoken words]",\n  "sound_effects": [\n    {\n      "name": "[description of sound 1]",\n      "waveform": "[sound effect 1 waveform characters]"\n    },\n    {\n      "name": "[description of sound 2]",\n      "waveform": "[sound effect 2 waveform characters]"\n    }\n  ],\n  "alignment_view": "[dialogue waveform characters]                [dialogue]\\n[sound effect 1 waveform characters]          [sound_1 at 0.0]\\n[sound effect 2 waveform characters]          [sound_2 at 0.0]"\n}\n```\n\nHow to Read Waveforms\nCharacters like ▁▂▃▄▅▆▇█ represent amplitude (volume) from quiet to loud\nThe dialogue waveform spans the entire clip duration\nBoth waveforms start aligned at position 0.0\nEach character position represents a time slice\n\nYour Analysis Process\nMap the dialogue text to its waveform - identify where each word occurs by matching speech patterns (peaks) with syllables and pauses (valleys) with spaces/punctuation\nIdentify the sound effect's actual sound moment (where amplitude peaks) versus any leading silence\n\nDetermine the logical placement based on:\nSemantic context (what's happening in the dialogue)\nNatural pauses or emphasis points\nThe sound effect's purpose and typical timing\nCalculate what percentage through the dialogue the sound effect's FIRST character should begin\n\nOutput Structure\nReturn ONLY a JSON object:\n\n```json\n{\n  "shot": "[number]",\n  "timings": [\n    {\n      "name": "[description of sound 1]",\n      "timing": 0.25\n    },\n    {\n      "name": "[description of sound 2]",\n      "timing": -0.15\n    }\n  ]\n}\n```\n\nWhere timing represents the percentage through the dialogue where the sound effect file should START (not where its peak occurs, but where its first character begins).\n\nCritical Reminders\nYou're positioning the START of the sound effect file, including any leading silence\nTiming values can be negative (sound starts before dialogue) or greater than 1.0 (starts near the end)\n\nNegative values mean the sound effect begins before the dialogue, with only its latter portion audible\n\n0.0 = beginning of dialogue, 1.0 = end of dialogue\n\nExample: -0.2 means the sound effect starts 20% of the dialogue duration before the dialogue begins\n\nAccount for the sound effect's dead space when determining placement\nThe sound effect may extend beyond the dialogue end - that's acceptable\nThink naturistically about when sounds would actually occur relative to speech""",
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze these waveforms and refine the SFX timing:\n\n{waveform_text}\n\nReturn a JSON object with refined timings:\n```json\n{{\"sfx_timings\": [percentage1, percentage2, ...]}}\n```"
                }
            ]
        )

        # Collect response
        content = ""
        for event in message:
            if event.type == "content_block_delta":
                content += event.delta.text
            elif event.type == "message_stop":
                break

        # Parse refined timings
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                timings = result.get("sfx_timings", [])

                # Update SFX timings
                for i, timing in enumerate(timings):
                    if i < len(shot_data["sfx"]):
                        shot_data["sfx"][i]["refined_timing_percentage"] = timing
                        print(f"    SFX {i+1} timing: 50% (default) → {timing}% (refined)")
        except Exception as e:
            print(f"    Warning: Failed to parse refined timings: {e}")
            # Add default timing of 50% if refinement failed
            for i, sfx in enumerate(shot_data["sfx"]):
                if not sfx.get("refined_timing_percentage"):
                    sfx["refined_timing_percentage"] = 50
                    print(f"    SFX {i+1}: Using default timing 50%")

        return shot_data

    def stage_1_audio_generation(self):
        """Generate dialogue and SFX audio with compression"""
        print("\n" + "="*50)
        print("STAGE 1: Audio Generation with Compression")
        print("="*50)

        # Load shot list if not already loaded
        if not self.shot_list_data:
            self._load_shot_list()

        processed_shots = []

        for shot in self.shot_list_data.get("shots", []):
            shot_number = shot.get("shot_number", 0)
            print(f"\nProcessing Shot {shot_number}...")

            shot_data = {
                "shot_number": shot_number,
                "dialogue": shot.get("dialogue"),
                "character": shot.get("character"),
                "sfx": []
            }

            # Generate dialogue if present and character is not "none"
            if shot.get("dialogue") and shot.get("character") and shot["character"].lower() != "none":
                character = shot["character"]
                voice_id = self.voice_mappings.get(
                    character,
                    self.voice_mappings.get("DEFAULT", "21m00Tcm4TlvDq8ikWAM")
                )

                print(f"  Generating dialogue for {character}...")

                try:
                    audio_path, final_dialogue, duration, iterations = self._generate_dialogue_with_compression(
                        dialogue=shot["dialogue"],
                        shot_number=shot_number,
                        voice_id=voice_id
                    )

                    shot_data["dialogue_audio_path"] = audio_path
                    shot_data["final_dialogue"] = final_dialogue
                    shot_data["dialogue_duration"] = duration
                    shot_data["compression_iterations"] = iterations
                    shot_data["original_dialogue"] = shot["dialogue"] if iterations > 0 else None

                except Exception as e:
                    print(f"  ERROR generating dialogue: {e}")
                    shot_data["dialogue_error"] = str(e)
            elif shot.get("character") and shot["character"].lower() == "none":
                print(f"  Skipping dialogue generation for 'none' character")
                shot_data["character"] = "none"
                shot_data["dialogue_skipped"] = True

            # Generate SFX if present (new format: array of strings)
            sound_effects = shot.get("sound_effects", [])
            if sound_effects:
                for i, sfx_text in enumerate(sound_effects, 1):
                    # Handle string format (new) or dict format (legacy)
                    if isinstance(sfx_text, dict):
                        # Legacy format compatibility
                        sfx_text = sfx_text.get("sfx", sfx_text.get("description", ""))
                    else:
                        # New format: just strings
                        sfx_text = str(sfx_text)

                    # Clean SFX text (remove {{SFX: }} wrapper if present)
                    sfx_text = re.sub(r'\{\{SFX:\s*|\}\}', '', sfx_text).strip()

                    try:
                        sfx_path, duration = self._generate_sfx_with_retry(
                            sfx_description=sfx_text,
                            shot_number=shot_number,
                            sfx_index=i
                        )

                        shot_data["sfx"].append({
                            "description": sfx_text,
                            "audio_path": sfx_path,
                            "duration": duration
                            # No timing_percentage - will be generated in Stage 3
                        })

                    except Exception as e:
                        print(f"  ERROR generating SFX after retries: {e}")
                        shot_data["sfx"].append({
                            "description": sfx_text,
                            "error": str(e)
                            # No timing_percentage
                        })

            processed_shots.append(shot_data)

        # Save stage output
        self.variables["processed_shots"] = processed_shots
        self._save_output(1, "audio_generated", {"shots": processed_shots})

        # Save debug log
        self._save_debug_log()

        print(f"\n✓ Generated audio for {len(processed_shots)} shots")

    def stage_2_waveform_generation(self):
        """Generate waveform visualizations for all audio"""
        print("\n" + "="*50)
        print("STAGE 2: Waveform Generation")
        print("="*50)

        shots_with_waveforms = []

        for shot in self.variables.get("processed_shots", []):
            shot_number = shot["shot_number"]
            print(f"\nGenerating waveforms for Shot {shot_number}...")

            # Generate dialogue waveform
            if shot.get("dialogue_audio_path"):
                waveform = self._generate_waveform(shot["dialogue_audio_path"])
                shot["dialogue_waveform"] = waveform
                print(f"  Dialogue: {waveform}")

            # Generate SFX waveforms
            for i, sfx in enumerate(shot.get("sfx", [])):
                if sfx.get("audio_path") and not sfx.get("error"):
                    waveform = self._generate_waveform(sfx["audio_path"])
                    sfx["waveform"] = waveform
                    print(f"  SFX {i+1}: {waveform}")
                elif sfx.get("error"):
                    print(f"  SFX {i+1}: Skipped (generation failed)")

            shots_with_waveforms.append(shot)

        # Save stage output
        self.variables["shots_with_waveforms"] = shots_with_waveforms
        self._save_output(2, "waveforms", {"shots": shots_with_waveforms})

        print(f"\n✓ Generated waveforms for {len(shots_with_waveforms)} shots")

    def stage_3_timing_refinement(self):
        """Refine SFX timing using Claude analysis"""
        print("\n" + "="*50)
        print("STAGE 3: Timing Refinement")
        print("="*50)

        refined_shots = []

        for shot in self.variables.get("shots_with_waveforms", []):
            shot_number = shot["shot_number"]

            if shot.get("sfx") and len(shot["sfx"]) > 0:
                # Only refine if there are successful SFX
                successful_sfx = [s for s in shot["sfx"] if not s.get("error")]
                if successful_sfx:
                    print(f"\nRefining timings for Shot {shot_number}...")
                    shot = self._refine_sfx_timing(shot)

            refined_shots.append(shot)

        # Save final output
        self.variables["refined_shots"] = refined_shots
        self._save_output(3, "refined_timings", {"shots": refined_shots})

        # Create enhanced shot list with updated dialogue
        self._create_enhanced_shot_list()

        print(f"\n✓ Refined timings for {len(refined_shots)} shots")
        print(f"✓ Saved enhanced shot list to {self.output_dir}/enhanced_shot_list.json")

    def stage_4_audio_mixing(self):
        """Mix dialogue and SFX into combined 10-second clips"""
        print("\n" + "="*50)
        print("STAGE 4: Audio Mixing & Trimming")
        print("="*50)

        # Get mixing settings from config
        sfx_volume = self.config.get("mixing", {}).get("sfx_volume", 0.7)
        target_duration_ms = self.config.get("mixing", {}).get("target_duration", 10) * 1000
        center_dialogue = self.config.get("mixing", {}).get("center_dialogue", True)

        mixed_shots = []

        for shot in self.variables.get("refined_shots", []):
            shot_number = shot["shot_number"]

            # Skip if no dialogue audio
            if not shot.get("dialogue_audio_path"):
                print(f"\nShot {shot_number}: No dialogue, skipping mixing")
                mixed_shots.append(shot)
                continue

            print(f"\nMixing Shot {shot_number}...")

            try:
                # Load dialogue audio
                dialogue_path = shot["dialogue_audio_path"]
                if not Path(dialogue_path).exists():
                    print(f"  Warning: Dialogue file not found: {dialogue_path}")
                    mixed_shots.append(shot)
                    continue

                dialogue_audio = AudioSegment.from_mp3(dialogue_path)
                dialogue_duration_ms = len(dialogue_audio)
                dialogue_duration_s = dialogue_duration_ms / 1000.0

                print(f"  Dialogue duration: {dialogue_duration_s:.2f}s")

                # Create base 10-second silent track
                combined = AudioSegment.silent(duration=target_duration_ms)

                # Calculate dialogue position (center if configured)
                if center_dialogue:
                    dialogue_start_ms = (target_duration_ms - dialogue_duration_ms) // 2
                else:
                    dialogue_start_ms = 0

                # Ensure dialogue doesn't go past 10 seconds
                if dialogue_start_ms + dialogue_duration_ms > target_duration_ms:
                    dialogue_start_ms = target_duration_ms - dialogue_duration_ms

                if dialogue_start_ms < 0:
                    # Dialogue is longer than 10 seconds - trim it
                    print(f"  Warning: Dialogue exceeds 10s, trimming...")
                    dialogue_audio = dialogue_audio[:target_duration_ms]
                    dialogue_start_ms = 0
                    dialogue_duration_ms = target_duration_ms

                # Overlay dialogue
                combined = combined.overlay(dialogue_audio, position=dialogue_start_ms)
                print(f"  Dialogue positioned at {dialogue_start_ms/1000:.2f}s")

                # Process each SFX
                sfx_count = 0
                for i, sfx in enumerate(shot.get("sfx", [])):
                    if sfx.get("error") or not sfx.get("audio_path"):
                        continue

                    sfx_path = sfx["audio_path"]
                    if not Path(sfx_path).exists():
                        print(f"  Warning: SFX file not found: {sfx_path}")
                        continue

                    # Load SFX audio
                    sfx_audio = AudioSegment.from_mp3(sfx_path)

                    # Apply volume reduction
                    sfx_audio = sfx_audio - (20 * np.log10(1/sfx_volume))  # Convert to dB reduction

                    # Get timing percentage (use refined or default)
                    timing_pct = sfx.get("refined_timing_percentage", 50)

                    # Calculate SFX start position relative to dialogue
                    sfx_start_relative_ms = (timing_pct / 100.0) * dialogue_duration_ms
                    sfx_start_absolute_ms = dialogue_start_ms + sfx_start_relative_ms

                    # Handle negative timing (SFX starts before dialogue)
                    if timing_pct < 0:
                        # Negative percentage means start before dialogue
                        sfx_start_absolute_ms = dialogue_start_ms + sfx_start_relative_ms

                    print(f"  SFX {i+1} timing: {timing_pct}% → {sfx_start_absolute_ms/1000:.2f}s")

                    # Trim SFX if it starts before 0
                    if sfx_start_absolute_ms < 0:
                        trim_amount_ms = int(-sfx_start_absolute_ms)
                        sfx_audio = sfx_audio[trim_amount_ms:]
                        print(f"    Trimmed {trim_amount_ms/1000:.2f}s from SFX start")
                        sfx_start_absolute_ms = 0

                    # Trim SFX if it extends past 10 seconds
                    sfx_end_ms = sfx_start_absolute_ms + len(sfx_audio)
                    if sfx_end_ms > target_duration_ms:
                        trim_amount_ms = int(sfx_end_ms - target_duration_ms)
                        sfx_audio = sfx_audio[:-trim_amount_ms]
                        print(f"    Trimmed {trim_amount_ms/1000:.2f}s from SFX end")

                    # Overlay SFX
                    if sfx_start_absolute_ms >= 0 and sfx_start_absolute_ms < target_duration_ms:
                        combined = combined.overlay(sfx_audio, position=int(sfx_start_absolute_ms))
                        sfx_count += 1
                        print(f"    ✓ Added SFX at {sfx_start_absolute_ms/1000:.2f}s ({len(sfx_audio)/1000:.2f}s duration)")

                # Export combined audio
                combined_path = self.audio_dir / f"shot_{shot_number:03d}_combined.mp3"
                combined.export(combined_path, format="mp3", bitrate="128k")

                shot["combined_audio_path"] = str(combined_path)
                shot["combined_duration"] = len(combined) / 1000.0
                shot["sfx_mixed_count"] = sfx_count

                print(f"  ✓ Mixed {sfx_count} SFX into combined audio ({len(combined)/1000:.2f}s)")

            except Exception as e:
                print(f"  ERROR mixing audio: {e}")
                shot["mixing_error"] = str(e)

            mixed_shots.append(shot)

        # Save stage output
        self.variables["mixed_shots"] = mixed_shots
        self._save_output(4, "mixed_audio", {"shots": mixed_shots})

        print(f"\n✓ Created mixed audio for {len([s for s in mixed_shots if s.get('combined_audio_path')])} shots")

    def _create_enhanced_shot_list(self):
        """Create enhanced shot list with compressed dialogue for lip sync"""
        # Load original shot list
        with open(self.shot_list_path, 'r') as f:
            original_data = json.load(f)

        # Create mapping of shot numbers to final dialogue
        dialogue_updates = {}
        for shot in self.variables.get("refined_shots", []):
            if shot.get("final_dialogue") and shot.get("compression_iterations", 0) > 0:
                dialogue_updates[shot["shot_number"]] = shot["final_dialogue"]

        # Update the original shot list with compressed dialogue
        enhanced_data = original_data.copy()
        shots_updated = 0

        for scene_data in enhanced_data.get('all_shot_lists', []):
            for shot in scene_data.get('shot_list', {}).get('shots', []):
                shot_num = shot.get('shot_number')
                if shot_num in dialogue_updates:
                    shot['original_dialogue'] = shot.get('dialogue')
                    shot['dialogue'] = dialogue_updates[shot_num]
                    shot['was_compressed'] = True
                    shots_updated += 1

        # Add metadata and audio information
        enhanced_shot_list = {
            "original_shot_list_path": self.shot_list_path,
            "generation_timestamp": datetime.now().isoformat(),
            "model_id": self.model_id,
            "compressed_dialogues_count": shots_updated,
            "audio_generation_results": self.variables.get("refined_shots", []),
            "enhanced_shot_lists": enhanced_data.get('all_shot_lists', [])
        }

        with open(self.output_dir / "enhanced_shot_list.json", 'w') as f:
            json.dump(enhanced_shot_list, f, indent=2)

        print(f"  Updated {shots_updated} shots with compressed dialogue for lip sync")

    def _save_debug_log(self):
        """Save detailed debug log for troubleshooting"""
        debug_output = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "model_id": self.model_id,
                "max_dialogue_duration": self.max_dialogue_duration,
                "scene_limit": self.scene_limit,
                "max_shots": self.max_shots
            },
            "compression_attempts": self.debug_log,
            "statistics": {
                "total_shots": len(self.variables.get("processed_shots", [])),
                "dialogue_generated": sum(1 for s in self.variables.get("processed_shots", [])
                                        if s.get("dialogue_audio_path")),
                "dialogue_compressed": sum(1 for s in self.variables.get("processed_shots", [])
                                         if s.get("compression_iterations", 0) > 0),
                "sfx_generated": sum(len(s.get("sfx", [])) for s in self.variables.get("processed_shots", [])),
                "errors": sum(1 for s in self.variables.get("processed_shots", [])
                            if s.get("dialogue_error") or any(sfx.get("error") for sfx in s.get("sfx", [])))
            }
        }

        with open(self.output_dir / "debug_log.json", 'w') as f:
            json.dump(debug_output, f, indent=2)

        print(f"  → Saved debug log to debug_log.json")

    def run(self):
        """Run the audio generation pipeline"""
        print(f"\nStarting Audio Generation Pipeline from stage {self.start_stage}")
        print(f"Output directory: {self.output_dir}")
        print(f"Shot list: {self.shot_list_path}")

        stages = [
            (1, self.stage_1_audio_generation),
            (2, self.stage_2_waveform_generation),
            (3, self.stage_3_timing_refinement),
            (4, self.stage_4_audio_mixing)
        ]

        for stage_num, stage_func in stages:
            if stage_num >= self.start_stage:
                stage_func()

        # Create summary
        summary = self._create_summary()
        with open(self.output_dir / "summary.txt", 'w') as f:
            f.write(summary)

        print("\n" + "="*50)
        print("PIPELINE COMPLETE!")
        print("="*50)
        print(f"All outputs saved to: {self.output_dir}")
        print("\nSummary:")
        print(summary)

    def _create_summary(self) -> str:
        """Create a human-readable summary of the pipeline run"""
        shots = self.variables.get("mixed_shots", self.variables.get("refined_shots", []))

        total_dialogue = sum(1 for s in shots if s.get("dialogue_audio_path"))
        total_sfx = sum(len([sfx for sfx in s.get("sfx", []) if not sfx.get("error")]) for s in shots)
        compressed_count = sum(1 for s in shots if s.get("compression_iterations", 0) > 0)
        skipped_none = sum(1 for s in shots if s.get("dialogue_skipped"))
        sfx_errors = sum(len([sfx for sfx in s.get("sfx", []) if sfx.get("error")]) for s in shots)
        mixed_count = sum(1 for s in shots if s.get("combined_audio_path"))

        total_dialogue_duration = sum(s.get("dialogue_duration", 0) for s in shots)
        total_sfx_duration = sum(
            sfx.get("duration", 0)
            for s in shots
            for sfx in s.get("sfx", [])
            if not sfx.get("error")
        )

        summary = f"""Audio Generation Pipeline Summary
================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Statistics:
- Total shots processed: {len(shots)}
- Dialogue clips generated: {total_dialogue}
- Dialogue skipped ('none'): {skipped_none}
- SFX clips generated: {total_sfx}
- SFX generation errors: {sfx_errors}
- Dialogues compressed: {compressed_count}
- Combined audio created: {mixed_count}

Duration:
- Total dialogue: {total_dialogue_duration:.1f} seconds
- Total SFX: {total_sfx_duration:.1f} seconds
- Average dialogue: {total_dialogue_duration/max(total_dialogue, 1):.1f} seconds

Configuration:
- Model: {self.model_id}
- Output format: {self.dialogue_output_format}
- Scene limit: {self.scene_limit or 'None'}
- Max shots: {self.max_shots or 'None'}

Debug log available: debug_log.json
Enhanced shot list: enhanced_shot_list.json
"""

        return summary