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

# Canonical market type aliases (Phase 4: dedupe / conflict normalization)
# Keys are lowercase; values are the canonical display label.
MARKET_ALIASES: dict[str, str] = {
    "money line": "1X2",
    "moneyline": "1X2",
    "ml": "1X2",
    "home/away": "1X2",
    "match result": "1X2",
    "both teams to score": "BTTS",
    "both teams score": "BTTS",
    "btts": "BTTS",
    "gg": "BTTS",
    "asian handicap": "Handicap",
    "ah": "Handicap",
}


def normalize_market_type(raw: str) -> str:
    """
    Map a raw market-type string to its canonical label.
    Unknown values pass through unchanged (original casing preserved).
    """
    return MARKET_ALIASES.get(raw.lower().strip(), raw.strip())

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
    prebuilt_parlays: list[dict] = field(default_factory=list)
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


def _parse_xlsx_confidence(raw: str) -> str:
    """
    Map richer worksheet confidence labels to parser confidence levels.
    Unknown labels safely fall back to default confidence.
    """
    cleaned = raw.strip().lower()
    alias_map = {
        "very high": "high",
        "high value": "high",
        "super safe": "high",
        "safe": "medium",
        "med": "medium",
    }
    return _parse_confidence(alias_map.get(cleaned, cleaned))


def _coerce_xlsx_odds(raw_value) -> str:
    """
    Normalize worksheet odds values to parser-friendly strings.

    Excel often drops the '+' sign from American odds (e.g., +120 -> 120).
    For large integer-like values, treat them as positive American odds.
    """
    if raw_value is None:
        return ""

    text = str(raw_value).strip()
    if not text or text.lower() == "nan":
        return ""

    # Keep explicit formats unchanged (+/- american, fractional, decimal text).
    if text.startswith(("+", "-")) or "/" in text:
        return text

    # If numeric and very large, interpret as American odds stripped by Excel.
    try:
        numeric = float(text)
        if numeric.is_integer() and abs(numeric) >= 100:
            return f"+{int(numeric)}" if numeric > 0 else str(int(numeric))
    except ValueError:
        pass

    return text


def _detect_sport(match_name: str) -> str:
    """
    Future-proof sport detection hook.
    Currently always returns 'football'.
    Extend with cricket/basketball keywords when needed.
    """
    return "football"


def _infer_market_from_selection(selection: str) -> str:
    """
    Infer a canonical market type from the selection text.

    Returns a value compatible with MARKET_ALIASES / analyser._market_to_prior_key.
    Falls back to 'freeform' when the selection text is ambiguous.
    """
    sel = selection.lower().strip()
    if any(kw in sel for kw in ("both teams to score", "btts", "gg")):
        return "BTTS"
    if any(kw in sel for kw in ("over", "under", "total")):
        return "O/U"
    if any(kw in sel for kw in ("asian handicap", "handicap", " ah")):
        return "Handicap"
    if any(kw in sel for kw in ("money line", "moneyline", " ml", "double chance")):
        return "1X2"
    # Default: if it doesn't match a special market, treat as moneyline pick
    return "1X2"


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
            market_type=_infer_market_from_selection(selection),
            selection=selection,
            decimal_odds=decimal_odds,
            confidence=DEFAULT_CONFIDENCE,
            sport=_detect_sport(match_name),
            raw_odds_str=raw_odds,
            line_number=line_number,
        ))

    return parsed_bets


def _parse_bets_xlsx(filepath: Path) -> ParseResult:
    """
    Parse worksheet-style bets from .xlsx/.xls files.

    Expected columns (case-insensitive):
      Match, Market, Selection, Odds, Confidence

    Required columns: Match, Selection, Odds
    """
    result = ParseResult()

    try:
        import pandas as pd
    except ImportError as e:
        msg = (
            "XLSX parsing requires openpyxl. Install it with "
            "'pip install openpyxl'."
        )
        logger.error("%s (%s)", msg, e)
        result.errors.append({"line": 0, "message": msg})
        _write_error_log(result.errors)
        return result

    try:
        sheets = pd.read_excel(filepath, sheet_name=None)
    except Exception as e:
        msg = f"Failed to read spreadsheet '{filepath}': {e}"
        logger.error(msg)
        result.errors.append({"line": 0, "message": msg})
        _write_error_log(result.errors)
        return result

    bet_like_sheet_count = 0
    parlay_sheet_count = 0
    for sheet_name, df in sheets.items():
        column_map = {str(c).strip().lower(): c for c in df.columns}
        parlay_columns = ("parlay name", "legs included")

        # Parse prebuilt parlay sheets when present.
        if all(c in column_map for c in parlay_columns):
            parlay_sheet_count += 1
            name_col = column_map["parlay name"]
            legs_included_col = column_map["legs included"]
            legs_col = column_map.get("legs")
            multiplier_col = column_map.get("multiplier")

            for idx, row in df.iterrows():
                excel_row = int(idx) + 2
                parlay_name = _clean_string("" if row.get(name_col) is None else str(row.get(name_col)))
                legs_included = _clean_string("" if row.get(legs_included_col) is None else str(row.get(legs_included_col)))

                if not parlay_name and not legs_included:
                    continue

                legs_raw = "" if not legs_col or row.get(legs_col) is None else str(row.get(legs_col)).strip()
                multiplier_raw = "" if not multiplier_col or row.get(multiplier_col) is None else str(row.get(multiplier_col)).strip()

                legs_count = None
                if legs_raw and legs_raw.lower() != "nan":
                    try:
                        legs_count = int(float(legs_raw))
                    except ValueError:
                        legs_count = None

                multiplier_value = None
                if multiplier_raw and multiplier_raw.lower() != "nan":
                    cleaned = multiplier_raw.lower().replace("x", "").replace(",", "").strip()
                    try:
                        multiplier_value = float(cleaned)
                    except ValueError:
                        multiplier_value = None

                result.prebuilt_parlays.append({
                    "parlay_name": parlay_name,
                    "legs": legs_count,
                    "multiplier": multiplier_value,
                    "multiplier_raw": multiplier_raw,
                    "legs_included": legs_included,
                    "sheet_name": sheet_name,
                    "line": excel_row,
                })

            continue

        required = ("match", "selection", "odds")
        if any(c not in column_map for c in required):
            logger.info("Skipping non-bet sheet '%s' (missing match/selection/odds columns).", sheet_name)
            continue

        bet_like_sheet_count += 1
        match_col = column_map["match"]
        selection_col = column_map["selection"]
        odds_col = column_map["odds"]
        market_col = column_map.get("market")
        confidence_col = column_map.get("confidence")

        for idx, row in df.iterrows():
            excel_row = int(idx) + 2  # Header is row 1.

            match_val = row.get(match_col)
            selection_val = row.get(selection_col)
            odds_val = row.get(odds_col)
            market_val = row.get(market_col) if market_col else None
            confidence_val = row.get(confidence_col) if confidence_col else None

            # Ignore fully empty worksheet rows.
            if (
                (match_val is None or str(match_val).strip() == "" or str(match_val).lower() == "nan")
                and (selection_val is None or str(selection_val).strip() == "" or str(selection_val).lower() == "nan")
                and (odds_val is None or str(odds_val).strip() == "" or str(odds_val).lower() == "nan")
            ):
                continue

            match_name = _clean_string("" if match_val is None else str(match_val))
            selection = _clean_string("" if selection_val is None else str(selection_val))
            raw_odds = _coerce_xlsx_odds(odds_val)
            market_type = normalize_market_type(
                _clean_string("" if market_val is None else str(market_val))
            ) if market_col else "freeform"
            confidence = _parse_xlsx_confidence(
                "" if confidence_val is None else str(confidence_val)
            )

            location = f"Sheet '{sheet_name}', line {excel_row}"
            if not match_name:
                result.errors.append({"line": excel_row, "message": f"{location}: Match name is empty."})
                continue
            if not selection:
                result.errors.append({"line": excel_row, "message": f"{location}: Selection is empty."})
                continue
            if not raw_odds:
                result.errors.append({"line": excel_row, "message": f"{location}: Odds are empty."})
                continue

            try:
                decimal_odds = to_decimal_odds(raw_odds)
            except (ValueError, ZeroDivisionError) as e:
                result.errors.append({
                    "line": excel_row,
                    "message": f"{location}: Odds conversion failed for '{raw_odds}': {e}",
                })
                continue

            if decimal_odds <= 1.0:
                result.errors.append({
                    "line": excel_row,
                    "message": f"{location}: Odds {decimal_odds} must be > 1.0 (got '{raw_odds}').",
                })
                continue

            result.bets.append(BetInput(
                match_name=match_name,
                market_type=market_type or "freeform",
                selection=selection,
                decimal_odds=decimal_odds,
                confidence=confidence,
                sport=_detect_sport(match_name),
                raw_odds_str=raw_odds,
                line_number=excel_row,
            ))

    if bet_like_sheet_count == 0 and parlay_sheet_count == 0:
        msg = "No bet-like sheet found. Required columns: match, selection, odds"
        logger.error(msg)
        result.errors.append({"line": 0, "message": msg})
        _write_error_log(result.errors)
        return result

    _write_error_log(result.errors)
    logger.info(
        "Parsed %d valid bets, %d prebuilt parlays, %d errors from spreadsheet(s).",
        len(result.bets),
        len(result.prebuilt_parlays),
        len(result.errors),
    )
    return result


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

    if filepath.suffix.lower() in {".xlsx", ".xls"}:
        return _parse_bets_xlsx(filepath)

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
