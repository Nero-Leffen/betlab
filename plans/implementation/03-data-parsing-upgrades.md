# Data and Parsing Upgrades: Step-by-Step Implementation

## Scope

This playbook covers:
1. Canonical parser pipeline.
2. Entity resolution to stable IDs.
3. Input quality scoring and review bucket.

## Step 1: Build Canonical Parser Pipeline

### Files
- [src/parser.py](../../src/parser.py)
- [config/settings.yaml](../../config/settings.yaml)

### Steps
1. Add canonical dictionaries for market aliases and selection aliases.
2. Normalize punctuation, spacing, and case consistently.
3. Convert free-form rows into canonical structure:
- match_name
- market_type
- selection
- odds
- confidence
4. Keep raw text and parsed components for auditability.

### Acceptance
1. Equivalent market labels map to one canonical value.
2. Parser supports structured and noisy free-form lines.

## Step 2: Entity Resolution

### Files
- [src/parser.py](../../src/parser.py)
- [src/parlay_builder.py](../../src/parlay_builder.py)

### Steps
1. Create team alias map and match normalization helper.
2. Generate stable match_id and team_id keys.
3. Use IDs for dedupe and correlation logic instead of raw strings.
4. Keep original display names for output readability.

### Acceptance
1. Same teams with spelling variants resolve to same IDs.
2. Correlation checks become less fragile.

## Step 3: Input Quality Scoring

### Files
- [src/parser.py](../../src/parser.py)
- [src/analyser.py](../../src/analyser.py)
- [src/output_generator.py](../../src/output_generator.py)

### Steps
1. Add parse-confidence score from 0 to 1.
2. Penalize confidence for ambiguous parse patterns.
3. Route low-score rows into review bucket.
4. Exclude review bucket from default auto-bet flow.
5. Include review summary in recommendations report.

### Acceptance
1. Ambiguous inputs do not silently enter recommendation list.
2. Review bucket appears in output summary.

## Suggested Test Cases

1. Alias normalization for market terms and team names.
2. Duplicate free-form lines with slight wording changes.
3. Ambiguous line with multiple odds formats.
4. Corrupted row with missing selection or invalid odds.

## Completion Criteria

1. Parser output includes canonical fields and parse-confidence.
2. Entity IDs are available to downstream modules.
3. Low-confidence records are visible but safely excluded from recommendations.
