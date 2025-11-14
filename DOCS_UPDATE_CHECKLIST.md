# Documentation Update Checklist

**Use this checklist BEFORE committing code changes to ensure PORTFOLIO_CONTEXT.md stays in sync.**

## When to Use
- After modifying any component in `/app` or `/components`
- After adding new pages or features
- After updating design system (`lib/designSystem.ts`)
- After changing typography, colors, or naming conventions

## Pre-Commit Checklist

### 1. Files Modified Checklist
- [ ] Did you modify any files in `app/` directory?
- [ ] Did you modify any files in `components/` directory?
- [ ] Did you modify any files in `lib/` directory?
- [ ] Did you create new files?

**If YES to any above:** Continue with sections below

### 2. Component/Page Changes
If you modified or created a component/page:

- [ ] **Component name updated in PORTFOLIO_CONTEXT.md** → Section "File Structure"
- [ ] **File path is correct** in the documentation
- [ ] **Component purpose documented** (what it does, why it exists)
- [ ] **Key props/interfaces listed** if applicable
- [ ] **Design patterns used documented** (e.g., CustomTooltip, metric cards)
- [ ] **Any special naming conventions noted** (e.g., precinct names: full vs short)

#### Example Entry to Add:
```
**components/zameen/YourNewComponent.tsx**
- Purpose: [What it does]
- Key Exports: [What components/functions it exports]
- Design Pattern: [Pattern it follows]
- Data Structure: [If it accepts special data]
```

### 3. Design System Changes
If you modified `lib/designSystem.ts`:

- [ ] **Color changes documented** → Section "Design System → Colors"
- [ ] **Typography changes documented** → Section "Design System → Typography"
- [ ] **Chart config changes documented** → Section "Design System → Chart Configuration"
- [ ] **New tokens/exports listed** with their purpose
- [ ] **Examples updated** in design system section

### 4. Naming Convention Changes
If you introduced new naming rules or updated existing ones:

- [ ] **Pattern documented** in "Design System → Naming Conventions"
- [ ] **All examples updated** throughout the document
- [ ] **Why this pattern was chosen** is explained
- [ ] **Where it applies** is clearly stated (e.g., "visible text", "internal mappings")

### 5. Typography/Color Updates
If you modified classes, colors, or sizes:

- [ ] **New standard documented** (e.g., "all body text uses base Tailwind size + text-slate-300")
- [ ] **Files affected listed** (e.g., "app/page.tsx, app/manutd/page.tsx, app/zameen/page.tsx")
- [ ] **Reason for change noted** (e.g., "consistency across portfolio")
- [ ] **Before/after examples provided** if helpful

### 6. Zameen-Specific Changes
If you modified Zameen page content:

- [ ] **Narrative copy updated** → Section "Zameen Project → Narrative Content"
- [ ] **Chart components updated** → Section "Zameen Project → Chart Components"
- [ ] **Data structure changes documented** if applicable
- [ ] **All precinct references checked** (full names vs short form)

### 7. Final Verification

Before committing:

- [ ] **Read your changes** in PORTFOLIO_CONTEXT.md
- [ ] **Verify accuracy** - does it match the code?
- [ ] **Check consistency** - do all examples use same patterns?
- [ ] **Test readability** - could ChatGPT understand this?
- [ ] **Cross-references** - are linked sections still accurate?

## Quick Update Commands

### View current docs status
```bash
cat PORTFOLIO_CONTEXT.md | head -50
```

### Find all files modified in last commit
```bash
git diff --name-only HEAD~1
```

### Search for specific component in docs
```bash
grep -n "ComponentName" PORTFOLIO_CONTEXT.md
```

### Format check (look for incomplete sections)
```bash
grep -n "TODO\|FIXME\|UPDATE ME" PORTFOLIO_CONTEXT.md
```

## Documentation Sections

Quick reference of PORTFOLIO_CONTEXT.md sections to update:

| Section | When to Update | What to Update |
|---------|---|---|
| **Project Overview** | Architecture changes | Tech stack, primary dependencies |
| **Design System** | Visual/style changes | Colors, typography, tokens |
| **File Structure** | New files created | Paths and purposes |
| **Chart Components** | Chart modifications | Component logic, data structures |
| **Zameen Narrative** | Copy changes | Exact narrative text |
| **Common Tasks** | New patterns emerge | Code patterns and how-tos |
| **Version History** | After each commit | What changed and why |

## Example: Updating PORTFOLIO_CONTEXT.md

### Bad: Vague update
```
Updated some stuff in ConstructionCostChartFromData
```

### Good: Specific update
```
**components/zameen/ConstructionCostChartFromData.tsx**
- Added CustomTooltip component to display: Precinct name + value with "PKR/sq yd" unit
- Changed X-axis from shortLabel to displayLabel (P5 → Precinct 5)
- Tooltip styling: bg-slate-900, border-slate-700, text-slate-200, font-size text-xs
- Removed text-sm from narrative paragraph for consistency
```

## Rules to Remember

1. **Full names visible, short forms hidden** - "Precinct 5" in UI, "P5" in internal data
2. **Consistent font sizes** - Base Tailwind size for body text, not text-sm
3. **Centralized colors** - Use tokens from lib/designSystem.ts
4. **Type safety** - Document TypeScript interfaces if they're used in components
5. **Design consistency** - All charts should use same tooltip/styling patterns

## Common Mistakes to Avoid

❌ **Mistake:** "Updated ChartComponent.tsx"
✅ **Fix:** "Modified SizeVsPriceSummary X-axis from 'P5' to 'Precinct 5' for naming consistency"

❌ **Mistake:** Forgetting to update example code in docs
✅ **Fix:** When changing code, update all code examples in PORTFOLIO_CONTEXT.md

❌ **Mistake:** Not documenting WHY a change was made
✅ **Fix:** Include reasoning (e.g., "for consistency", "to improve readability", "to match design system")

❌ **Mistake:** Leaving version history blank
✅ **Fix:** Add entry: "v1.2.0 - Fixed precinct naming across all charts (2025-11-13)"

## Need Help?

If you're unsure what to document:
1. **Ask:** "Would ChatGPT need to know this to understand my codebase?"
2. **If YES:** Document it in PORTFOLIO_CONTEXT.md
3. **If NO:** You might not need it in the context file

---

**Last Updated:** 2025-11-13
**Maintenance:** Review this checklist quarterly or when significant changes occur
