"""Presentation of scientific validation notices.

Pure helpers that turn the plain notice records produced by
``seebeck_prime.application.use_cases.validate_calculated_properties`` into
the strings the user sees.

The module deliberately imports neither Qt nor the domain layer:

* no Qt keeps it usable (and testable) in a headless environment;
* no domain import keeps the layer boundary that
  ``tests/test_architecture_dependencies.py::test_presentation_does_not_import_domain_or_infrastructure``
  enforces. The notices arrive as plain dictionaries.
"""

from __future__ import annotations

#: Severities in the order they should be reported to the user.
SEVERITY_ORDER = ("error", "warning", "info")

#: Human-readable labels for the severities.
SEVERITY_LABELS = {
    "error": "Error",
    "warning": "Warning",
    "info": "Information",
}


def split_by_severity(notices):
    """Split notices into ``(errors, warnings, infos)``.

    Args:
        notices: Iterable of ``{"severity", "field", "message"}`` records.

    Returns:
        A 3-tuple of lists, in the order errors, warnings, infos.
    """
    buckets = {"error": [], "warning": [], "info": []}
    for notice in notices or ():
        severity = str(notice.get("severity", "info")).lower()
        buckets.setdefault(severity, []).append(notice)
    return (
        buckets.get("error", []),
        buckets.get("warning", []),
        buckets.get("info", []),
    )


def has_blocking_notices(notices) -> bool:
    """True when at least one ERROR-level notice is present.

    An error means the data cannot be interpreted as a physical measurement
    (for example a non-positive temperature), so the caller must stop and
    tell the user rather than continue silently.
    """
    errors, _, _ = split_by_severity(notices)
    return bool(errors)


def summarise(notices) -> str:
    """A one-line summary suitable for a status bar.

    Returns an empty string when there is nothing to report, so that a
    caller can use the result directly as a "clear the status bar" signal.
    """
    errors, warnings, infos = split_by_severity(notices)
    parts = []
    for label, group in (
        ("error", errors),
        ("warning", warnings),
        ("information", infos),
    ):
        if group:
            parts.append(f"{len(group)} {label}{'' if len(group) == 1 else 's'}")
    if not parts:
        return ""
    fields = sorted({str(n.get("field", "")) for n in errors + warnings + infos if n.get("field")})
    summary = "Scientific validation: " + ", ".join(parts)
    if fields:
        summary += " (" + ", ".join(fields) + ")"
    return summary


def format_detail(notices) -> str:
    """A multi-line detail block for a modal notice, errors first.

    The negative-lattice-conductivity case is stated explicitly rather than
    being implied, because the calculated value is *kept* in the data (it is
    never clipped to zero) and the user needs to know that the number on
    screen is a diagnostic, not a physical value.
    """
    errors, warnings, infos = split_by_severity(notices)
    lines = []
    for label, group in (
        (SEVERITY_LABELS["error"], errors),
        (SEVERITY_LABELS["warning"], warnings),
        (SEVERITY_LABELS["info"], infos),
    ):
        for notice in group:
            field = str(notice.get("field", "") or "data")
            message = str(notice.get("message", ""))
            lines.append(f"{label} [{field}]: {message}")
    if not lines:
        return ""
    return "\n".join(lines)


def negative_lattice_count(notices) -> int:
    """How many notices concern a negative lattice thermal conductivity."""
    count = 0
    for notice in notices or ():
        if str(notice.get("field", "")) == "kappa_L":
            count += 1
    return count


def notice_signature(notices):
    """A hashable signature of the notice set.

    The GUI uses this to show a modal notice only when the set of messages
    has *changed*, so that a recalculation triggered by every cell edit does
    not produce an endless stream of identical dialogs - while the
    persistent status-bar indicator keeps the condition visible.
    """
    return tuple(
        sorted(
            (
                str(notice.get("severity", "")),
                str(notice.get("field", "")),
                str(notice.get("message", "")),
            )
            for notice in (notices or ())
        )
    )
