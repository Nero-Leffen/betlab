# BetLab System Diagrams

This directory contains Mermaid diagrams that visualize the BetLab system architecture, data flow, dependencies, and pipeline execution. These diagrams are essential for understanding how the betting analytics engine processes bets from input to output.

## Diagram Files

### 1. `data_flow.mmd` - End-to-End Pipeline Visualization
**Purpose:** Shows the complete data flow through the BetLab system

**Visualizes:**
- Input source (bets.txt)
- 5 pipeline phases:
  1. **Parse** (parser.py) - Normalize match info and odds
  2. **EV Filter** (analyser.py) - Check expected value threshold
  3. **Kelly Sizing** (bankroll_mgr.py) - Calculate optimal stake amounts
  4. **Parlay Builder** (parlay_builder.py) - Create single and parlay combinations
  5. **Output** (output_generator.py) - Generate recommendations and logs
- Output files (recommendations.md, bet_log_template.csv)
- Error handling path (rejected bets → error_log.txt)

**Color Coding:**
- Light Blue: Input data
- Green: Valid outputs
- Orange: Errors and rejections

**When to Reference:** When explaining the overall system architecture or end-to-end bet processing flow to stakeholders.

---

### 2. `module_dependencies.mmd` - Module Dependency Graph
**Purpose:** Shows which modules depend on which other modules

**Visualizes:**
- Independent modules:
  - parser.py (primary input handler)
  - math_engine.py (pure mathematical functions)
- Dependent modules:
  - analyser.py (depends on: parser, math_engine)
  - bankroll_mgr.py (depends on: math_engine)
  - parlay_builder.py (depends on: analyser, math_engine)
  - output_generator.py (depends on all other modules)

**Color Coding:**
- Orange: Independent modules (no dependencies)
- Light Blue: Processing modules
- Green: Calculation modules
- Pink: Combination/Builder modules
- Purple: Output/Final stage modules

**When to Reference:** When discussing code organization, understanding module coupling, or planning refactoring efforts.

---

### 3. `pipeline_walkthrough.mmd` - Sequence Diagram
**Purpose:** Shows a single bet's journey through the entire system with actual data values

**Visualizes:**
- Example: User enters "Man City 1.85"
- Step-by-step processing:
  1. Parser normalizes the odds to decimal format (1.85)
  2. Math engine calculates implied probability (54.1%)
  3. Analyser computes expected value (2.4%)
  4. Decision point: EV >= 2% threshold?
     - **If Pass:** Bankroll manager sizes stake (₹2,400), parlay builder creates combinations, output generates recommendations
     - **If Fail:** Rejection logged with reason
- Shows actual calculated values at each stage

**When to Reference:** When training new developers, explaining decision logic, or demonstrating how the system handles specific bet scenarios.

---

## Viewing Options

### Option 1: GitHub (Recommended)
If this repository is on GitHub, Mermaid diagrams render automatically in the repository viewer. Simply navigate to the diagram files and they will display as visual graphics.

**Pros:** No installation needed, renders in web browser
**Cons:** Requires GitHub access

### Option 2: VSCode with Mermaid Preview Extension
Install the "Markdown Preview Mermaid Support" extension for VSCode:
1. Open VSCode Extensions (Ctrl+Shift+X)
2. Search for "Mermaid"
3. Install "Markdown Preview Mermaid Support" (by Matt Bierner)
4. Open any .mmd file
5. Press Ctrl+Shift+V to preview

**Pros:** Local rendering, no internet required
**Cons:** Requires extension installation

### Option 3: Online Mermaid Editor
Use the official Mermaid Live Editor: https://mermaid.live

1. Copy the entire content of a .mmd file
2. Paste into the editor
3. View the rendered diagram instantly

**Pros:** Full-featured editor with export options
**Cons:** Requires internet, may slow with large diagrams

### Option 4: Command Line Rendering
Install mermaid-cli for local rendering to PNG/SVG:

```bash
# Install Node.js first (if not already installed)
npm install -g @mermaid-js/mermaid-cli

# Render a diagram to PNG
mmdc -i data_flow.mmd -o data_flow.png

# Render a diagram to SVG
mmdc -i module_dependencies.mmd -o module_dependencies.svg
```

**Pros:** Batch processing, version control compatible
**Cons:** Requires Node.js installation

---

## Diagram Quick Reference

| Diagram | Type | Best For | Key Insight |
|---------|------|----------|------------|
| data_flow.mmd | Flowchart | Portfolio/stakeholders | "5 phases → 2 outputs + error handling" |
| module_dependencies.mmd | Graph | Code architects | "2 independent cores, 4 dependent modules" |
| pipeline_walkthrough.mmd | Sequence | Technical training | "Shows values at each calculation step" |

---

## Integration with Documentation

These diagrams complement the following documentation files:

- **ARCHITECTURE.md** - Detailed written descriptions of system design (diagrams provide visual reference)
- **DESIGN_DECISIONS.md** - Rationale behind architectural choices (diagrams show implementation)
- **MODULE Guides** - Specific module documentation (diagrams show cross-module relationships)

---

## Updating Diagrams

When the system changes:

1. Update the relevant .mmd file with new logic
2. Test syntax using Mermaid Live Editor: https://mermaid.live
3. Commit changes with message describing what changed
4. The diagrams will auto-update in GitHub, VSCode, and online viewers

---

## File Format

All diagrams use Mermaid syntax (.mmd extension). Mermaid is:
- **Markdown-based** - Human readable source code
- **Plain text** - Version control friendly
- **Syntax simple** - No special tools needed to edit
- **Widely supported** - GitHub, GitLab, VSCode, multiple documentation platforms

---

## Troubleshooting

### "Diagram won't render in GitHub"
- GitHub supports Mermaid natively, but may cache old versions
- Clear browser cache (Ctrl+Shift+Delete) and refresh

### "Diagram looks wrong in VSCode"
- Ensure "Markdown Preview Mermaid Support" extension is installed
- Reload VSCode (Ctrl+Shift+P → "Reload Window")
- Check for syntax errors using Mermaid Live Editor

### "Can't run mermaid-cli"
- Ensure Node.js is installed: `node --version`
- Reinstall mmdc: `npm install -g @mermaid-js/mermaid-cli`
- On Windows, may need to restart terminal after installation

---

## Related Files

- `../ARCHITECTURE.md` - System architecture documentation
- `../DESIGN_DECISIONS.md` - Design rationale
- `../MODULES/` - Module-specific documentation
