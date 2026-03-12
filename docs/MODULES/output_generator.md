# Output Generator Module

## Purpose

The Output Generator module creates final deliverables from BetLab's analysis: human-readable Markdown reports summarizing betting recommendations, and CSV templates for manual entry into sportsbooks. This module transforms analysis outputs into actionable, documented bet placement instructions.

## Key Responsibilities

- Generate comprehensive Markdown reports with recommendations and analysis
- Export structured CSV templates for bet tracking and sportsbook entry
- Generate unique bet IDs for tracking and audit trails
- Format financial data consistently across outputs
- Provide summary statistics and performance narratives

## Dependencies

```python
from typing import List, Dict, Any
from datetime import datetime
import csv
from pathlib import Path
```

## Function Reference

### `generate_report(singles: List[Dict], parlays: List[Dict], summary: Dict) -> str`

**Purpose:** Create comprehensive Markdown report documenting all recommended bets, analysis, and decision rationale. Intended for human review before placing bets.

**Parameters:**
- `singles` (list[dict]): Recommended single bets with all analysis fields
- `parlays` (list[dict]): Recommended parlay combinations with EV analysis
- `summary` (dict): Session-level statistics (bankroll, daily limit, streak info, etc.)

**Returns:**
- `str`: Formatted Markdown report as string

**Raises:**
- `ValueError`: If required fields missing from input dicts

**Example:**
```python
from betlab.output_generator import generate_report

singles = [
    {
        "id": "BET_20250313_001",
        "event": "Patriots vs Chiefs",
        "odds": 2.50,
        "probability": 0.50,
        "ev": 0.25,
        "stake": 150.00,
        "sport": "NFL"
    },
]

parlays = [
    {
        "id": "PARLAY_20250313_001",
        "legs": 2,
        "leg_ids": ["BET_20250313_001", "BET_20250313_002"],
        "odds": 3.82,
        "probability": 0.35,
        "ev": 0.35,
        "stake": 75.00
    },
]

summary = {
    "date": "2025-03-13",
    "bankroll": 10000.0,
    "daily_limit": 1000.0,
    "daily_staked": 225.0,
    "unit_size": 100.0,
    "streak": "none",
    "total_bets": 3,
}

report = generate_report(singles, parlays, summary)
print(report)  # Large formatted Markdown document

# Can write to file
with open("bets_20250313.md", "w") as f:
    f.write(report)
```

**Report Structure:**
- Header with date and session summary
- Bankroll status section
- Singles section with individual EV analysis
- Parlays section with combination details
- Summary statistics and daily limits
- Appendix with formulas and assumptions

**Notes:**
- Report serves as betting slip and analysis documentation
- Recommended: Review entire report before placing any bets
- Include reasoning for each bet (why selected, EV justification)
- Easy to archive for later performance analysis
- Professional formatting suitable for sportsbook review

---

### `export_csv_template(singles: List[Dict], parlays: List[Dict], output_path: str) -> None`

**Purpose:** Export structured CSV template for manual entry into sportsbook interfaces or bet tracking systems. Provides clean tabular format for ease of entry.

**Parameters:**
- `singles` (list[dict]): Single bet recommendations
- `parlays` (list[dict]): Parlay recommendations
- `output_path` (str): File path for CSV output

**Returns:**
- `None` (writes to file)

**Raises:**
- `IOError`: If unable to write to specified path
- `ValueError`: If data malformed

**Example:**
```python
from betlab.output_generator import export_csv_template

singles = [
    {
        "id": "BET_20250313_001",
        "event": "Patriots vs Chiefs",
        "odds": 2.50,
        "stake": 150.00,
        "sport": "NFL"
    },
    {
        "id": "BET_20250313_002",
        "event": "Lakers vs Celtics",
        "odds": 1.91,
        "stake": 75.00,
        "sport": "NBA"
    },
]

parlays = [
    {
        "id": "PARLAY_20250313_001",
        "legs": 2,
        "leg_ids": ["BET_20250313_001", "BET_20250313_002"],
        "odds": 3.82,
        "stake": 75.00,
    },
]

# Export to CSV
export_csv_template(singles, parlays, output_path="bets_20250313.csv")

# CSV content (readable format):
# bet_id,type,event,odds,stake,sport,status
# BET_20250313_001,single,Patriots vs Chiefs,2.50,150.00,NFL,pending
# BET_20250313_002,single,Lakers vs Celtics,1.91,75.00,NBA,pending
# PARLAY_20250313_001,parlay,BET_20250313_001+BET_20250313_002,3.82,75.00,mixed,pending
```

**CSV Columns:**
- bet_id: Unique identifier for tracking
- type: "single" or "parlay"
- event/legs: Event description or component bet IDs
- odds: Decimal odds
- stake: Recommended stake amount
- sport: Sport type
- status: Tracking field (pending → placed → won/lost)

**Notes:**
- Template designed for manual sportsbook entry
- Status field allows tracking bet placement
- Can be imported into spreadsheets for tracking
- Include datetime for reference
- CSV suitable for backup and audit trails

---

### `generate_bet_id(date: str, index: int) -> str`

**Purpose:** Create unique, human-readable bet identifiers combining date and sequence number. Ensures all bets have consistent, traceable IDs.

**Parameters:**
- `date` (str): Date in format YYYYMMDD (e.g., "20250313")
- `index` (int): Sequence number (1-based)

**Returns:**
- `str`: Formatted bet ID (e.g., "BET_20250313_001")

**Raises:**
- `ValueError`: If date format invalid or index < 1

**Example:**
```python
from betlab.output_generator import generate_bet_id
from datetime import datetime

# Generate IDs for today's bets
today = datetime.now().strftime("%Y%m%d")

bet_id_1 = generate_bet_id(today, 1)
print(bet_id_1)  # Output: BET_20250313_001

bet_id_2 = generate_bet_id(today, 2)
print(bet_id_2)  # Output: BET_20250313_002

# Parlay ID (different prefix)
parlay_id = f"PARLAY_{today}_001"
print(parlay_id)  # Output: PARLAY_20250313_001
```

**Notes:**
- Format: BET_YYYYMMDD_XXX for singles
- Format: PARLAY_YYYYMMDD_XXX for parlays
- IDs sortable chronologically
- Index resets each day
- Used in reports, CSVs, and historical records

---

## Code Example: End-to-End Usage

```python
from betlab.output_generator import (
    generate_report,
    export_csv_template,
    generate_bet_id
)
from datetime import datetime

# Scenario: Generate final output after completing all analysis

# Prepare data
today = datetime.now().strftime("%Y%m%d")

singles = [
    {
        "id": generate_bet_id(today, 1),
        "event": "Patriots vs Chiefs",
        "odds": 2.50,
        "probability": 0.50,
        "ev": 0.25,
        "stake": 150.00,
        "sport": "NFL",
        "confidence": "high"
    },
    {
        "id": generate_bet_id(today, 2),
        "event": "Lakers vs Celtics",
        "odds": 1.91,
        "probability": 0.58,
        "ev": 0.11,
        "stake": 75.00,
        "sport": "NBA",
        "confidence": "medium"
    },
]

parlays = [
    {
        "id": f"PARLAY_{today}_001",
        "legs": 2,
        "leg_ids": [singles[0]['id'], singles[1]['id']],
        "leg_events": [singles[0]['event'], singles[1]['event']],
        "odds": 3.82,
        "probability": 0.35,
        "ev": 0.35,
        "stake": 75.00,
    },
]

summary = {
    "date": today,
    "bankroll": 10000.0,
    "daily_limit": 1000.0,
    "daily_staked": 225.0,
    "unit_size": 100.0,
    "streak": "none",
    "total_singles": len(singles),
    "total_parlays": len(parlays),
    "total_recommended_stake": sum(b['stake'] for b in singles) + sum(p['stake'] for p in parlays),
}

# Generate report
print("=== Generating Markdown Report ===")
report = generate_report(singles, parlays, summary)
report_filename = f"bets_{today}.md"
with open(report_filename, "w") as f:
    f.write(report)
print(f"Report saved to {report_filename}")

# Export CSV
print("\n=== Exporting CSV Template ===")
csv_filename = f"bets_{today}.csv"
export_csv_template(singles, parlays, output_path=csv_filename)
print(f"CSV template saved to {csv_filename}")

# Display summary
print(f"\n=== Session Summary ===")
print(f"Date: {summary['date']}")
print(f"Singles: {summary['total_singles']}")
print(f"Parlays: {summary['total_parlays']}")
print(f"Total stake: ${summary['total_recommended_stake']:.2f}")
print(f"Daily limit: ${summary['daily_limit']:.2f}")
print(f"Remaining: ${summary['daily_limit'] - summary['daily_staked']:.2f}")
```

## Configuration

Key parameters for output generation:

```python
# ID formats
BET_ID_PREFIX = "BET"
PARLAY_ID_PREFIX = "PARLAY"
ID_DATE_FORMAT = "%Y%m%d"  # YYYYMMDD
ID_INDEX_FORMAT = "{:03d}"  # Zero-padded 3 digits

# CSV columns for singles
SINGLES_CSV_COLUMNS = [
    'bet_id', 'type', 'event', 'odds', 'stake',
    'sport', 'confidence', 'status'
]

# CSV columns for parlays
PARLAYS_CSV_COLUMNS = [
    'bet_id', 'type', 'legs', 'component_bets',
    'odds', 'stake', 'status'
]

# Report formatting
REPORT_TITLE_FORMAT = "BetLab Betting Report - {date}"
REPORT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CURRENCY_SYMBOL = "$"
```

## Testing

The output generator module includes comprehensive tests in `tests/test_output_generator.py`:

- **test_generate_report**: Report structure, formatting, content accuracy
- **test_export_csv_template**: CSV format, column headers, data integrity
- **test_generate_bet_id**: ID format, date parsing, indexing
- **test_edge_cases**: Empty lists, special characters in events
- **test_file_operations**: Write permissions, file creation

Run tests with:
```bash
pytest tests/test_output_generator.py -v
```

## Integration Notes

- Input: Final recommendations from parlay_builder and bankroll_mgr
- Stake amounts from bankroll_mgr (calculate_stake)
- EV and probability analysis from math_engine and parlay_builder
- Output: Markdown reports for human review, CSV for sportsbook entry
- Recommended workflow: Generate report → human review → export CSV → place bets
- Archive reports for post-analysis performance tracking
- CSV provides historical record for auditing and strategy refinement

## Output Examples

### Report Sample Header
```markdown
# BetLab Betting Report - 2025-03-13

## Session Summary
- **Date:** 2025-03-13
- **Bankroll:** $10,000.00
- **Daily Limit:** $1,000.00
- **Daily Staked:** $225.00
- **Remaining:** $775.00
- **Unit Size:** $100.00

## Singles Recommendations (2 bets)
...
```

### CSV Sample
```
bet_id,type,event,odds,stake,sport,confidence,status
BET_20250313_001,single,Patriots vs Chiefs,2.50,150.00,NFL,high,pending
BET_20250313_002,single,Lakers vs Celtics,1.91,75.00,NBA,medium,pending
PARLAY_20250313_001,parlay,BET_20250313_001+BET_20250313_002,3.82,75.00,mixed,pending
```
