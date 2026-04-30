"""Rules for excluding metric pairs from correlation comparisons.

Add new rules as plain functions below and register them in RULES.
A pair is excluded if ANY rule returns True.
"""


def _gl_vs_gl2(m1: str, m2: str) -> bool:
    """gl_* and gl2_* metrics measure the same thing across WebGL versions.

    Pairing them inflates apparent correlation (they're almost identical)
    so they should be excluded from max-AMI and similar comparisons.
    """
    m1_is_gl  = m1.startswith('gl_')  and not m1.startswith('gl2_')
    m2_is_gl  = m2.startswith('gl_')  and not m2.startswith('gl2_')
    m1_is_gl2 = m1.startswith('gl2_')
    m2_is_gl2 = m2.startswith('gl2_')
    return (m1_is_gl and m2_is_gl2) or (m2_is_gl and m1_is_gl2)


def _clientrects_hash_vs_clientrects_hash(m1: str, m2: str) -> bool:
    """Two combined clientrects hash metrics can't be meaningfully compared.

    They all summarise the same underlying clientrects measurements via different
    hash aggregations, so high AMI between them reflects shared input data rather
    than an independent correlation signal.
    """
    def is_cr_hash(m):
        return m.startswith('combined_clientrects_') and m.endswith('_hash')
    return is_cr_hash(m1) and is_cr_hash(m2)


def _redundant_metric(m1: str, m2: str) -> bool:
    """Exclude metrics that are known duplicates of another metric.

    These metrics carry no independent signal and would inflate pair counts.
    gl2_vendor has AMI=1.0 with gl_vendor (identical values across browsers).
    """
    _REDUNDANT = {'gl2_vendor'}
    return m1 in _REDUNDANT or m2 in _REDUNDANT


def _font_allowlisted_vs_nonallowlisted(m1: str, m2: str) -> bool:
    """Allow-listed and non-allow-listed variants of the same font metric.

    fonts_variant_X_allowlisted and fonts_variant_X_nonallowlisted measure the
    same underlying font signal filtered two different ways, so pairing them
    reflects shared input rather than an independent correlation.
    """
    def base(m):
        if m.endswith('_allowlisted'):
            return m[:-len('_allowlisted')]
        if m.endswith('_nonallowlisted'):
            return m[:-len('_nonallowlisted')]
        return None
    b1, b2 = base(m1), base(m2)
    return b1 is not None and b2 is not None and b1 == b2


# ── Registry ──────────────────────────────────────────────────────────────────
# Add new rule functions to this list to activate them.
RULES = [
    _gl_vs_gl2,
    _redundant_metric,
    _clientrects_hash_vs_clientrects_hash,
    _font_allowlisted_vs_nonallowlisted,
]


def is_valid_metric_pair_for_comparison(m1: str, m2: str) -> bool:
    """Return True if (m1, m2) is a legitimate pair for correlation analysis."""
    return not any(rule(m1, m2) for rule in RULES)
