---
name: shadcn
description: 'Select, add, compose, and style shadcn/ui components following a design spec. Handles component imports, composition, accessibility, and CLI operations. Use after frontend-design has produced a spec, or for trivial mechanical changes where no design decision is needed, or triggered when the user says "add component", "build component", "shadcn", "shadcn/ui", "UI component", or similar.'
---

## What I Do

Implement frontend components using shadcn/ui. Component structure and composition follow shadcn conventions; visual style defers to the `frontend-design` spec.

## Principles

1. **Use existing components first.** Run `npx shadcn@latest search` to check registries before writing custom UI. Check community registries too (`@magicui`, `@tailark`).
2. **Compose, don't reinvent.** Settings page = Tabs + Card + form controls. Dashboard = Sidebar + Card + Chart + Table.
3. **Use built-in variants before custom styles.** `variant="outline"`, `size="sm"`, etc.
4. **Use semantic colors.** `bg-primary`, `text-muted-foreground` — never raw values like `bg-blue-500`.

## Boundaries

- **Mode:** Build — writes component code, updates Tailwind config and CSS variables.
- **Ordering:** Always invoke after frontend-design. Never use both simultaneously.
- **Component structure** — use shadcn patterns for imports, composition, accessibility
- **Visual deferral** — colors, typography, spacing, motion come from the design spec; never let shadcn defaults override intentional design decisions
- **No design decisions** — if no design spec exists and the change is non-trivial, raise: "No design spec found, run frontend-design first"

## When to Use

Invoke after `frontend-design` has produced a spec, when:
- Selecting and adding shadcn components
- Writing or refactoring component code
- Implementing component structure, imports, and composition

**Trivial-change carveout:** For purely mechanical changes (no aesthetic decision needed), may run without a prior design spec. When in doubt, ask for the spec first.

## Conflict Resolution

When both `frontend-design` and `shadcn` are active:

| Owned by shadcn | Owned by frontend-design |
|------------------|---------------------------|
| Component selection, imports, composition, accessibility | Color, typography, spacing, motion, aesthetics |
| API patterns, responsive breakpoints | Visual hierarchy and layout philosophy |
| Component structure and variant usage | Design tokens (CSS variable values) |

**Rule:** Design spec wins for visual style. shadcn wins for API/composition. Never let shadcn's defaults override an intentional design decision.

## Phase 0: Prerequisites

- [ ] Read the design spec from `frontend-design` — all sections must be available
- [ ] Verify spec has all required sections: aesthetic direction, color system, typography scale, motion principles, layout philosophy, design token mapping
- [ ] Verify the Design Token Mapping table is complete — every color, font, radius, shadow, spacing value has an exact hex/value and a target config key
- [ ] If spec is missing a required section or has an incomplete token mapping, raise early: "Design spec missing required section: [X]. Run frontend-design first." Do not proceed with default shadcn values for skipped sections.

## Project Context

On every interaction, run the project context command first:
```bash
npx shadcn@latest info --json
```

The JSON output contains these key fields that guide all subsequent decisions:

| Field | What it tells you |
|-------|-------------------|
| `aliases` | Import prefix (`@/`, `~/`) — never hardcode paths |
| `isRSC` | If `true`, components using `useState`/`useEffect`/browser APIs need `"use client"` |
| `tailwindVersion` | `"v4"` uses `@theme inline` blocks; `"v3"` uses `tailwind.config.js` |
| `tailwindCssFile` | The one CSS file to edit — never create a new one |
| `style` | Visual treatment (`nova`, `vega`, etc.) |
| `base` | Primitive library (`radix` or `base`) — affects component APIs |
| `iconLibrary` | Determines icon package (`lucide-react`, `@tabler/icons-react`, etc.) |
| `resolvedPaths` | Exact file-system destinations for components, utils, hooks |
| `framework` | Routing conventions (Next.js App Router vs Vite SPA) |
| `packageManager` | Use for all non-shadcn dependency installs |
| `preset` | Resolved preset code — use `preset resolve --json` for structured values |

Use `npx shadcn@latest docs <component>` to get documentation and example URLs for any component.

## Essential Rules

### Styling & Tailwind
- Use semantic colors (`bg-primary`, `text-muted-foreground`) — never raw values like `bg-blue-500`
- No `space-x-*` or `space-y-*` — use `flex` with `gap-*`
- Use `size-*` when width and height are equal (`size-10` not `w-10 h-10`)
- Use `truncate` shorthand, not `overflow-hidden text-ellipsis whitespace-nowrap`
- No manual `dark:` overrides — use semantic tokens
- Use `cn()` for conditional classes, not manual ternaries
- No manual `z-index` on overlay components (Dialog, Sheet, Popover handle their own)

### Forms & Inputs
- Forms use `FieldGroup` + `Field` — never raw `div space-y-*` layouts
- `InputGroup` uses `InputGroupInput`/`InputGroupTextarea` — never raw `Input` inside `InputGroup`
- Option sets (2–7) use `ToggleGroup` — don't loop `Button` with manual active state
- `FieldSet` + `FieldLegend` for related checkboxes/radios
- Validation: `data-invalid` on `Field`, `aria-invalid` on the control

### Component Structure
- Items always inside their Group: `SelectItem` → `SelectGroup`, `DropdownMenuItem` → `DropdownMenuGroup`
- Dialog/Sheet/Drawer always need a Title (`className="sr-only"` if visually hidden)
- Full Card composition: `CardHeader`/`CardTitle`/`CardDescription`/`CardContent`/`CardFooter`
- `Avatar` always needs `AvatarFallback`
- `TabsTrigger` must be inside `TabsList`
- Button has no `isPending` — compose with `Spinner` + `data-icon` + `disabled`

### Use Components, Not Custom Markup
- Callouts → `Alert`
- Empty states → `Empty`
- Toast → `sonner`'s `toast()`
- Separator → `Separator` (not `<hr>` or `border-t`)
- Loading placeholders → `Skeleton`
- Badges → `Badge`

### Icons
- Icons in `Button` use `data-icon="inline-start"` or `data-icon="inline-end"` — no sizing classes on icons inside components
- Pass icons as objects, not string keys: `icon={CheckIcon}`

## Key Patterns

```tsx
// Form layout
<FieldGroup>
  <Field>
    <FieldLabel htmlFor="email">Email</FieldLabel>
    <Input id="email" />
  </Field>
</FieldGroup>

// Icons in buttons
<Button>
  <SearchIcon data-icon="inline-start" />
  Search
</Button>

// Spacing: gap, not space
<div className="flex flex-col gap-4">

// Equal dimensions
<Avatar className="size-10">

// Semantic colors
<Badge variant="secondary">+20.1%</Badge>
```

## Component Selection

| Need | Use |
|------|-----|
| Button/action | `Button` with appropriate variant |
| Form inputs | `Input`, `Select`, `Combobox`, `Switch`, `Checkbox`, `RadioGroup`, `Textarea` |
| Toggle 2-5 options | `ToggleGroup` + `ToggleGroupItem` |
| Data display | `Table`, `Card`, `Badge`, `Avatar` |
| Navigation | `Sidebar`, `NavigationMenu`, `Breadcrumb`, `Tabs`, `Pagination` |
| Overlays | `Dialog` (modal), `Sheet` (side panel), `Drawer` (bottom sheet) |
| Feedback | `sonner` (toast), `Alert`, `Progress`, `Skeleton`, `Spinner` |
| Charts | `Chart` (wraps Recharts) |
| Empty states | `Empty` |
| Menus | `DropdownMenu`, `ContextMenu`, `Menubar` |
| Tooltips | `Tooltip`, `HoverCard`, `Popover` |

## Upstream Reference

For the full rulebook covering edge cases, see the official shadcn skill:
- `skills.sh/shadcn/ui/shadcn` — complete rules for styling, forms, composition, icons, CLI
- Detailed rule files: `styling.md`, `forms.md`, `composition.md`, `icons.md`, `base-vs-radix.md`, `cli.md`

Run `npx shadcn@latest docs <component>` and fetch the URLs for component-specific API reference.

## Workflow

### Step 0: Parse Design Spec & Extract Tokens

If a design spec exists from `frontend-design`, read the spec's **Design Token Mapping** table. Extract every token and its target:

- Colors → note hex values and their target config keys
- Font → note the font name and fallback stack
- Border radius, spacing, shadows → note exact values
- Motion timing, container width → note CSS variable names

If no spec exists and the change is non-trivial, raise: "No design spec found, run frontend-design first." For trivial mechanical changes, proceed with shadcn defaults.

### Steps 1-7

1. Get project context: `npx shadcn@latest info --json`
2. Check installed components (list `resolvedPaths.ui` directory)
3. **Apply design tokens** — write the extracted tokens into:
   - `tailwind.config.js` `theme.extend.{colors,fontFamily,borderRadius,spacing,boxShadow,maxWidth}`
   - `global.css` CSS variable layer (semantic tokens referencing the config)
4. Find/add components: `npx shadcn@latest search` / `npx shadcn@latest add`
5. **Get docs** — `npx shadcn@latest docs <component>` → fetch the returned URLs. Always do this before writing code. It ensures you're working with the correct API and usage patterns rather than guessing.
6. **Registry must be explicit** — When the user asks to add a block or component from a registry, do not guess which registry. If no registry is specified (e.g. "add a login block" without `@shadcn`, `@tailark`, etc.), ask which registry to use. Never default to one on behalf of the user.
7. Import and compose following the rules above
8. Override default variants/colors to match the design spec

### Post-Install Verification

After adding or updating components, verify correctness:

1. **Read the added files** — check for missing sub-components (e.g. `SelectItem` without `SelectGroup`), missing imports, incorrect composition.
2. **Check icon library alignment** — if the registry item imports from `lucide-react` but the project uses `hugeicons` (from `iconLibrary` in project context), swap imports accordingly.
3. **Verify no default shadcn colors leaked through:**
   ```bash
   grep -rn "bg-blue-\|bg-purple-\|bg-zinc-\|bg-slate-\|text-blue-\|text-purple-" --include="*.tsx" --include="*.ts" frontend/src/
   ```
   Any matches mean shadcn defaults surfaced instead of design spec tokens. Fix with semantic tokens from the spec.
4. **Run build or type check** — `npx tsc --noEmit` to catch any import errors or type mismatches.

### Updating Components

When updating an existing component from upstream while preserving local changes:

1. Preview: `npx shadcn@latest add <component> --dry-run` — shows all affected files
2. Diff per file: `npx shadcn@latest add <component> --diff <file>` — shows upstream vs local changes
3. Decide per file:
   - No local changes → safe to overwrite
   - Has local changes → read the file, analyze the diff, apply upstream updates while preserving modifications
   - User says "just update everything" → use `--overwrite`, but confirm first
4. **Never use `--overwrite` without the user's explicit approval.**

---

## Outputs & Triggers

### Output
Components implemented — design code written, Tailwind config updated, CSS variables applied. Visual style follows the design spec; component structure follows shadcn conventions.

### Exit Declaration
State clearly: "**Implementation complete. Say 'review' to trigger review-implementation, or redsign the app UI/UX.**"

### Next Step
User invokes `review-implementation`.
