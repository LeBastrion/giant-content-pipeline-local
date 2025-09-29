"""
Example implementation of dialogue compression logic
This shows how the audio pipeline would handle the 10-second limit
"""

import librosa
import anthropic
from typing import Dict, Tuple

class DialogueCompressor:
    """Handles dialogue compression to ensure < 10 seconds"""

    def __init__(self, anthropic_client):
        self.client = anthropic_client
        self.max_duration = 10.0  # seconds

    def check_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        return duration

    def compress_dialogue(self, dialogue: str, shot_number: int) -> str:
        """Use Claude to compress dialogue text"""

        message = self.client.messages.create(
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
                            "text": f'{{"shot_number": {shot_number}, "dialogue": "{dialogue}"}}'
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
        import json
        try:
            result = json.loads(content)
            return result.get("rewritten_dialogue", dialogue)
        except:
            # Fallback to original if parsing fails
            return dialogue

    def process_dialogue_with_compression(
        self,
        dialogue: str,
        shot_number: int,
        voice_id: str,
        elevenlabs_client
    ) -> Tuple[str, str, float, int]:
        """
        Generate dialogue audio with compression if needed

        Returns:
            - audio_path: Path to final audio file
            - final_dialogue: Final dialogue text (may be compressed)
            - duration: Audio duration in seconds
            - compression_iterations: Number of compression attempts
        """

        compression_iterations = 0
        current_dialogue = dialogue

        while compression_iterations < 5:  # Max 5 attempts
            # Generate audio with ElevenLabs
            audio = elevenlabs_client.text_to_speech.convert(
                text=current_dialogue,
                voice_id=voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128"
            )

            # Save audio to temp file
            temp_path = f"temp_shot_{shot_number}_iter_{compression_iterations}.mp3"
            with open(temp_path, "wb") as f:
                f.write(audio)

            # Check duration
            duration = self.check_audio_duration(temp_path)

            if duration <= self.max_duration:
                # Success! Under 10 seconds
                final_path = f"shot_{shot_number:03d}_dialogue.mp3"
                import shutil
                shutil.move(temp_path, final_path)

                return final_path, current_dialogue, duration, compression_iterations

            # Need to compress
            print(f"  Shot {shot_number} dialogue too long ({duration:.1f}s), compressing...")
            compression_iterations += 1
            current_dialogue = self.compress_dialogue(current_dialogue, shot_number)

        # Failed to compress under 10 seconds after max attempts
        raise ValueError(f"Could not compress dialogue under 10 seconds after {compression_iterations} attempts")


# Usage example:
def generate_audio_with_compression(shot_data: Dict, voice_mappings: Dict):
    """Process a single shot with dialogue compression"""

    # Initialize clients
    anthropic_client = anthropic.Anthropic()
    elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    compressor = DialogueCompressor(anthropic_client)

    shot_number = shot_data["shot_number"]
    character = shot_data["character"]
    dialogue = shot_data["dialogue"]

    # Get voice ID for character
    voice_id = voice_mappings.get(character, voice_mappings.get("DEFAULT"))

    # Generate with compression if needed
    audio_path, final_dialogue, duration, iterations = compressor.process_dialogue_with_compression(
        dialogue=dialogue,
        shot_number=shot_number,
        voice_id=voice_id,
        elevenlabs_client=elevenlabs_client
    )

    # Update shot data with results
    shot_data["audio_path"] = audio_path
    shot_data["final_dialogue"] = final_dialogue
    shot_data["audio_duration"] = duration
    shot_data["compression_iterations"] = iterations

    if iterations > 0:
        print(f"  ✓ Compressed dialogue to {duration:.1f}s after {iterations} iteration(s)")
    else:
        print(f"  ✓ Dialogue generated ({duration:.1f}s)")

    return shot_data