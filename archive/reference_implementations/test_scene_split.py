#!/usr/bin/env python3
"""Test scene splitting logic"""

import re

def split_into_scenes(script):
    """Split script into individual scenes based on scene headings"""
    if not script:
        print("Empty script")
        return []

    scene_pattern = r'^(INT\.|EXT\.).*$'
    scenes = []
    current_scene = None

    lines = script.split('\n')
    print(f"Processing {len(lines)} lines")

    for line in lines:
        if re.match(scene_pattern, line.strip()):
            if current_scene:
                scenes.append(current_scene)
                print(f"Found scene: {current_scene['heading']}")
            current_scene = {
                "heading": line.strip(),
                "content": line + "\n"
            }
        elif current_scene:
            current_scene["content"] += line + "\n"

    if current_scene:
        scenes.append(current_scene)
        print(f"Found scene: {current_scene['heading']}")

    return scenes

# Test with sample script
test_script = """Title: The Growing Game

FADE IN:

INT. THE NEST - DAY

Sparkles and Blossom flutter around their cozy hideout, organizing tiny treasures.

SPARKLES
Look at all these shiny things!

EXT. LUCY'S BACKYARD - DAY

Lucy plays in the garden.

LUCY (O.S.)
Mom, where are my seeds?

INT. KITCHEN - CONTINUOUS

The fairies search for the seeds.

FADE OUT.
"""

print("Testing scene splitting:")
print("-" * 40)
scenes = split_into_scenes(test_script)
print(f"\nTotal scenes found: {len(scenes)}")
for i, scene in enumerate(scenes, 1):
    print(f"\nScene {i}: {scene['heading']}")
    print(f"Content preview: {scene['content'][:100]}...")