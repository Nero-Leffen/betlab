# Parser Module

## Purpose

The Parser module handles conversion and validation of betting odds across multiple international formats (decimal, American, and fractional). It provides a unified interface for normalizing odds data from various betting sources into a standard internal format.

## Key Responsibilities

- Parse decimal odds (European format: 1.50, 2.00, etc.)
- Parse American odds (moneyline format: +150, -200, etc.)
- Parse fractional odds (British format: 1/2, 5/4, etc.)
- Normalize mixed input formats into decimal odds
- Validate odds for correctness and reasonable ranges

## Dependencies

```python
import re
from typing import Union
```

## Function Reference

### `parse_decimal(odds_str: str) -> float`

**Purpose:** Convert decimal-format odds string to float, validating format and range.

**Parameters:**
- `odds_str` (str): Decimal odds as string (e.g., "1.50", "2.75")

**Returns:**
- `float`: Parsed decimal odds value

**Raises:**
- `ValueError`: If format is invalid or odds < 1.0

**Example:**
```python
from betlab.parser import parse_decimal

odds = parse_decimal("2.50")
print(odds)  # Output: 2.5

odds = parse_decimal("1.1")
print(odds)  # Output: 1.1
```

**Notes:**
- Decimal odds must be >= 1.0 (represents minimum return on stake)
- Handles whitespace trimming automatically
- Standard European/international odds format

---

### `parse_american(odds_str: str) -> float`

**Purpose:** Convert American (moneyline) odds to decimal format.

**Parameters:**
- `odds_str` (str): American odds as string (e.g., "+150", "-200")

**Returns:**
- `float`: Equivalent decimal odds

**Raises:**
- `ValueError`: If format is invalid or value is -100

**Example:**
```python
from betlab.parser import parse_american

# Positive odds: +150 means $150 profit on $100 stake
decimal = parse_american("+150")
print(decimal)  # Output: 2.5

# Negative odds: -200 means $100 profit on $200 stake
decimal = parse_american("-200")
print(decimal)  # Output: 1.5
```

**Notes:**
- Positive odds: `(odds + 100) / 100`
- Negative odds: `100 / abs(odds)`
- -100 is invalid (would create division issues)
- Common in US sportsbooks (NFL, NBA, MLB)

---

### `parse_fractional(odds_str: str) -> float`

**Purpose:** Convert fractional odds (British format) to decimal.

**Parameters:**
- `odds_str` (str): Fractional odds as string (e.g., "1/2", "5/4")

**Returns:**
- `float`: Equivalent decimal odds

**Raises:**
- `ValueError`: If format invalid or denominator is zero

**Example:**
```python
from betlab.parser import parse_fractional

# 1/2 means £1 profit on £2 stake, total return £3
decimal = parse_fractional("1/2")
print(decimal)  # Output: 1.5

# 5/4 means £5 profit on £4 stake, total return £9
decimal = parse_fractional("5/4")
print(decimal)  # Output: 2.25
```

**Notes:**
- Formula: `(numerator / denominator) + 1`
- Common in UK, Australia, Ireland betting
- Handles spaces around "/" automatically
- Both integers and decimal components supported

---

### `normalize_odds(odds_input: Union[str, float]) -> float`

**Purpose:** Auto-detect odds format and convert to decimal. Handles mixed input types intelligently.

**Parameters:**
- `odds_input` (str | float): Odds in any format or as float

**Returns:**
- `float`: Normalized decimal odds

**Raises:**
- `ValueError`: If format unrecognizable

**Example:**
```python
from betlab.parser import normalize_odds

# Already decimal
result = normalize_odds(2.50)
print(result)  # Output: 2.5

# American format (auto-detected)
result = normalize_odds("-200")
print(result)  # Output: 1.5

# Fractional format (auto-detected)
result = normalize_odds("5/4")
print(result)  # Output: 2.25

# Decimal string
result = normalize_odds("1.80")
print(result)  # Output: 1.8
```

**Notes:**
- Detection logic: 1) Check if float, 2) Check for "+/-" (American), 3) Check for "/" (fractional), 4) Assume decimal
- Most flexible function for importing odds from various sources
- Recommended entry point for user input

---

### `validate_odds(odds: float) -> bool`

**Purpose:** Verify odds value is within valid ranges and mathematically sound.

**Parameters:**
- `odds` (float): Decimal odds to validate

**Returns:**
- `bool`: True if valid, False otherwise

**Raises:**
- `ValueError`: With detailed message if validation fails

**Example:**
```python
from betlab.parser import validate_odds

# Valid odds
try:
    validate_odds(2.50)
    print("Valid")  # Output: Valid
except ValueError as e:
    print(f"Invalid: {e}")

# Invalid: too low
try:
    validate_odds(0.99)
except ValueError as e:
    print(f"Invalid: {e}")  # Output: Invalid: Odds must be >= 1.0

# Invalid: impossibly high (would indicate rigged market)
try:
    validate_odds(1000.0)
except ValueError as e:
    print(f"Invalid: {e}")  # Output: Invalid: Odds exceed reasonable market limits
```

**Notes:**
- Minimum: 1.0 (guaranteed loss of stake)
- Maximum: 1000.0 (sanity check for data corruption)
- Should be used before storing odds in database
- Raises descriptive errors for debugging

---

## Code Example: End-to-End Usage

```python
from betlab.parser import normalize_odds, validate_odds, parse_american

# Scenario: User inputs odds from different sportsbooks
odds_sources = [
    ("2.50", "decimal"),
    ("-200", "american"),
    ("5/4", "fractional"),
]

normalized_odds = []

for odds_input, source_type in odds_sources:
    try:
        # Normalize to decimal
        decimal_odds = normalize_odds(odds_input)

        # Validate
        validate_odds(decimal_odds)

        normalized_odds.append({
            "original": odds_input,
            "source": source_type,
            "decimal": decimal_odds,
            "implied_probability": 1 / decimal_odds
        })

    except ValueError as e:
        print(f"Error processing {odds_input}: {e}")

for item in normalized_odds:
    print(f"{item['original']} ({item['source']}) → {item['decimal']} decimal")
```

## Configuration

The parser module operates with minimal configuration. Key constants:

```python
# Validation ranges
MIN_ODDS = 1.0  # No negative returns
MAX_ODDS = 1000.0  # Sanity check for data errors

# Format detection thresholds
DECIMAL_PRECISION = 2  # Expected decimal places for decimal odds
```

## Testing

The parser module includes comprehensive tests in `tests/test_parser.py`:

- **test_parse_decimal**: Various decimal format inputs
- **test_parse_american**: Positive/negative American odds
- **test_parse_fractional**: Various fractional combinations
- **test_normalize_odds**: Format auto-detection
- **test_validate_odds**: Boundary conditions and error cases
- **test_edge_cases**: Whitespace, precision, rounding behavior

Run tests with:
```bash
pytest tests/test_parser.py -v
```
