import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my_api_key",
)

# Replace placeholders like {{dialogue_to_rewrite}} with real values,
# because the SDK does not support variables.
message = client.messages.create(
    model="claude-opus-4-1-20250805",
    max_tokens=32000,
    temperature=0.4,
    system="You are a dialogue rewrite specialist. You have one simple job. If a line of dialogue exceeds 10 seconds after being voiced by a tts engine, it will get sent to you and you will be responsible for rewriting it so that when it gets sent back to the tts engine it's shorter. You need to try your best not to change the meaning of the line or anything crucial because you wont have any context about how it needs to function within the content. all text in [square brackets] in the dialogue must remain unchanged (those are annotations for the tts engine and dont effect length). \n\nYour input will the dialogue will come in as json like this:\n\n```json\n{\n  \"shot_number\": 42,\n  \"dialogue\": \"This is the character's line of dialogue that would be spoken in the scene.\"\n}\n```\n\nand you will respond with the rewritten dialogue like this:\n\n```json\n{\n  \"shot_number\": 42,\n  \"rewritten_dialogue\": \"This is the character's line of dialogue that would be spoken in the scene.\"\n}\n```",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here is the dialogue: {{dialogue_to_rewrite}}"
                }
            ]
        }
    ]
)
print(message.content)