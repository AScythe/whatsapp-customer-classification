---
description: Scaffold a new OpenCode skill or command. Usage: /scaffold skill <name> OR /scaffold command <name>
---

You are scaffolding a new OpenCode resource. The type is "$1" and the name is "$2".

Follow the instructions below based on the type.

---

## If type is "skill"

Create the following file in the CURRENT PROJECT directory:
`.opencode/skills/$2/SKILL.md`

Use this template for the SKILL.md contents:
```
---
name: $2
description: <ask the user for a short description, or infer from the name>
---

## What I do
- <describe what this skill does>

## When to use me

Use this when <describe the trigger scenario>.
```

Make sure:
The folder name matches the `name` field in frontmatter.
The name is lowercase alphanumeric with single-hyphen separators (no leading/trailing hyphens, no consecutive hyphens). The description is 1-1024 characters.

---

## If type is "command"

Create the following file in the CURRENT PROJECT directory:

`.opencode/commands/$2.md`

Use this template for the command file contents:

```
---
description: <ask the user for a short description, or infer from the name>
---

<prompt template for what this command should do>
```

Make sure:
- The file is named `$2.md`.
- The description is concise and clear.

---

## If type is "global-skill"

Create the following file in the GLOBAL config directory: 

`~/.config/opencode/skills/$2/SKILL.md`

Use the same SKILL.md template as the "skill" type above.

---

## If type is "global-command"

Create the following file in the GLOBAL config directory: 
`~/.config/opencode/commands/$2.md`

Use the same command template as the "command" type above.

---

## After creating the file

1. Show the user the file that was created and its full path.
2. Confirm the resource was scaffolded successfully.
3. Remind the user they can edit the file to customize it further.