# Pitch step

## input variables - variables passed in to api call

{{bible}}
{{kiddo_pitch_instruction}}
{{pitch_user_message}}

## output variables - variables that must be extracted/parsed from output

{{episode_title}}
{{pitch_paragraph}}

---

# Script step

## input variables - variables passed in to api call

{{bible}}
{{kiddo_script_instruction}}
{{episode_title}}
{{pitch_paragraph}}
{{script_user_message}}

## output variables - variables that must be extracted/parsed from output

{{script}}

---

# Script sfx and dialogue

## input variables - variables passed in to api call

{{bible}}
{{script}}

## output variables - variables that must be extracted/parsed from output

{{script_tagged}}

---

# Script blocking and props

## input variables - variables passed in to api call

{{bible}}
{{script_tagged}}

## output variables - variables that must be extracted/parsed from output

{{script_blocking}}

---

# shot lists

## input variables - variables passed in to api call

{{bible}}
{{script_blocking}}
{{previous_shot_lists}}
{{shot_list_scene}}

## output variables - variables that must be extracted/parsed from output

{{shot_list}} - CRUCIALLY THERE WILL BE ONE SHOT LIST FOR EVERY SCENE SO WE WILL HAVE TO FIND A WAY TO STORE EACH SHOT LIST UNIQUELY