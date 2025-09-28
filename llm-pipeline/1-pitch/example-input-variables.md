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

# {{pitch_user_message}}:

## Info:
this variable represents a string that the user writes in to steer what the story is about. it will always be passed in as plain text. although it's format is entirely unimportant. It might also contain some specific direction about how to work with the kiddo character creatively per the given project bible.

## Example:
```text
Give me an episode that teaches the importance of patience.
```

---

# {{kiddo_pitch_instruction}}:

## Info:
For this variable we will either pass in a preset string, a preset string appended with a string that the user enters or we will pass in null. On the frontend there will be an array selector with 3 options, they will be: Include Generic Kiddo, Inlcude Specific Kiddo, None.  If the user selects 'Include Generic Kiddo' we will pass in a preset string. if the user selects 'Inlcude Specific Kiddo' we will pass in a preset string appended with whatever text the user has added for the specific kiddo in a text box. If the user selects 'None' we will pass in nothing for this variable.

## Example (user has selected: Inlcude Generic Kiddo)
```text
For this episode I want you to Include a character named 'Kiddo' who represents the child watching this episode - written into the story itself. Kiddo is a full character, interacting with others and shaping events just like anyone else. Open with Kiddo if possible to establish their presence early. Keep Kiddo universally relatable: refer to them by name rather than pronouns, and avoid any physical or gendered attributes. Kiddo should feel like the story's heart - defined by their role in the adventure rather than their appearance.
```

## Example (user has selected: Inlcude Specific Kiddo)
```text
Include a character named 'Kiddo' who represents the specific child watching this episode - not just as a viewer, but as themselves within the story. Kiddo is a full character, interacting with others and shaping events just like anyone else. Open with Kiddo if possible to establish their presence early. Weave the following details naturally into how Kiddo appears and acts in the story, making them feel authentically represented. Kiddo should feel like the story's heart - bringing their unique personality and interests into the adventure.

Details about Kiddo:

[insert user added details about Kiddo]
```

## Example (user has selected: None)
null

---
