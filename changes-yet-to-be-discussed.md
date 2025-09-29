# I have implemented these changes and it's important that we understand that these will need to be discussed and thought about and we will need to understand how they implement other things in the pipeline. Everything depends on something else so it's very important we understand all of the implications.

## Change to the shot list output.

Shot List Generator Changes Summary
Output Format Changes
The YAML output structure has been modified with the following fields:
Added Fields:

additional_characters: Array of non-speaking characters from the bible visible in the shot
lip_sync_required: Boolean indicating if the shot needs lip sync (true when dialogue exists AND speaker's face is visible)
props: Array of props from the script's {{PROPS}} annotations that appear in this shot

Modified Fields:

sound_effects: Simplified from objects with timing to a flat array of SFX strings

Old: [{sfx: "{{SFX: door slam}}", timing: 50}]
New: ["{{SFX: door slam}}"]



Behavioral Changes

Sound Effects: The LLM no longer calculates timing percentages for SFX. It still splits compound SFX annotations into separate array entries (e.g., "{{SFX: rustling, chiming}}" becomes two entries).
Character Tracking: The LLM now explicitly tracks which bible characters are visible in each shot beyond the speaking character, outputting them in additional_characters.
Props Extraction: The LLM identifies which props from the scene's {{PROPS}} annotations would be visible in each shot based on blocking and framing.
Lip Sync Detection: The LLM determines if lip sync is needed by checking two conditions: dialogue exists AND the character's face would be visible given the shot framing.

Pipeline Impact

Downstream systems expecting SFX timing data will need alternative timing source
Lip sync pipeline can now filter shots directly via boolean flag
Character presence tracking is now explicit for scene composition
Props list enables automated asset management per shot

The core shot breakdown logic remains unchanged - one shot per dialogue line, preserving all annotations, maintaining visual continuity.

- In terms of how the timing now works, obviously currently we're replacing this timing with the timing from the audio generation pipeline, but now we will just be adding it anew. The idea was the audio generation pipeline added more accurate timing, but since we have that already, we might as well just use that timing. And if for whatever reason the timing call doesn't work, we will default the timing percentage