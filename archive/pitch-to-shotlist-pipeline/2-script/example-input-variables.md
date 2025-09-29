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

# {{kiddo_script_instruction}}:

## Info:
For this variable we will either pass in a preset string, a preset string appended with a string that the user enters or we will pass in null. On the frontend there will be an array selector with 3 options, they will be: Include Generic Kiddo, Inlcude Specific Kiddo, None.  If the user selects 'Include Generic Kiddo' we will pass in a preset string. if the user selects 'Inlcude Specific Kiddo' we will pass in a preset string appended with whatever text the user has added for the specific kiddo in a text box. If the user selects 'None' we will pass in nothing for this variable.

## Example (user has selected: Inlcude Generic Kiddo)
```text
Note: The character 'Kiddo' appearing in this pitch represents the child watching this episode - written into the story itself. Kiddo doesn't appear in the story Bible because they're dynamically included for each viewer. Treat Kiddo as a full character who interacts with others and shapes events just like anyone else. Keep Kiddo universally relatable: refer to them by name rather than pronouns, and avoid any physical or gendered attributes. Kiddo should feel like the story's heart - defined by their role in the adventure rather than their appearance.
```

## Example (user has selected: Inlcude Specific Kiddo)
```text
Note: The character 'Kiddo' appearing in this pitch represents the specific child watching this episode - written as themselves within the story. Kiddo doesn't appear in the story Bible because they're dynamically included for each viewer. Treat Kiddo as a full character who interacts with others and shapes events just like anyone else. Use the details below to inform how Kiddo speaks, acts, and engages with the world, making them feel authentically represented throughout the script.

Details about Kiddo:

[insert user added details about Kiddo]
```

## Example (user has selected: None)
null

---

# {{episode_title}}:

## Info:
this will be the episode title that gets parsed/extracted from the pitch generation step output.

## Example
```text
The Waiting Game
```

---

# {{pitch_paragraph}}:

## Info:
this will be the pitch paragraph that gets parsed/extracted from the pitch generation step output.

## Example
```text
Kiddo bounces from foot to foot in Lucy's playroom, desperately wanting to play with the new puzzle Lucy's mom just brought home, but Lucy's mom says they have to wait until after lunch—so naturally, Sparkles and Blossom decide to help speed up time, completely misunderstanding how waiting works. The fairies try everything: pushing clock hands forward (which just breaks the clock), making lunch disappear faster (by hiding sandwich pieces around the house), and even attempting to cast a "hurry-up spell" using Lucy's bubble wand, which only creates a spectacular mess of soap bubbles that nearly reveals their existence when Muffin starts batting at them. As their increasingly frantic attempts to eliminate waiting time create more chaos—and actually make lunch take longer as Lucy's mom searches for the missing sandwich pieces—Blossom discovers Lucy's egg timer and becomes fascinated by how it measures waiting, while Sparkles races around trying to make everything in the house go faster, from spinning the ceiling fan to fast-forwarding Lucy's mom's music. When Kiddo finally sits down and starts building a tower with blocks to pass the time, showing the fairies how doing something gentle makes waiting easier, Sparkles and Blossom realize they've been thinking about patience all wrong—it's not about making time go faster, but about finding peaceful things to do while time passes on its own, and soon all three are working together to create the most elaborate block castle ever, making the waiting time feel magical instead of endless, until suddenly Lucy's mom announces lunch is over and it's puzzle time, leaving everyone amazed at how quickly the time passed when they stopped fighting against it.
```

---

# {{script_user_message}}:

## Info:
this variable represents a string that the user writes in to steer the script creatively. it will always be passed in as plain text. although it's format is entirely unimportant. It might also contain some specific direction about how to work with the kiddo character creatively per the given project bible.

## Example:
```text
I want you to focus on funny dialogue in this one. Also, in the Flutter project, the Kiddo character should always be one of the fairies.
```