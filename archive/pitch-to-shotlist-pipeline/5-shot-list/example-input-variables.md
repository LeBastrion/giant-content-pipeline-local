# {{bible}}:

## Info:
the bible variable will always get a formatted project bible passed in. The format isnt important, the llm is just using this text for context about the project

## Example:
```markdown
# Flutter

## Overview

Flutter follows two whimsical young fairies-in-training—Sparkles and Blossom—assigned to a curious and kind-hearted 4-year-old human girl named Lucy. Acting as invisible guardians, they live in Lucy's home, hidden in nooks and crannies, tasked with quietly helping her thrive. There's just one catch: they're still learning how the human world works.

Each episode centers on the fairies helping Lucy with something her mom thinks she's lost—like her toothbrush, a missing sock, or a library book. But because Sparkles and Blossom don't understand what these objects are or why they matter, they must investigate their purpose, track them down, and return them—all without being seen.

As they solve these everyday mysteries, the fairies (and viewers) discover the why behind common routines and habits. Whether it's brushing your teeth, reading before bed, or putting toys away, Flutter helps preschoolers learn the "why" behind the "what" through wonder, imagination, and a little bit of magic.

## Thematic Elements

At its heart, Flutter explores themes of curiosity, care, and discovery through the eyes of two personal fairies helping a little girl navigate her everyday world. The show celebrates how children perceive magic in the ordinary—the sparkle in a sunbeam, the mystery of a lost object, or the... and so on
```
---

# {{script_blocking}}:

## Info:
this variable represents the same short short script format, but this time its annotated with sfx cues and the dialogue is slightly changed for the TTS engine.

## Example:
```fountain
Title: The Crayon Case

FADE IN:

INT. THE NEST - DAY

{{BLOCKING: Kiddo bursts through the sparkling entrance in the background, wings fluttering wildly. Sparkles is lounging in her hammock in the left foreground. Blossom sits at the petal-shaped table on the right, her magical notebook open in front of her.}}

{{PROPS: purple crayon stub, hammock, magical notebook, telescope (paper towel tube), button chairs, petal table}}

Sunlight filters through the chandelier crystals, casting rainbow patterns across button chairs and petal tables. KIDDO tumbles through the sparkling entrance, wings fluttering wildly, clutching a MASSIVE PURPLE CRAYON STUB like a trophy.

KIDDO
[breathless, excited] Found it! The magic disappearing wand!

SPARKLES bounces up from her hammock, pink wings shimmering with excitement. {{SFX: soft fabric rustling, fairy wings chiming}}

SPARKLES
[gasps] A disappearing wand? Let me
and so on...
```

---

# {{previous_shot_lists}}

## Info:
This will be all previous shot lists in the order that they were generated. So it would be this shot list for scene one and then scene two and then scene three, for example. And then the current scene we would be writing a shot list for (shot list scene) would be scene four in that example.

## Example:
```fountain
scene: INT. THE NEST - DAY
shots:
  - shot_number: 1
    character: KIDDO
    dialogue: "[breathless, excited] Found it! The magic disappearing wand!"
    sound_effects: []
    image_prompt: "Medium shot from inside the Nest. Kiddo, a young fairy with iridescent wings and wild curly hair, bursts through the sparkling entrance in the center clutching a massive purple crayon stub like a trophy, wings fluttering wildly with an excited expression. Sparkles visible lounging in her hammock to the left, Blossom at the petal table to the right. The Nest constructed from soft found materials like buttons, ribbons, fabric, flower petals, and shiny beads, with twinkling repurposed holiday bulbs casting gentle glow, sunlight filtering through chandelier crystals creating rainbow patterns."
    animation_prompt: "Kiddo tumbles through the entrance with wings fluttering frantically, holding the crayon high above their head triumphantly. Sparkles starts to sit up in her hammock with interest. Blossom looks up from her notebook."

  - shot_number: 2
    character: SPARKLES
    dialogue: "[gasps] A disappearing wand? Let me see, let me SEE!"
    sound_effects:
      - sfx: "{{SFX: soft fabric rustling}}"
        timing: 0
      - sfx: "{{SFX: fairy wings chiming}}"
        timing: 15
    image_prompt: "Close-up on Sparkles. An 8-year-old fairy with pink-tinted wings, bubble ponytails, sparkly tunic and mismatched socks, bouncing up from her hammock with eyes wide and shimmering with excitement, arms reaching forward eagerly. The Nest's cozy interior visible in background with button chairs and twinkling lights."
    animation_prompt: "Sparkles bounces energetically up from the hammock, her pink wings shimmering and chiming as she moves. Her arms reach out toward Kiddo with grabbing motions, eyes sparkling with curiosity."

  - shot_number: 3
    character: BLOSSOM
    dialogue: "[cautious] Hold on—where exactly did you find this?"
    sound_effects:
      - sfx: "{{SFX: pages fluttering softly}}"
        timing: 0
    image_prompt: "Medium shot. Blossom, an 8-year-old fairy with lavender wings, glasses, tidy bun, wearing a pocketed apron full of pencils and string, sits at the petal-shaped table adjusting her glasses with one hand while pulling her magical notebook closer with the other, looking cautious and analytical. Her notebook open showing sketches of human objects. The Nest's warm handmade details visible around her."
    animation_prompt: "Blossom adjusts her glasses with a thoughtful gesture, then pulls her magical notebook filled with sketches toward her, pages fluttering softly as she prepares to take notes."
```

---

# {{shot_list_scene}}

## Info:
This would be the current scene we are writing a shot list for. Shot lists get written scene by scene by scene until all scenes are complete. 

## Example:
```fountain
INT. THE NEST - DAY

{{BLOCKING: Kiddo bursts through the sparkling entrance in the center, clutching a massive purple crayon stub. Sparkles is lounging in her hammock to the left. Blossom sits at the petal-shaped table on the right with her notebook open in front of her}}

{{PROPS: purple crayon stub, hammock, button chairs, petal table, magical notebook, telescope (paper towel tube)}}

Sunlight filters through the chandelier crystals, casting rainbow patterns across button chairs and petal tables. KIDDO tumbles through the sparkling entrance, wings fluttering wildly, clutching a MASSIVE PURPLE CRAYON STUB like a trophy.

KIDDO
[breathless, excited] Found it! The magic disappearing wand!

SPARKLES bounces up from her hammock, pink wings shimmering with excitement. {{SFX: soft fabric rustling, fairy wings chiming}}

SPARKLES
[gasps] A disappearing wand? Let me see, let me SEE!

BLOSSOM adjusts her glasses, pulling out her magical notebook filled with sketches of human objects. {{SFX: pages fluttering softly}}

BLOSSOM
[cautious] Hold on—where exactly did you find this?

KIDDO
[proud] Lucy's art table! She used it and POOF—her yellow crayon vanished!

From below, LUCY'S MOM's voice drifts up through the floorboards. {{SFX: muffled footsteps from below}}

LUCY'S MOM (O.S.)
[distant, muffled] Lucy, honey, where did your yellow crayon go?

The three fairies flutter to their telescope (made from a paper towel tube) and peer down. {{SFX: tiny wings buzzing}} Lucy sits at her art table, shoulders slumped, staring at an unfinished rainbow missing its sun.

SPARKLES
[concerned] Oh no! She can't finish her rainbow!

KIDDO
Should I wave the wand and make it reappear?

Kiddo waves the purple crayon dramatically. Fairy dust swirls everywhere, making Blossom sneeze. {{SFX: magical sparkles tinkling}}

BLOSSOM
[sneezes] Wait wait WAIT! Let me measure this first.

She holds up the crayon against her notebook drawings, comparing sizes and shapes.

BLOSSOM (CONT'D)
[thoughtful] According to my notes, this matches a "coloring stick"...

SPARKLES
[impatient] We don't have time for notes! Lucy needs her sunshine-maker!

KIDDO
[worried] But what if I accidentally disappear something else?

BLOSSOM
Good point. Let's investigate properly.
```