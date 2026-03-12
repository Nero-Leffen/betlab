"""
parser.py
=========
Parses bets.txt (pipe-delimited) into structured BetInput objects.

Accepted line format:
    Match Name | Market Type | Selection | Odds | [Confidence]

Supports decimal, American (+150, -110), and fractional (5/2) odds.
Invalid lines are discarded and logged to data/logs/error_log.txt.
"""

from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.math_engine import to_decimal_odds

logger = logging.getLogger(__name__)

# Valid confidence levels (case-insensitive)
VALID_CONFIDENCE = {"high", "medium", "low"}
DEFAULT_CONFIDENCE = "medium"

# Free-form bet line support, e.g.:
#   "Marseille vs Angers: Marseille Money Line @ 1.47"
#   "Napoli vs Lecce: BTTS @ 2.65 OR Over 1.5 @ 1.44"
FREEFORM_LINE_RE = re.compile(r"^(?P<match>[^:|]+?)\s*:\s*(?P<picks>.+)$", re.IGNORECASE)
PICK_SEGMENT_RE = re.compile(
    r"^(?P<selection>.+?)\s*@\s*(?P<odds>[+-]?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)\b",
    re.IGNORECASE,
)
TRAILING_TIMESTAMP_RE = re.compile(r"\s+\d{1,2}:\d{2}\s*$")


@dataclass
class BetInput:
    """Structured representation of a single parsed bet."""
    match_name: str
    market_type: str
    selection: str
    decimal_odds: float
    confidence: str                    # 'high' | 'medium' | 'low'
    sport: str = "football"            # Extendable for future sports
    raw_odds_str: str = ""             # Original odds string for logging
    line_number: int = 0


@dataclass
class ParseResult:
    """Output of the parser: valid bets + error summary."""
    bets: list[BetInput] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


def _clean_string(value: str) -> str:
    return value.strip()


def _clean_freeform_segment(value: str) -> str:
    """Remove timestamps and trailing separators from free-form text segments."""
    value = TRAILING_TIMESTAMP_RE.sub("", value.strip())
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -|,;")


def _parse_confidence(raw: str) -> str:
    """
    Normalise confidence string. Defaults to 'medium' if blank or unrecognised.
    """
    cleaned = raw.strip().lower()
    return cleaned if cleaned in VALID_CONFIDENCE else DEFAULT_CONFIDENCE


def _detect_sport(match_name: str) -> str:
    """
    Future-proof sport detection hook.
    Currently always returns 'football'.
    Extend with cricket/basketball keywords when needed.
    """
    return "football"


def parse_line(line: str, line_number: int) -> tuple[Optional[BetInput], Optional[str]]:
    """
    Parse a single pipe-delimited line.

    Returns (BetInput, None) on success or (None, error_message) on failure.
    """
    # Skip blank lines and comment lines
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None, None

    parts = stripped.split("|")

    # Must have at least 4 fields: Match | Market | Selection | Odds
    if len(parts) < 4:
        return None, f"Line {line_number}: Expected at least 4 fields, got {len(parts)}: '{stripped}'"

    match_name  = _clean_string(parts[0])
    market_type = _clean_string(parts[1])
    selection   = _clean_string(parts[2])
    raw_odds    = _clean_string(parts[3])
    confidence  = _parse_confidence(parts[4]) if len(parts) >= 5 else DEFAULT_CONFIDENCE

    # Validate match name
    if not match_name:
        return None, f"Line {line_number}: Match name is empty."

    # Validate selection
    if not selection:
        return None, f"Line {line_number}: Selection is empty."

    # Convert and validate odds
    try:
        decimal_odds = to_decimal_odds(raw_odds)
    except (ValueError, ZeroDivisionError) as e:
        return None, f"Line {line_number}: Odds conversion failed for '{raw_odds}': {e}"

    if decimal_odds <= 1.0:
        return None, f"Line {line_number}: Odds {decimal_odds} must be > 1.0 (got '{raw_odds}')."

    sport = _detect_sport(match_name)

    bet = BetInput(
        match_name=match_name,
        market_type=market_type,
        selection=selection,
        decimal_odds=decimal_odds,
        confidence=confidence,
        sport=sport,
        raw_odds_str=raw_odds,
        line_number=line_number,
    )
    return bet, None


def _parse_freeform_line(line: str, line_number: int) -> list[BetInput]:
    """
    Parse free-form lines that look like:
      Match Name: Selection @ Odds [OR Selection @ Odds ...]

    Returns zero or more BetInput entries.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return []

    match = FREEFORM_LINE_RE.match(stripped)
    if not match:
        return []

    match_name = _clean_string(match.group("match"))
    if not match_name:
        return []

    picks_text = _clean_freeform_segment(match.group("picks"))
    if "@" not in picks_text:
        return []

    parsed_bets: list[BetInput] = []
    segments = re.split(r"\s+OR\s+", picks_text, flags=re.IGNORECASE)
    for segment in segments:
        segment = _clean_freeform_segment(segment)
        if not segment:
            continue

        m = PICK_SEGMENT_RE.match(segment)
        if not m:
            continue

        selection = _clean_string(m.group("selection"))
        raw_odds = _clean_string(m.group("odds"))
        if not selection or not raw_odds:
            continue

        try:
            decimal_odds = to_decimal_odds(raw_odds)
        except (ValueError, ZeroDivisionError):
            continue

        if decimal_odds <= 1.0:
            continue

        parsed_bets.append(BetInput(
            match_name=match_name,
            market_type="freeform",
            selection=selection,
            decimal_odds=decimal_odds,
            confidence=DEFAULT_CONFIDENCE,
            sport=_detect_sport(match_name),
            raw_odds_str=raw_odds,
            line_number=line_number,
        ))

    return parsed_bets


def parse_bets_file(filepath: str | Path) -> ParseResult:
    """
    Read and parse a bets.txt file.

    Returns a ParseResult with valid BetInput objects and a list of errors.
    Errors are also written to data/logs/error_log.txt.
    """
    filepath = Path(filepath)
    result = ParseResult()

    if not filepath.exists():
        msg = f"Input file not found: {filepath}"
        logger.error(msg)
        result.errors.append({"line": 0, "message": msg})
        return result

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        logger.warning("Input file is empty: %s", filepath)
        return result

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip obvious non-data lines in free-form dumps.
        if not stripped or stripped.startswith("#"):
            continue

        # 1) Strict pipe format remains the primary contract.
        if "|" in stripped:
            bet, error = parse_line(line, i)
            if error:
                logger.warning(error)
                result.errors.append({"line": i, "message": error})
            elif bet is not None:
                result.bets.append(bet)
            continue

        # 2) Free-form extraction for text dumps.
        freeform_bets = _parse_freeform_line(line, i)
        if freeform_bets:
            result.bets.extend(freeform_bets)
            continue

        # 3) Ignore headings/noise lines instead of logging parse errors.
        #    This makes the parser robust against arbitrary text documents.
        continue

    _write_error_log(result.errors)
    logger.info("Parsed %d valid bets, %d errors.", len(result.bets), len(result.errors))
    return result


def _write_error_log(errors: list[dict]) -> None:
    """Write parse errors to data/logs/error_log.txt."""
    log_path = Path("data/logs/error_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "w", encoding="utf-8") as f:
        if not errors:
            f.write("No parse errors.\n")
            return
        f.write(f"Parse Error Log — {len(errors)} issue(s) found\n")
        f.write("=" * 50 + "\n")
        for err in errors:
            f.write(f"[Line {err['line']}] {err['message']}\n")
