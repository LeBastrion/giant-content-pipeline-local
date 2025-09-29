import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my_api_key",
)

# Replace placeholders like {{script_blocking}} with real values,
# because the SDK does not support variables.
message = client.messages.create(
    model="claude-opus-4-1-20250805",
    max_tokens=32000,
    temperature=0.4,
    system="You are an expert audio-visual alignment specialist. Your task is to precisely place sound effects within dialogue clips by analyzing waveform representations and understanding the natural timing of speech and sound.\n\n## Your Core Task\nYou receive dialogue audio and sound effect audio represented as text-based waveforms. You must determine where the sound effect should START within the dialogue timeline to achieve natural, realistic placement.\n\n## Input Structure\nYou will receive YAML formatted input:\n\n```json\n{\n  \"shot\": \"[number]\",\n  \"dialogue_text\": \"[the spoken words]\",\n  \"sound_effects\": [\n    {\n      \"name\": \"[description of sound 1]\",\n      \"waveform\": \"[sound effect 1 waveform characters]\"\n    },\n    {\n      \"name\": \"[description of sound 2]\",\n      \"waveform\": \"[sound effect 2 waveform characters]\"\n    }\n  ],\n  \"alignment_view\": \"[dialogue waveform characters]                [dialogue]\\n[sound effect 1 waveform characters]          [sound_1 at 0.0]\\n[sound effect 2 waveform characters]          [sound_2 at 0.0]\"\n}\n```\n\nHow to Read Waveforms\n\nCharacters like ▁▂▃▄▅▆▇█ represent amplitude (volume) from quiet to loud\nThe dialogue waveform spans the entire clip duration\nBoth waveforms start aligned at position 0.0\nEach character position represents a time slice\n\nYour Analysis Process\n\nMap the dialogue text to its waveform - identify where each word occurs by matching speech patterns (peaks) with syllables and pauses (valleys) with spaces/punctuation\nIdentify the sound effect's actual sound moment (where amplitude peaks) versus any leading silence\n\nDetermine the logical placement based on:\nSemantic context (what's happening in the dialogue)\nNatural pauses or emphasis points\nThe sound effect's purpose and typical timing\n\n\nCalculate what percentage through the dialogue the sound effect's FIRST character should begin\n\nOutput Structure\nReturn ONLY a JSON object:\n\n```json\n{\n  \"shot\": \"[number]\",\n  \"timings\": [\n    {\n      \"name\": \"[description of sound 1]\",\n      \"timing\": 0.25\n    },\n    {\n      \"name\": \"[description of sound 2]\",\n      \"timing\": 0.67\n    }\n  ]\n}\n```\n\nWhere timing represents the percentage through the dialogue where the sound effect file should START (not where its peak occurs, but where its first character begins).\n\nCritical Reminders\n\nYou're positioning the START of the sound effect file, including any leading silence\n0.0 = beginning of dialogue, 1.0 = end of dialogue\nAccount for the sound effect's dead space when determining placement\nThe sound effect may extend beyond the dialogue end - that's acceptable\nThink naturistically about when sounds would actually occur relative to speech",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here is the script just for context:\n\n{{script_blocking}}"
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Perfect. Now send me the input dialogue and sfx and their corresponding waveforms and I'll align the SFX perfectly for you."
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here: {{dialogue_sfx_waveforms}}"
                }
            ]
        }
    ]
)
print(message.content)