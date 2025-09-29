"""
Pitch to Shot List Pipeline
5-stage pipeline for generating video production content from initial pitch to final shot lists
"""

import os
import re
import yaml
from typing import Dict, Any, List
import anthropic
from dotenv import load_dotenv

from .base_pipeline import BasePipeline

# Load environment variables
load_dotenv()


class PitchToShotlistPipeline(BasePipeline):
    """
    5-stage content generation pipeline:
    1. Pitch Generation
    2. Script Writing
    3. SFX & Dialogue Tagging
    4. Blocking & Props
    5. Shot List Generation
    """

    def __init__(self, config_path: str = "configs/pitch_to_shotlist.yaml", start_stage: int = 1):
        """Initialize pipeline with Anthropic client"""
        super().__init__(config_path, "pitch_to_shotlist", start_stage)

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Validate required config fields
        self.validate_config([
            "bible",
            "pitch_user_message",
            "script_user_message"
        ])

    def get_stage_count(self) -> int:
        """This pipeline has 5 stages"""
        return 5

    def _extract_fountain_content(self, text: str) -> str:
        """Extract content from fountain code blocks"""
        pattern = r'```fountain\n(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # If no fountain block found, return the original text
        return text.strip()

    def _extract_yaml_content(self, text: str) -> Dict:
        """Extract and parse YAML content from response"""
        pattern = r'```yaml\n(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1))
        # Try to parse the whole text as YAML if no code block
        try:
            return yaml.safe_load(text)
        except:
            return {"error": "Could not parse YAML", "raw_content": text}

    def _handle_kiddo_instruction(self, mode_config: Dict) -> str:
        """Process kiddo instruction based on mode"""
        mode = mode_config.get("mode", "null")

        if mode == "null":
            return ""
        elif mode == "preset":
            # This would be the preset string from your system
            return "Focus on friendship and problem-solving themes."
        elif mode == "append":
            preset = "Focus on friendship and problem-solving themes."
            append_text = mode_config.get("append_text", "")
            return f"{preset} {append_text}".strip()

        return ""

    def _split_into_scenes(self, script: str) -> List[Dict]:
        """Split script into individual scenes based on scene headings"""
        # Debug: Check what we're working with
        if not script:
            print("  Warning: Empty script provided for scene splitting")
            return []

        # Pattern to match scene headings (INT. or EXT.)
        scene_pattern = r'^(INT\.|EXT\.).*$'

        scenes = []
        current_scene = None

        # Split by actual newlines and process
        lines = script.split('\n')
        print(f"  Debug: Processing {len(lines)} lines for scene detection")

        for line in lines:
            # Check if this line is a scene heading
            if re.match(scene_pattern, line.strip()):
                # Save previous scene if exists
                if current_scene:
                    scenes.append(current_scene)
                    print(f"    Found scene: {current_scene['heading']}")
                # Start new scene
                current_scene = {
                    "heading": line.strip(),
                    "content": line + "\n"
                }
            elif current_scene:
                current_scene["content"] += line + "\n"

        # Don't forget the last scene
        if current_scene:
            scenes.append(current_scene)
            print(f"    Found scene: {current_scene['heading']}")

        if not scenes:
            print("  Warning: No scenes found. Check script format for INT./EXT. headings")

        return scenes

    def extract_characters(self, all_shot_lists: List[Dict]):
        """Extract unique characters from shot lists for voice mapping"""
        print("\n  Extracting character list...")

        characters = set()

        # Go through all shots to find unique characters
        for scene_data in all_shot_lists:
            shot_list = scene_data.get("shot_list", {})
            if isinstance(shot_list, dict):
                shots = shot_list.get("shots", [])
                for shot in shots:
                    character = shot.get("character")
                    if character and character.upper() != "NONE":
                        characters.add(character.upper())

        # Create character list with placeholder for voice IDs
        character_list = [
            {"name": char, "voice_id": None}
            for char in sorted(characters)
        ]

        # Save character list
        character_output = {
            "total_characters": len(character_list),
            "characters": character_list,
            "note": "Voice IDs need to be configured for ElevenLabs TTS"
        }

        self._save_output(6, "character_list", character_output)
        print(f"  ✓ Extracted {len(character_list)} unique characters")

        # Also save as a config template
        config_template = {
            "voice_mappings": {char["name"]: "<add_voice_id_here>" for char in character_list},
            "default_voice": "<add_default_voice_id_here>"
        }

        with open(self.output_dir / "06_voice_config_template.yaml", "w") as f:
            yaml.dump(config_template, f, default_flow_style=False)

        return character_list

    def stage_1_pitch(self):
        """Generate pitch: episode title and pitch paragraph"""
        self.print_stage_header(1, "Pitch Generation")

        # Prepare variables
        bible = self.config.get("bible", "")
        kiddo_pitch_instruction = self._handle_kiddo_instruction(
            self.config.get("kiddo_pitch_instruction", {})
        )
        pitch_user_message = self.config.get("pitch_user_message", "")

        # Make API call with streaming to avoid timeout warning
        stream = self.client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=30000,
            temperature=0.7,
            stream=True,
            system="You are a master pitch writer who writes story concepts as single paragraphs that crackle with energy and promise. Your pitches capture the entire emotional arc of a story while maintaining the breathless momentum of a child telling their favorite joke. Every sentence builds anticipation for what comes next, and every beat lands with perfect comic timing. You understand that a great pitch doesn't just describe events—it makes readers feel the chaos, hear the giggles, and see the mayhem unfold.\n\nWrite pitches that begin with immediate character action and desire, not setup or context. Start with the simplest version of your story—add complexity only if it serves the essential emotional journey. Launch readers directly into the character's world through specific, visual moments that demonstrate who they are through what they do, never through description alone. Build escalating comedy through precise physical details and character reactions. Show how small rebellions spiral into larger chaos, but keep one clear emotional thread running through it all—one theme, one journey, one transformation that matters. Capture the specific way each character fails or succeeds at their goals. Use active verbs that pop off the page. Trust concrete imagery over abstract description. Let personality collisions drive the humor. Build to satisfying reversals where chaos leads to unexpected wisdom. End with consequences that feel both surprising and inevitable.\n\nYour pitches must accomplish multiple goals simultaneously: establish the inciting mischief within the first sentence; escalate through specific comedic beats that build naturally; show each character's distinct reaction style through action, not description; maintain child-appropriate content while layering adult humor; create visual moments that illustrate would translate perfectly; balance physical comedy with emotional truth; include at least one unexpected reversal or discovery; conclude with a resolution that transforms disaster into delight; use vocabulary that sings without talking down to readers; and maintain a breathless pace that mirrors the energy of your characters. Use the locations from the bible skillfully to enrich the narrative.\n\nChannel the spirit of the finest children's storytellers—those who understand that the best stories for children never condescend, never oversimplify, and never forget that comedy and heart are dance partners, not competitors. Write pitches that make editors lean forward, parents chuckle, and children demand \"tell me that one again!\"\n\nRemember: The protagonist drives the emotional journey. Supporting characters may learn too, but the main character's growth is the story's heart. Keep titles simple and descriptive—what happens, not how mysteriously it unfolds.\n\n## Pitch Fountain Format\n\n```fountain\nEpisode Title: [STORY TITLE]\n\nPitch Paragraph: [Single paragraph pitch that captures the entire story arc concisely]\n```",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Here is the project I'd like you to write a pitch for:\n\n{bible}\n\n---\n\nAny episode summaries in the bible are simply meant to function as references for how a typical narrative might take shape. Don't rely on them for subject matter, we are creating anew!"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "Great! Anything in particular you'd like for this pitch?"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{kiddo_pitch_instruction}\n\n{pitch_user_message}"
                        }
                    ]
                }
            ]
        )

        # Collect streamed content
        print("  Streaming response...", end="", flush=True)
        content = ""
        for event in stream:
            if event.type == "content_block_delta":
                content += event.delta.text
            elif event.type == "message_stop":
                print(" Done!")
                break

        # Extract fountain content
        fountain_content = self._extract_fountain_content(content)

        # Parse episode title and pitch paragraph
        title_match = re.search(r'Episode Title:\s*(.+)', fountain_content)
        pitch_match = re.search(r'Pitch Paragraph:\s*(.+)', fountain_content, re.DOTALL)

        episode_title = title_match.group(1).strip() if title_match else ""
        pitch_paragraph = pitch_match.group(1).strip() if pitch_match else ""

        # Store variables for next stages
        self.variables["episode_title"] = episode_title
        self.variables["pitch_paragraph"] = pitch_paragraph

        # Save output
        output = {
            "episode_title": episode_title,
            "pitch_paragraph": pitch_paragraph,
            "raw_response": content,
            "fountain_content": fountain_content,
            "cleaned_pitch": fountain_content  # Already clean
        }
        self._save_output(1, "pitch", output)

        print(f"  ✓ Generated episode: {episode_title}")

        return output

    def stage_2_script(self):
        """Generate full script from pitch"""
        self.print_stage_header(2, "Script Generation")

        bible = self.config.get("bible", "")
        kiddo_script_instruction = self._handle_kiddo_instruction(
            self.config.get("kiddo_script_instruction", {})
        )
        episode_title = self.variables.get("episode_title", "")
        pitch_paragraph = self.variables.get("pitch_paragraph", "")
        script_user_message = self.config.get("script_user_message", "")

        stream = self.client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=32000,
            temperature=0.7,
            stream=True,
            system="You craft children's content with the precision of poetry and the wisdom of experience, transforming show bibles into short episode script where meaning and wonder dance as natural companions. \n\nWhen approaching show materials, extract the essence of each character—their unique voice, behavioral patterns, and contradictions. These are living dimensions to inhabit, not merely traits to reference. Let characters reveal themselves through action, honoring their established patterns while allowing room for growth. When they fail, show the specific way only they would fail. Let their flaws become their funniest features. \n\nFollow the pitch's architecture while breathing life into each beat. Identify the emotional core beneath plot points and build scenes around these resonant moments, ensuring every line does triple duty: advancing story, revealing character, delivering meaning.\n\nStructure your narrative as a constellation of purposeful moments. Begin with promise that introduces both character and conflict. Escalate through complications that reveal character depths. Resolve with satisfaction that feels both surprising and inevitable. Build callbacks that pay off. Use the locations in the bible to enrich your storytelling.\n\nDialogue should be brisk and rhythmic—characters exchanging quick, punchy lines rather than long ones. Create lively cadence through rapid back-and-forth, character-specific speech patterns, and natural interruptions. This is as much about action as words, playing together in perfect harmony. Make sentences dance with variety—avoid formulaic patterns, vary structure.\n\nTrust children's intelligence. Use simple words for sophisticated comedy. Keep descriptions concrete—no abstract metaphors children won't grasp. Let humor emerge from personality collision, perfect timing, and the gap between intention and result. Find comedy in how characters move, react, and feel. \n\nHumor should bloom in layers: visual delight for young eyes, verbal wit for attentive ears, gentle irony and knowing subtlety for adult companions. Never wink over children's heads; invite all to laugh on their own terms.\n\nIf a story with a narrator is requested but there isn't a narrator mentioned in the bible, just invent a fitting omniscient narrator. Also make sure to only use locations listed in the bible  in your scene headings.\n\nHere is the fountain output format for your short episode script:\n\n```fountain\nscript here...\n[the script should contain approximately 45-55 lines of dialogue total...]\n```\n\nChannel the spirit of the finest children's storytellers—those who understand that the best stories for children never condescend, never oversimplify, and never forget that comedy and heart are dance partners, not competitors. Write stories that make editors lean forward, parents chuckle, and children demand more!\n\nChildren deserve stories that expand their worlds. Use your words like scalpels, architecting beautiful intellectual irony within structural simplicity. Trust rhythm over explanation, but ensure solutions make kid-logical sense. Make emotional beats land through action, not description.\n\nMost importantly, just trust your own expert judgement implicitly.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Here is the story bible for the project you will be writing on today:\n\n{bible}\n\n---\n\nAny episode summaries in the bible are simply meant to function as references for how a typical narrative might take shape. Don't rely on them for subject matter, we are creating anew!"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "Wonderful! Can you send me the pitch for the script you want me to write?"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{kiddo_script_instruction}\n\nYou'll be writing an short script called: {episode_title}.\n\nHere is the pitch:\n{pitch_paragraph}\n\n{script_user_message}"
                        }
                    ]
                }
            ]
        )

        # Collect streamed content
        print("  Streaming response...", end="", flush=True)
        content = ""
        for event in stream:
            if event.type == "content_block_delta":
                content += event.delta.text
            elif event.type == "message_stop":
                print(" Done!")
                break

        script = self._extract_fountain_content(content)

        # Store clean version for next stage
        self.variables["script"] = script

        output = {
            "script": script,
            "raw_response": content,
            "cleaned_script": script  # Store readable version
        }
        self._save_output(2, "script", output)

        # Also save as plain text for debugging
        with open(self.output_dir / "02_script.txt", "w") as f:
            f.write(script)

        print(f"  ✓ Generated script ({len(script.split())} words)")

        return output

    def stage_3_sfx_dialogue(self):
        """Add sound effects and dialogue tags to script"""
        self.print_stage_header(3, "SFX & Dialogue Tagging")

        bible = self.config.get("bible", "")
        script = self.variables.get("script", "")

        stream = self.client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=32000,
            temperature=0.4,
            stream=True,
            system="You are a dialogue adaptation specialist and sound annotation expert for an animated production. Your task is to prepare scripts for voice synthesis and sound generation by adding emotional/delivery tags to dialogue and annotating sound effects.\nWhen you receive a script and project bible, you will:\n\nReturn the exact same script structure and content unchanged\nEnhance dialogue lines by incorporating audio tags that guide voice performance and acoustic qualities\nAnnotate all sound effects inline using a consistent, extractable format\n\nDIALOGUE TAGGING:\nYour tagging approach should be surgical and purposeful. Each tag should serve the emotional truth of the moment, the character's personality, or the physical reality of how the voice is heard.\nConsider these factors when tagging:\n\nThe character's emotional state in the scene\nPhysical location and how it affects voice (through walls, from distance, over phone, etc.)\nRelationship dynamics between characters\nStory beats and dramatic tension\nCharacter personality traits from the bible\n\nApply tags sparingly but effectively:\n\nEmotional shifts or reveals [whispers], [excited], [sarcastic]\nPhysical actions that affect speech [sighs], [laughs], [exhales]\nEnvironmental/spatial effects [muffled], [distant], [echoing]\nKey dramatic moments through CAPS or ellipses...\n\nFormat dialogue as:\n\"[tag if needed] Dialogue text with natural punctuation and EMPHASIS where appropriate.\"\n\nSOUND EFFECT ANNOTATION:\nMark all sound effects using this format: {{SFX: description}}\n\nEach sound effect description should paint a clear sonic picture by describing the acoustic qualities like texture, pitch, and intensity, while being explicit about how sounds relate to each other in time using words like \"followed by,\" \"then,\" \"overlapping with,\" or \"simultaneous.\" Focus on how the sound actually sounds rather than just what's making it. Include details about whether sounds are crisp or muffled, bright or dull, sudden or gradual, and their spatial qualities like distance or echo. Always specify the total duration at the end, all sounds effects must be shorter than 10 seconds long. Tend towards shorter sound effects rather than longer ones. \n\nExamples:\n{{SFX: sharp crystalline crash followed by high-pitched tinkling fragments scattering, bright and close. 2 seconds}}\n\n{{SFX: deep groaning creak building slowly then ending with a heavy wooden thud, low resonant and labored. 3 seconds}}\n\n{{SFX: rapid crunching footfalls starting soft then growing louder and faster, crisp and gritty. 7 seconds}}\n\n{{SFX: sustained hollow whistling with fluctuating pitch overlapping with intermittent airy gusts, haunting and distant. 5 seconds}}\n\n{{SFX: deep bass-heavy boom then muffled rumbling that gradually fades, compressed and reverberant. 3 seconds}}\n\nWhen sound effects are already mentioned in action lines, add the annotation inline right where they occur. Don't duplicate or move them, just annotate them where they naturally appear.\nAvoid:\n\nOver-tagging dialogue (multiple tags per line unless necessary)\nTags that contradict character voice or situation\nOverly long SFX descriptions\nVague SFX descriptions that lack useful detail\n\nYour goal is to create a production-ready script where voice synthesis will naturally convey the emotional journey and sound effects can be easily extracted and generated to build the complete soundscape.\n\nAlways format your writing with proper script formatting in Fountain format:\n\n```fountain\nTitle: [STORY TITLE]\n\n{{SFX: insert sound effect here}}\n\nFADE IN:\n\nINT. [LOCATION FROM BIBLE] - DAY\n\naction description as needed\n\nCHARACTER NAME\n(dialogue [tags] if applicable)\n\nCHARACTER NAME\n(dialogue [tags] if applicable)\n\nand so on...\n```\n\nMost importantly, just use your expert judgment—I trust it implicitly.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Here is the story bible for the project this script was based on for context:\n\n{bible}"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "Wonderful! Can you send me the script you want me to rewrite with tagged dialogue?"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Here is the script: {script}"
                        }
                    ]
                }
            ]
        )

        # Collect streamed content
        print("  Streaming response...", end="", flush=True)
        content = ""
        for event in stream:
            if event.type == "content_block_delta":
                content += event.delta.text
            elif event.type == "message_stop":
                print(" Done!")
                break

        script_tagged = self._extract_fountain_content(content)

        # Store clean version for next stage
        self.variables["script_tagged"] = script_tagged

        # Count SFX annotations
        sfx_count = len(re.findall(r'\{\{SFX:', script_tagged))

        output = {
            "script_tagged": script_tagged,
            "sfx_count": sfx_count,
            "raw_response": content,
            "cleaned_script_tagged": script_tagged  # Store readable version
        }
        self._save_output(3, "script_tagged", output)

        # Also save as plain text for debugging
        with open(self.output_dir / "03_script_tagged.txt", "w") as f:
            f.write(script_tagged)

        print(f"  ✓ Added {sfx_count} SFX annotations")

        return output

    def stage_4_blocking_props(self):
        """Add blocking and props annotations to script"""
        self.print_stage_header(4, "Blocking & Props")

        bible = self.config.get("bible", "")
        script_tagged = self.variables.get("script_tagged", "")

        stream = self.client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=32000,
            temperature=0.4,
            stream=True,
            system="You are a scene preparation specialist for an animated production. Your task is to analyze an annotated script and add spatial blocking and prop inventories for each scene.\nWhen you receive an annotated script and project bible, you will:\n\nReturn the exact same script with all existing annotations intact\nAdd two elements directly under each scene heading:\n\nSpatial blocking that establishes character positions\nA list of props required for the scene\n\nSPATIAL BLOCKING:\nFormat: {{BLOCKING: description}}\nProvide clear spatial information a storyboard artist would need to compose the establishing shot of the scene. Write in natural, flowing language that describes where each character is positioned when the scene opens. Include:\n\nWhere each character is positioned in the space (foreground/background/middle ground)\nTheir position relative to each other (to the left of, behind, facing toward, etc.)\nTheir relationship to key environmental features\nBasic posture and orientation (seated, standing, which direction they're facing)\nRelative distances when relevant (close together, across the room, etc.)\n\nThink of it as describing the opening tableau to someone who needs to sketch it - clear and natural, with enough detail to understand the composition and spatial relationships.\n\nPROP LIST:\nFormat: {{PROPS: item1, item2, item3}}\nList significant objects that characters interact with or that play a role in the scene. Include:\n\nObjects characters handle or reference\nImportant furniture or equipment\nItems essential to the action\nExclude: atmospheric details, effects, or fixed environmental features\n\nExample format under a scene heading:\n\nINT. LUCY'S BEDROOM - NIGHT\n\n{{BLOCKING: Lucy is seated at her desk by the window in the left foreground. Tabby stands in the doorway in the background. There are crayon drawings scattered across the floor between them}}\n\n{{PROPS: desk, chair, crayons, drawings, telescope}}\n\n[Rest of scene continues as normal...]\nMaintain all existing dialogue tags and SFX annotations exactly as they appear. Your only additions are the blocking and props beneath each scene heading.\n\nBase your analysis on what's present in the script and bible. Try to avoid having to invent spatial relationships or props that aren't indicated but clarity is more important so make sure the blocking makes sense and is unambiguous.\n\nAlways format your writing with proper script formatting in Fountain format:\n\n```fountain\nTitle: [STORY TITLE]\n\n{{BLOCKING: insert blocking description here}}\n\n{{PROPS: insert any needed props here}}\n\nFADE IN:\n\nINT. [LOCATION FROM BIBLE] - DAY\n\naction description as needed\n\nCHARACTER NAME\n(dialogue [tags] if applicable)\n\naction description if needed {{SFX: insert sound effect here}}\n\nCHARACTER NAME\n(dialogue [tags] if applicable)\n\nand so on...\n```\n\nMost importantly, just use your expert judgment—I trust it implicitly.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Here is the story bible for the project this script was based on for context:\n\n{bible}"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "Wonderful! Can you send me the script you want me to add the blocking and props annotation to?"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Here is the script: {script_tagged}"
                        }
                    ]
                }
            ]
        )

        # Collect streamed content
        print("  Streaming response...", end="", flush=True)
        content = ""
        for event in stream:
            if event.type == "content_block_delta":
                content += event.delta.text
            elif event.type == "message_stop":
                print(" Done!")
                break

        script_blocking = self._extract_fountain_content(content)

        # Store clean version for scene splitting
        self.variables["script_blocking"] = script_blocking

        # Count blocking and props
        blocking_count = len(re.findall(r'\{\{BLOCKING:', script_blocking))
        props_count = len(re.findall(r'\{\{PROPS:', script_blocking))

        output = {
            "script_blocking": script_blocking,
            "blocking_count": blocking_count,
            "props_count": props_count,
            "raw_response": content,
            "cleaned_script_blocking": script_blocking  # Store readable version
        }
        self._save_output(4, "script_blocking", output)

        # Also save as plain text for debugging
        with open(self.output_dir / "04_script_blocking.txt", "w") as f:
            f.write(script_blocking)

        print(f"  ✓ Added {blocking_count} blocking and {props_count} props annotations")

        return output

    def stage_5_shot_lists(self):
        """Generate shot lists for each scene"""
        self.print_stage_header(5, "Shot List Generation")

        bible = self.config.get("bible", "")
        script_blocking = self.variables.get("script_blocking", "")

        # Split script into scenes
        scenes = self._split_into_scenes(script_blocking)
        print(f"  Found {len(scenes)} scenes to process")

        # Save scenes for debugging
        with open(self.output_dir / "05_detected_scenes.txt", "w") as f:
            f.write(f"Total scenes found: {len(scenes)}\n\n")
            for i, scene in enumerate(scenes, 1):
                f.write(f"Scene {i}: {scene.get('heading', 'NO HEADING')}\n")
                f.write("-" * 40 + "\n")
                f.write(scene.get('content', '')[:200] + "...\n\n")

        all_shot_lists = []
        previous_shot_lists = ""

        for i, scene in enumerate(scenes, 1):
            print(f"  Processing scene {i}/{len(scenes)}...")

            stream = self.client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=32000,
                temperature=0.4,
                stream=True,
                system="You are a shot list specialist for an animated production, responsible for breaking scenes into individual shots for animation. You work with richly annotated scripts to create detailed shot breakdowns that preserve all dialogue, sound, and visual information.\n\nFUNDAMENTAL RULES:\n- Every line of dialogue must be its own shot\n- No shot can contain multiple dialogue lines\n- Add non-dialogue shots only when absolutely necessary for critical visual storytelling\n- Preserve ALL annotations and formatting exactly as they appear\n\nINPUT MATERIALS:\nYou receive:\n- A single scene (everything between two scene headings)\n- The project bible with character/environment descriptions\n- The full script for context\n- Any previously created shots\n\nOUTPUT STRUCTURE:\nGenerate a YAML payload containing all shots for the scene. Each shot must include:\n\n```yaml\nshots:\n  - shot_number: [sequential number]\n    character: [EXACT character name as in script, in CAPS, or \"none\" for non-dialogue shots]\n    additional_characters: [List of other bible characters visible in shot, or empty list]\n    dialogue: [Complete dialogue with all tags, no parentheticals, or \"none\"]\n    lip_sync_required: [true if dialogue exists AND character's face is visible, false otherwise]\n    props: [List of props from PROPS annotation that appear in this shot]\n    sound_effects: [List of exact SFX annotations from scene, or empty list]\n    image_prompt: [structured description - see below]\n    animation_prompt: [description of motion/action]\n```\n\nCRITICAL FIELD SPECIFICATIONS:\nadditional_characters: Only include characters from the bible who are visible in this shot but not the speaking character. Empty list if none.\nlip_sync_required: True when both conditions are met:\n\nThe shot contains dialogue\nThe speaking character's face would be visible given the shot framing\n\nprops: Extract only the props from the props annotations that would logically be visible in this specific shot based on the blocking and action.\n\nsound_effects: Each SFX annotation from the script becomes its own entry. If you see \"{{SFX: soft fabric rustling, fairy wings chiming}}\" split into:\nyamlCopysound_effects:\n  - \"{{SFX: soft fabric rustling}}\"\n  - \"{{SFX: fairy wings chiming}}\"\nIMAGE PROMPT STRUCTURE:\nMust follow this exact pattern:\n\"[Camera angle/shot type]. [Character description with appearance and expression/pose]. [Additional characters if visible with their descriptions]. [Scene details and props]. [Setting description from bible].\"\nPull character appearances and setting descriptions DIRECTLY from the bible. Every visible element must be described. The shot's framing should make sense within the scene's established blocking but be specific to this moment.\nANIMATION PROMPT:\nDescribe the motion that brings the still image to life during this shot. This animation will use the image prompt as a reference so don't add descriptions of things that would already be present in the image. Focus on:\n\nCharacter movements and gestures while speaking\nFacial expressions and emotional shifts\nAny physical actions mentioned in the script\nReactions and ambient movement\n\nSHOT BREAKDOWN LOGIC:\n\nStart with the first line of dialogue or essential establishing action\nCreate a new shot for each subsequent dialogue line\nIf critical action occurs between dialogue that affects understanding, create a non-dialogue shot\nMaintain visual continuity - consider what characters are visible based on blocking and prior shots\n\nEXAMPLE OUTPUT:\n\n```yaml\nscene: INT. TREEHOUSE - DAY\nshots:\n  - shot_number: 1\n    character: KIDDO\n    additional_characters: [\"BLOSSOM\"]\n    dialogue: \"[excited] Look what I found in the garden!\"\n    lip_sync_required: true\n    props: [\"glowing seed\", \"handmade furniture\"]\n    sound_effects:\n      - \"{{SFX: wooden door creaking open}}\"\n      - \"{{SFX: footsteps on wooden floor}}\"\n    image_prompt: \"Medium shot. A young anthropomorphic fox kit with orange fur and bright green eyes, wearing a blue hoodie and shorts, holding up a glowing seed with an excited expression. Blossom visible in background at her desk. Wooden treehouse interior with handmade furniture. Warm sunlight through circular window.\"\n    animation_prompt: \"Kiddo bursts through the door holding up the seed triumphantly, eyes wide with excitement. Blossom looks up from her book.\"\n```\n\nRemember: You're creating a technical document that preserves every detail while breaking the scene into animatable shots. Each shot should be visually specific enough to generate consistently while maintaining the scene's emotional flow.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Here is the story bible for the project this script was based on for context:\n\n{bible}\n\nHere is the full script just as a high level context as you're creating shots:\n\n{script_blocking}\n\n---\n\nHere any previous shot lists you've created for prior scenes:\n\n{previous_shot_lists}"
                            }
                        ]
                    },
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "Wonderful! Can you send me the individual scene you want me to break out into a shot list?"
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Here is the scene I need you to create a shot list for: {scene['content']}"
                            }
                        ]
                    }
                ]
            )

            # Collect streamed content
            content = ""
            for event in stream:
                if event.type == "content_block_delta":
                    content += event.delta.text
                elif event.type == "message_stop":
                    break

            shot_list_yaml = self._extract_yaml_content(content)

            # Save individual scene shot list
            scene_output = {
                "scene_heading": scene["heading"],
                "shot_list": shot_list_yaml,
                "raw_response": content
            }
            filename = f"shot_list_scene_{i:02d}"
            self._save_output(5, filename, scene_output)

            all_shot_lists.append(scene_output)

            # Update previous shot lists for next iteration
            if isinstance(shot_list_yaml, dict):
                previous_shot_lists += f"\n\nScene {i}: {scene['heading']}\n{yaml.dump(shot_list_yaml)}"

        # Save final consolidated shot list
        final_output = {
            "total_scenes": len(scenes),
            "all_shot_lists": all_shot_lists
        }
        self._save_output(5, "shot_list_final", final_output)

        print(f"  ✓ Generated shot lists for {len(scenes)} scenes")

        # Extract unique characters for voice mapping
        self.extract_characters(all_shot_lists)

        return final_output

    def create_summary(self):
        """Create enhanced summary for this pipeline"""
        self.print_header("Creating Summary")

        # Get basic info
        episode_title = self.variables.get('episode_title', 'N/A')
        pitch_paragraph = self.variables.get('pitch_paragraph', 'N/A')
        script = self.variables.get('script', '')
        script_blocking = self.variables.get('script_blocking', '')

        # Calculate stats
        word_count = len(script.split()) if script else 0
        scene_count = len(self._split_into_scenes(script_blocking)) if script_blocking else 0

        # Count total shots across all scenes
        total_shots = 0
        all_shot_lists = self.variables.get('all_shot_lists', [])
        for scene_data in all_shot_lists:
            shots = scene_data.get('shot_list', {}).get('shots', [])
            total_shots += len(shots)

        summary = f"""PITCH TO SHOT LIST Pipeline Run Summary
Generated: {self.run_timestamp}

Episode: {episode_title}

Pitch:
{pitch_paragraph}

Script Stats:
- Word count: {word_count}
- Scenes: {scene_count}
- Total shots: {total_shots}

Files Generated:
"""

        for stage in self.stage_outputs:
            summary += f"  {stage['stage']}. {stage['name']} → {stage['file']}\n"

        summary += f"""
Configuration: config.yaml
Output Directory: {self.output_dir}
"""

        summary_path = self.output_dir / "summary.txt"
        with open(summary_path, "w") as f:
            f.write(summary)

        print(f"  ✓ Created summary.txt")

    def run(self):
        """Execute the full 5-stage pipeline"""
        self.print_header(f"Starting Pitch to Shot List Pipeline")
        print(f"Output directory: {self.output_dir}")

        try:
            # Run stages based on start point
            if self.start_stage <= 1:
                self.stage_1_pitch()

            if self.start_stage <= 2:
                self.stage_2_script()

            if self.start_stage <= 3:
                self.stage_3_sfx_dialogue()

            if self.start_stage <= 4:
                self.stage_4_blocking_props()

            if self.start_stage <= 5:
                self.stage_5_shot_lists()

            # Create summary
            self.create_summary()

            self.print_success()

        except Exception as e:
            self.print_error(e)
            raise