import re
import zoneinfo
from datetime import datetime

from utility import *
from webgl_constants import WEBGL_PARAM_METRICS, WEBGL2_PARAM_METRICS, KNOWN_WEBGL_EXTENSIONS, KNOWN_WEBGL_EXTENSIONS_RAW, log_unknown_extensions, _webgl_param_list_for_length

"""
This is the base class for Filters.  A Filter is applied to a DataValues instance and it modifies the object in-place.

  (This means that you cannot compare two different filters without running the analysis twice and saving the results
   in-between, but I think that's an okay limitation.)

When a filter modifies the DataValues instance, it saves the original values so that the filter can be removed.
Filters must be applied and removed in order, they are stored as a stack.
"""
class Filter:
  applied_effect = False
  def __init__(self, dataValues):
    # Modify the dataValues instance as desired.
    # Save the original values in members variables
    raise NotImplementedError("Not Implemented")
  def revert(self, dataValues):
    # Restore the original values
    raise NotImplementedError("Not Implemented")
  def had_an_effect(self):
    # Returns true if the filter modified the values
    return self.applied_effect
  @classmethod
  def affected_metrics(cls):
    """Return the list of DataValues attribute names this filter may modify.
    Subclasses should override this."""
    return []

"""## Define the CorrectionFilter"""

class CorrectionFilter(Filter):
  def __init__(self, dataValues):
    self.originals = {}
    self.originals['screen_primary_video_dynamic_range'] = dataValues.screen_primary_video_dynamic_range
    self.originals['hw_processor_count'] = dataValues.hw_processor_count

    if dataValues.screen_primary_video_dynamic_range and dataValues.screen_primary_color_depth <= 24:
      dataValues.screen_primary_video_dynamic_range = False
      self.applied_effect = True

    # In Nightly this value is actually 128, but we'll use the release value for now...
    if dataValues.hw_processor_count > 128:
      dataValues.hw_processor_count = 128
      self.applied_effect = True

  def revert(self, dataValues):
    dataValues.screen_primary_video_dynamic_range = self.originals['screen_primary_video_dynamic_range']
    dataValues.hw_processor_count = self.originals['hw_processor_count']

# Canvas pairs: (hw_attr, sw_attr) for fill-in when HW is missing but SW exists
_CANVAS_HW_SW_PAIRS = [
    ('canvas_canvasdata01', 'canvassoftware_canvasdata01'),
    ('canvas_canvasdata02', 'canvassoftware_canvasdata02'),
    ('canvas_canvasdata03', 'canvassoftware_canvasdata03'),
    ('canvas_canvasdata04', 'canvassoftware_canvasdata04'),
    ('canvas_canvasdata05', 'canvassoftware_canvasdata05'),
    ('canvas_canvasdata06', 'canvassoftware_canvasdata06'),
    ('canvas_canvasdata07', 'canvassoftware_canvasdata07'),
    ('canvas_canvasdata08', 'canvassoftware_canvasdata08'),
    ('canvas_canvasdata09', 'canvassoftware_canvasdata09'),
    ('canvas_canvasdata10', 'canvassoftware_canvasdata10'),
    ('canvas_canvasdata11_webgl', 'canvassoftware_canvasdata11_webgl'),
    ('canvas_canvasdata12_fingerprintjs1', 'canvassoftware_canvasdata12_fingerprintjs1'),
    ('canvas_canvasdata13_fingerprintjs2', 'canvassoftware_canvasdata13_fingerprintjs2'),
]

# Global counters for reporting — reset by CanvasSoftwareFillIn.reset_counters()
_canvas_fill_counts = {}  # {hw_attr: count}
_canvas_fill_all_count = 0

class CanvasSoftwareFillIn(Filter):
    """If a user has software-rendered canvas but no hardware-rendered canvas,
    fill in the hardware attribute with the software value.

    This corrects for users whose GPU doesn't support hardware canvas rendering,
    ensuring they aren't treated as having no canvas data at all.
    """
    def __init__(self, dataValues):
        global _canvas_fill_counts, _canvas_fill_all_count
        self.originals = {}
        replaced_any = False
        replaced_all = True

        for hw_attr, sw_attr in _CANVAS_HW_SW_PAIRS:
            hw_val = getattr(dataValues, hw_attr)
            sw_val = getattr(dataValues, sw_attr)

            if hw_val == "None" and sw_val != "None":
                self.originals[hw_attr] = hw_val
                setattr(dataValues, hw_attr, sw_val)
                self.applied_effect = True
                replaced_any = True
                _canvas_fill_counts[hw_attr] = _canvas_fill_counts.get(hw_attr, 0) + 1
            else:
                replaced_all = False

        if replaced_any and replaced_all:
            _canvas_fill_all_count += 1

    def revert(self, dataValues):
        for attr, val in self.originals.items():
            setattr(dataValues, attr, val)

    @classmethod
    def affected_metrics(cls):
        return [hw for hw, _ in _CANVAS_HW_SW_PAIRS]

    @staticmethod
    def reset_counters():
        global _canvas_fill_counts, _canvas_fill_all_count
        _canvas_fill_counts = {}
        _canvas_fill_all_count = 0

    @staticmethod
    def report():
        """Return a string summarizing how many users had canvas values filled in."""
        lines = ["Canvas Software Fill-In:"]
        for hw_attr, sw_attr in _CANVAS_HW_SW_PAIRS:
            count = _canvas_fill_counts.get(hw_attr, 0)
            if count:
                lines.append(f"  {count:,} replaced {hw_attr}")
        lines.append(f"  {_canvas_fill_all_count:,} replaced ALL canvas attributes")
        return "\n".join(lines)


class TimezoneBugFix(Filter):
  def __init__(self, dataValues):
    self.originals = {}
    self.originals['intl_timezoneoffset'] = dataValues.intl_timezoneoffset

    try:
      tz = zoneinfo.ZoneInfo(dataValues.intl_timezone)
      now_in_tz = datetime.now(tz)
      offset_timedelta = now_in_tz.utcoffset()
      dataValues.intl_timezoneoffset = offset_timedelta.total_seconds()
    except Exception as e:
      o = backup_timezone(dataValues.intl_timezone)
      if o:
        dataValues.intl_timezoneoffset = float(o)
      else:
        dataValues.intl_timezoneoffset = 0.0

    self.applied_effect = True

  def revert(self, dataValues):
    dataValues.intl_timezoneoffset = self.originals['intl_timezoneoffset']


# Pre-computed DST info: {iana_name: (summer_offset_str, transition_date)}
# Built once at import time for all IANA zones that observe DST.
_DST_SUMMER_OFFSETS = {}  # {name: summer_offset_minutes_str}
_DST_TRANSITION_DATES = {}  # {name: date of spring-forward transition}
def _build_dst_summer_offsets():
    from datetime import timezone as _tz, timedelta
    jan = datetime(2026, 1, 15, 12, tzinfo=_tz.utc)
    jul = datetime(2026, 7, 15, 12, tzinfo=_tz.utc)
    for name in sorted(zoneinfo.available_timezones()):
        try:
            zi = zoneinfo.ZoneInfo(name)
            off_jan = jan.astimezone(zi).utcoffset().total_seconds() / 60
            off_jul = jul.astimezone(zi).utcoffset().total_seconds() / 60
            if off_jan != off_jul:
                summer_off = max(off_jan, off_jul)
                _DST_SUMMER_OFFSETS[name] = str(int(-summer_off))
                # Find the spring-forward transition date by walking days
                prev_off = None
                for d in range(365):
                    dt = datetime(2026, 1, 1, 12, tzinfo=_tz.utc) + timedelta(days=d)
                    off = dt.astimezone(zi).utcoffset().total_seconds() / 60
                    if prev_off is not None and off == summer_off and prev_off != summer_off:
                        _DST_TRANSITION_DATES[name] = dt.date()
                        break
                    prev_off = off
        except Exception:
            pass
_build_dst_summer_offsets()


class DSTNormalizationFilter(Filter):
    """Normalize timezone_offset_web for DST-observing zones so that all
    submissions use the post-spring-forward (summer) offset value.

    This makes the offset stable across DST boundaries, preventing the same
    user from producing different fingerprint hashes before vs. after the
    transition."""

    @classmethod
    def affected_metrics(cls):
        return ['intl_timezone_offset_web']

    # Only apply to submissions in this date window (inclusive)
    _DATE_START = datetime(2026, 3, 25).date()
    _DATE_END   = datetime(2026, 4, 14).date()

    def __init__(self, dataValues):
        self.originals = {}
        self.originals['intl_timezone_offset_web'] = dataValues.intl_timezone_offset_web
        self.applied_effect = False

        # Only apply within the DST transition window
        sub_date = dataValues.submission_date
        if hasattr(sub_date, 'date'):
            sub_date = sub_date.date()
        if sub_date < self._DATE_START or sub_date > self._DATE_END:
            return

        tz_name = dataValues.intl_timezone_web
        summer_offset = _DST_SUMMER_OFFSETS.get(tz_name)
        transition_date = _DST_TRANSITION_DATES.get(tz_name)
        if (summer_offset is not None
                and transition_date is not None
                and self._DATE_START <= transition_date <= self._DATE_END
                and dataValues.intl_timezone_offset_web != summer_offset):
            dataValues.intl_timezone_offset_web = summer_offset
            self.applied_effect = True

    def revert(self, dataValues):
        dataValues.intl_timezone_offset_web = self.originals['intl_timezone_offset_web']

class cpuModelFilter(Filter):
  def __init__(self, dataValues):
    self.originals = {}
    manufacturer, family, microarch, model = self.normalize_cpu_model(dataValues.hw_cpu_model)
    dataValues.hw_cpu_model_manufacturer = manufacturer
    dataValues.hw_cpu_model_family       = family
    dataValues.hw_cpu_model_microarch    = microarch
    dataValues.hw_cpu_model_model        = model
    self.applied_effect = True

  def revert(self, dataValues):
    pass

  def normalize_cpu_model(self, cpu: str) -> tuple:
    # Strip non-ASCII characters (handles encoding corruption like "IntelÂ® Coreâ¢")
    cpu = cpu.encode('ascii', errors='ignore').decode('ascii')

    # Remove trademark symbols (case insensitive)
    cpu = re.sub(r'\(R\)|\(TM\)', '', cpu, flags=re.IGNORECASE)

    # Fix common Intel typos and manglings (before word removal so "Core" gets cleaned)
    cpu = re.sub(r'^lntel\b', 'Intel', cpu)                              # lowercase-L typo
    cpu = re.sub(r'^Inter\b', 'Intel', cpu)                              # "Inter" typo
    cpu = re.sub(r'^Intel\(T\)', 'Intel', cpu)                           # "Intel(T)" mangled trademark
    cpu = re.sub(r'\bCoreT\b', 'Core', cpu)                             # incomplete TM strip: "CoreT"
    cpu = re.sub(r'\bCoreTM\)?', 'Core', cpu)                           # "CoreTM" or "CoreTM)" residue
    cpu = re.sub(r'\bCore\(T[^M)][^)]*\)', 'Core', cpu, flags=re.IGNORECASE)  # Core(TE), Core(TI), etc.
    cpu = re.sub(r'\bCore\(TM\(', 'Core', cpu)                          # "Core(TM(" malformed
    cpu = re.sub(r'\bCore\(PM\)', 'Core', cpu)                          # "Core(PM)"
    cpu = re.sub(r'\bCmre\b', 'Core', cpu)                              # OCR-like corruption
    cpu = re.sub(r'\bCord\(', 'Core(', cpu)                              # OCR-like corruption
    cpu = re.sub(r'\bBore\b', 'Core', cpu)                              # OCR-like corruption
    cpu = re.sub(r'\bAore\b', 'Core', cpu)                              # OCR-like corruption
    cpu = re.sub(r'\bCor\}', 'Core', cpu)                               # "Cor}" corruption

    # Remove "w/" if present (case insensitive)
    cpu = re.sub(r'\bw/\b', '', cpu, flags=re.IGNORECASE)

    # Remove "Mobile Gfx" entirely (case insensitive)
    cpu = re.sub(r'Mobile\s+Gfx', '', cpu, flags=re.IGNORECASE)

    # Collapse "HD Graphics" to "HDGraphics" (case insensitive)
    cpu = re.sub(r'HD\s+Graphics', 'HDGraphics', cpu, flags=re.IGNORECASE)

    # Remove frequency information (anything after '@')
    cpu = re.split(r'\s*@\s*', cpu)[0]

    # Remove common words we don't need (case insensitive)
    cpu = re.sub(r'\bCPU\b', '', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r'\bProcessor\b', '', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r'\bwith\b', '', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r'\d+-Core\b', '', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r' Core ', ' ', cpu, flags=re.IGNORECASE)

    # Remove extra spaces and trim
    cpu = re.sub(r'\s+', ' ', cpu).strip()

    # Handle specific generation notation: Convert "11th Gen" to "11th"
    cpu = re.sub(r'(\d+)(?:th|nd|rd|st)\s+Gen', r'\1th', cpu, flags=re.IGNORECASE)

    # Normalize Apple case variants before manufacturer detection
    cpu = re.sub(r'^Apple\s+silicon\b', 'Apple Silicon', cpu)            # lowercase 's'
    cpu = re.sub(r'^Apple\s+processor\b.*', 'Apple Silicon', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r'^Apple\s+Part\b.*', 'Apple Silicon', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r'^VirtualApple\b', 'Apple Virtual', cpu)

    # Add manufacturer prefix for brands that appear without one
    if re.search(r'\bKryo\b|\bFalkor\b|\bSnapdragon\b|\bKrait\b', cpu, re.IGNORECASE):
      # Qualcomm: Kryo, Falkor, Snapdragon
      if not re.match(r'^Qualcomm\b', cpu, re.IGNORECASE):
        cpu = 'Qualcomm ' + cpu
    elif re.match(r'^exynos\b', cpu, re.IGNORECASE):
      # Samsung Exynos (always lowercase in raw telemetry)
      cpu = re.sub(r'^exynos\b', 'Samsung Exynos', cpu, flags=re.IGNORECASE)
    elif re.match(r'^(Pentium|Celeron|Xeon|Atom)\b', cpu, re.IGNORECASE):
      # Intel sub-brands that appear without "Intel" prefix
      cpu = 'Intel ' + cpu
    elif re.match(r'^TaiShan\b', cpu, re.IGNORECASE):
      # ARM server CPU (Huawei Kunpeng)
      cpu = 'ARM ' + cpu
    elif re.match(r'^(Swift|Firestorm|Avalanche)\b', cpu, re.IGNORECASE):
      # Apple CPU core names
      cpu = 'Apple ' + cpu
    elif re.match(r'^(Neoverse|Denver|Carmel|Ampere)\b', cpu, re.IGNORECASE):
      # ARM server/mobile cores
      cpu = 'ARM ' + cpu
    elif re.match(r'^(Athlon|Ryzen|Sempron|Phenom|Turion|Opteron|EPYC)\b', cpu, re.IGNORECASE):
      # AMD brands without "AMD" prefix
      cpu = 'AMD ' + cpu
    elif re.match(r'^Westmere\b', cpu, re.IGNORECASE):
      # Intel microarchitecture name (VMs)
      cpu = 'Intel ' + cpu
    elif re.match(r'^DO-', cpu):
      # DigitalOcean VPS CPU names
      cpu = 'Virtual ' + cpu
    elif re.match(r'^Common\s+KVM\b', cpu, re.IGNORECASE):
      cpu = 'Virtual KVM'
    elif re.match(r'^Collax\s+Virtual\b', cpu, re.IGNORECASE):
      cpu = 'Virtual Collax'
    elif re.match(r'^StratoVirt\b', cpu, re.IGNORECASE):
      cpu = 'Virtual StratoVirt'
    elif re.match(r'^FTC[0-9]', cpu):
      # Phytium (Chinese ARM CPU)
      cpu = 'Phytium ' + cpu
    elif re.match(r'^\d+\s+APU\b', cpu, re.IGNORECASE):
      # Numeric AMD APU: "410 APU 410 APU with AMD Radeon..."
      cpu = 'AMD ' + cpu

    # Dash handling for specific patterns (order matters)
    cpu = re.sub(r'Cortex-', 'Cortex ', cpu, flags=re.IGNORECASE)
    # Qualcomm Kryo: "Kryo-4XX-Gold" → "Kryo 4XX" (drop tier suffix like Gold/Silver)
    cpu = re.sub(r'\bKryo-(\w+)-\w+', r'Kryo \1', cpu, flags=re.IGNORECASE)
    # Remaining Kryo/Falkor dashes: "Kryo-V2" → "Kryo V2", "Falkor-V1" → "Falkor V1"
    cpu = re.sub(r'\b(Kryo|Falkor)-(\w+)', r'\1 \2', cpu, flags=re.IGNORECASE)
    # Slash in "Falkor-V1/Kryo" → strip the "/Kryo" alias
    cpu = re.sub(r'/Kryo\b', '', cpu, flags=re.IGNORECASE)
    # TaiShan dash
    cpu = re.sub(r'\bTaiShan-', 'TaiShan ', cpu, flags=re.IGNORECASE)
    # Apple M chips: "something-M1" → "something M1"
    cpu = re.sub(r'(.+)-M([0-9])', r'\1 M\2 ', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r'M([0-9])-(.+)', r'\1 \2', cpu, flags=re.IGNORECASE)
    # Intel i-series: "i5-1135G7" → "i5 1135G7" (use \b so it works without leading space)
    cpu = re.sub(r'\bi([0-9])-', r'i\1 ', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r' A([0-9]+)-(.+)', r' A\1 \2', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r'virt-(.+)', r'virt \1', cpu, flags=re.IGNORECASE)
    cpu = re.sub(r' (.+)-(.+) ', r' \1 \2 ', cpu, flags=re.IGNORECASE)

    # Tokenize by whitespace
    tokens = cpu.split()

    # Strip stray punctuation from each token
    tokens = [token.strip(" ,") for token in tokens]

    # Normalize all-caps alphabetic tokens to title case (e.g., "INTEL" → "Intel",
    # "XEON" → "Xeon", "RYZEN" → "Ryzen"), but preserve known acronyms.
    # Only pure-alpha tokens are touched — model numbers like "N4020" are left alone.
    _KEEP_CAPS = {'AMD', 'ARM', 'NVIDIA', 'IBM', 'QEMU', 'KVM', 'EPYC'}
    for _i in range(len(tokens)):
      tok = tokens[_i]
      if tok.isupper() and len(tok) > 2 and tok.isalpha() and tok not in _KEEP_CAPS:
        tokens[_i] = tok.title()

    # Reorder: put generation ordinal after Intel ("11th Intel i5" → "Intel 11th i5")
    if len(tokens) >= 2 and tokens[1] == "Intel":
      tokens = [tokens[1], tokens[0], *tokens[2:]]

    # Remove redundant "Core" token after Intel ("Intel Core i5" → "Intel i5")
    if len(tokens) >= 2 and tokens[0] == "Intel" and tokens[1] == "Core":
      tokens = [tokens[0], *tokens[2:]]

    # Merge specific adjacent tokens
    result_tokens = []
    skip_next = False
    for i, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue

        # Merge "Ryzen" with sub-brand or series number
        if token.lower() == 'ryzen' and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if next_token.lower() in ('ai', 'z1', 'z2'):
                token = 'Ryzen' + next_token.upper()
                skip_next = True
            elif next_token.lower() == 'threadripper':
                token = 'Threadripper'
                skip_next = True
            elif next_token.lower() == 'embedded':
                token = 'RyzenEmbedded'
                skip_next = True
            elif re.match(r'\d', next_token):
                token = token + next_token
                skip_next = True

        # Merge "Radeon" with "Vega": "Radeon" + "Vega8" → "RadeonVega8"
        if token.lower() == 'radeon' and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if next_token.lower().startswith('vega'):
                token = token + next_token
                skip_next = True

        result_tokens.append(token)

    # ── Semantic classification ───────────────────────────────────────────────
    # Derive (manufacturer, family, microarch, model) from the cleaned token list.
    # Coarser classifiers inherit the value of the next coarser one when no
    # additional information is available.

    if not result_tokens:
      return ('', '', '', '')

    model        = '_'.join(result_tokens)
    manufacturer = result_tokens[0]

    _GEN_ORD = re.compile(r'^\d+(?:th|nd|rd|st)$', re.IGNORECASE)

    if manufacturer == 'Intel':
      # tokens: [Intel, (gen?,) tier, (sku?)]
      if len(result_tokens) >= 3 and _GEN_ORD.match(result_tokens[1]):
        gen  = result_tokens[1]   # e.g. '12th'
        tier = result_tokens[2]   # e.g. 'i5'
        family   = f'Intel_{tier}'
        microarch = f'Intel_{gen}_{tier}'
      else:
        tier = result_tokens[1] if len(result_tokens) >= 2 else ''
        family   = f'Intel_{tier}' if tier else 'Intel'
        microarch = family            # no generation label → inherit
      # Post-process special Intel cases
      if tier and re.match(r'^M-', tier):
        # Intel Core M processors: M-5Y10c, M-5Y31, etc.
        family    = 'Intel_CoreM'
        microarch = family
      elif tier and tier.startswith('('):
        # VM architecture names: (Broadwell, (Haswell, (Skylake
        arch = tier.strip('()')
        family    = 'Intel_Virtual'
        microarch = f'Intel_Virtual_{arch}'

    elif manufacturer == 'AMD':
      # tokens: [AMD, Ryzen5/Athlon/FX/Threadripper/RyzenAI/…, (sku?), (gpu?)]
      sub = result_tokens[1] if len(result_tokens) >= 2 else ''
      if sub == 'Threadripper':
        family = 'AMD_Threadripper'
      elif sub.startswith('RyzenAI') or sub.startswith('RyzenZ'):
        family = f'AMD_{sub}'
      else:
        family = f'AMD_{sub}' if sub else 'AMD'
      microarch = family                # AMD strings carry no generation label

    elif manufacturer == 'Qualcomm':
      # tokens: [Qualcomm, Kryo/Falkor/Snapdragon, (gen?,)]
      sub = result_tokens[1] if len(result_tokens) >= 2 else ''
      gen = result_tokens[2] if len(result_tokens) >= 3 else ''
      family    = f'Qualcomm_{sub}' if sub else 'Qualcomm'
      microarch = f'Qualcomm_{sub}_{gen}' if gen else family

    elif manufacturer == 'Apple':
      # tokens: [Apple, M1/M2/Swift/Firestorm/Silicon/Virtual/…]
      chip = result_tokens[1] if len(result_tokens) >= 2 else ''
      if re.match(r'^M\d', chip, re.IGNORECASE):
        family    = 'Apple_M'
        microarch = f'Apple_{chip}'
      elif chip.lower() in ('swift', 'firestorm', 'avalanche', 'virtual', 'silicon', 'a18'):
        family    = 'Apple_Silicon'
        microarch = 'Apple_Silicon'
      else:
        family    = f'Apple_{chip}' if chip else 'Apple'
        microarch = family

    elif manufacturer == 'Samsung':
      # tokens: [Samsung, Exynos, M4/M5/…]
      sub  = result_tokens[1] if len(result_tokens) >= 2 else ''
      core = result_tokens[2] if len(result_tokens) >= 3 else ''
      family    = f'Samsung_{sub}' if sub else 'Samsung'
      microarch = f'Samsung_{sub}_{core}' if core else family

    elif manufacturer == 'Cortex':
      # tokens: [Cortex, A78/X4/…] — core name is all we have
      core = result_tokens[1] if len(result_tokens) >= 2 else ''
      family    = f'Cortex_{core}' if core else 'Cortex'
      microarch = family            # Cortex core name IS the microarch

    elif manufacturer == 'QEMU':
      # tokens: [QEMU, Virtual, CPU, version, …] — "version" and beyond is noise
      sub = result_tokens[1] if len(result_tokens) >= 2 else ''
      family    = f'QEMU_{sub}' if sub else 'QEMU'
      microarch = family          # "version 2.5+" is noise, not microarch detail

    elif manufacturer == 'ARM':
      # tokens: [ARM, TaiShan/Neoverse-N1/Denver/…]
      sub = result_tokens[1] if len(result_tokens) >= 2 else ''
      if sub.startswith('Neoverse'):
        family    = 'ARM_Neoverse'
        microarch = f'ARM_{sub}'
      elif sub == 'TaiShan':
        family    = 'ARM_TaiShan'
        microarch = family
      else:
        family    = f'ARM_{sub}' if sub else 'ARM'
        microarch = family

    elif manufacturer == 'Virtual':
      # tokens: [Virtual, DO-Regular/KVM/Collax/StratoVirt/…]
      sub = result_tokens[1] if len(result_tokens) >= 2 else ''
      family    = f'Virtual_{sub}' if sub else 'Virtual'
      microarch = family

    elif manufacturer == 'Phytium':
      # tokens: [Phytium, FTC663/FTC862/…]
      sub = result_tokens[1] if len(result_tokens) >= 2 else ''
      family    = f'Phytium_{sub}' if sub else 'Phytium'
      microarch = family

    else:
      # Generic fallback — classify as Other (real but unrecognized) or Unknown (garbage)
      label = self._fallback_label(manufacturer)
      manufacturer = label
      family       = label
      microarch    = label

    return (manufacturer, family, microarch, model)

  @staticmethod
  def _fallback_label(first_token: str) -> str:
    """Return 'Unknown' for garbage/useless values, 'Other' for real but unrecognized."""
    if not first_token:
      return 'Unknown'
    s = first_token
    if len(s) <= 3:
      return 'Unknown'
    if s.isdigit():
      return 'Unknown'
    # CPUID family/model codes: "06/55", "19/01"
    if re.match(r'^\d{2}/[0-9a-f]{2}$', s):
      return 'Unknown'
    # All-lowercase gibberish
    if s.islower() and len(s) > 6:
      return 'Unknown'
    # Common generic words
    if s.lower() in ('not', 'none', 'unknown', 'default', 'empty', 'general', 'high'):
      return 'Unknown'
    return 'Other'

class webglRendererRawFilter(Filter):
  """Classify the raw WebGL renderer string into four semantic dimensions:

    vendor  — GPU hardware manufacturer (Intel, NVIDIA, AMD, Mali, Adreno,
               Apple, PowerVR, Samsung, Microsoft, software)
    family  — Product line (Intel_UHD, Intel_IrisXe, NVIDIA_RTX, AMD_RX_6xxx,
               Mali_G, Adreno_700s, Apple_M1, …)
    model   — Specific chip without driver-version noise (Intel_UHD_630,
               NVIDIA_RTX_3060, Mali-G57_MC2, Adreno_740, Apple_M1_Pro, …)
    api     — Rendering platform (ANGLE_D3D11, ANGLE_Vulkan, Mesa, macOS,
               mobile, software)

  The old friendly_1/2/3 attributes are removed; the four named classifiers
  replace them.
  """

  def __init__(self, dataValues):
    self.originals = {}
    raw = getattr(dataValues, 'webgl_renderer_raw', None)
    vendor, family, model, api = self.normalize_renderer(raw)
    dataValues.webgl_renderer_raw_vendor = vendor
    dataValues.webgl_renderer_raw_family = family
    dataValues.webgl_renderer_raw_model  = model
    dataValues.webgl_renderer_raw_api    = api
    self.applied_effect = True

  def revert(self, dataValues):
    for attr, val in self.originals.items():
      setattr(dataValues, attr, val)

  # ── Low-level helpers ───────────────────────────────────────────────────

  @staticmethod
  def _strip(s):
    """Remove (R) and (TM) trademark markers (with optional leading space)."""
    return re.sub(r'\s*\((?:R|TM)\)', '', s).strip()

  @staticmethod
  def _classify_intel(name):
    """Return (family, model) for a cleaned Intel GPU name string."""
    # Iris Xe / Xe Graphics (Arc and 12th-gen+)
    if re.search(r'Iris\s+Xe|Xe\s+Graphics', name, re.IGNORECASE):
      return ('Intel_IrisXe', 'Intel_IrisXe')
    # Iris Pro
    if re.search(r'Iris\s+Pro', name, re.IGNORECASE):
      m = re.search(r'(\d{4})', name)
      return ('Intel_IrisPro', f'Intel_IrisPro_{m.group(1)}' if m else 'Intel_IrisPro')
    # Iris (plain)
    if re.search(r'\bIris\b', name, re.IGNORECASE):
      m = re.search(r'(\d{3,4})', name)
      return ('Intel_Iris', f'Intel_Iris_{m.group(1)}' if m else 'Intel_Iris')
    # UHD Graphics
    if re.search(r'\bUHD\b', name, re.IGNORECASE):
      m = re.search(r'UHD\s+(?:Graphics\s+)?(\d{3,4})', name, re.IGNORECASE)
      return ('Intel_UHD', f'Intel_UHD_{m.group(1)}' if m else 'Intel_UHD')
    # HD Graphics
    if re.search(r'\bHD\b', name, re.IGNORECASE):
      m = re.search(r'HD\s+(?:Graphics\s+)?(\d{3,4})', name, re.IGNORECASE)
      return ('Intel_HD', f'Intel_HD_{m.group(1)}' if m else 'Intel_HD')
    # Generic "Intel Graphics" (Intel 4-series, Alder/Raptor/Meteor Lake)
    return ('Intel_Graphics', 'Intel_Graphics')

  @staticmethod
  def _classify_nvidia(name):
    """Return (family, model) for a cleaned NVIDIA GPU name string."""
    if re.search(r'\bRTX\b', name, re.IGNORECASE):
      m = re.search(r'RTX\s+([\d]+\s*\w*)', name, re.IGNORECASE)
      if m:
        tag = m.group(1).strip().replace(' ', '_')
        return ('NVIDIA_RTX', f'NVIDIA_RTX_{tag}')
      return ('NVIDIA_RTX', 'NVIDIA_RTX')
    if re.search(r'\bGTX\b', name, re.IGNORECASE):
      m = re.search(r'GTX\s+([\d]+\w*)', name, re.IGNORECASE)
      return ('NVIDIA_GTX', f'NVIDIA_GTX_{m.group(1)}' if m else 'NVIDIA_GTX')
    if re.search(r'\bQuadro\b', name, re.IGNORECASE):
      return ('NVIDIA_Quadro', 'NVIDIA_Quadro')
    if re.search(r'\bTesla\b', name, re.IGNORECASE):
      return ('NVIDIA_Tesla', 'NVIDIA_Tesla')
    # Numeric model (e.g. GeForce 940MX)
    m = re.search(r'(\d{3,4}\w*)', name)
    return ('NVIDIA', f'NVIDIA_{m.group(1)}' if m else 'NVIDIA')

  @staticmethod
  def _classify_amd(name):
    """Return (family, model) for a cleaned AMD/ATI GPU name string."""
    # Legacy ATI
    if re.search(r'\bATI\b', name, re.IGNORECASE):
      m = re.search(r'HD\s+(\d+)', name, re.IGNORECASE)
      return ('AMD_ATI', f'AMD_ATI_HD{m.group(1)}' if m else 'AMD_ATI')
    # Radeon RX (discrete, numbered)
    if re.search(r'Radeon\s+RX\b', name, re.IGNORECASE):
      m = re.search(r'RX\s+([\d]+\s*\w*)', name, re.IGNORECASE)
      if m:
        tag = m.group(1).strip()
        d = re.match(r'(\d)', tag)
        family = f'AMD_RX_{d.group(1)}xxx' if d else 'AMD_RX'
        return (family, f'AMD_RX_{tag.replace(" ", "_")}')
      return ('AMD_RX', 'AMD_RX')
    # Radeon Pro (macOS discrete)
    if re.search(r'Radeon\s+Pro\b', name, re.IGNORECASE):
      m = re.search(r'Pro\s+(\w+)', name, re.IGNORECASE)
      return ('AMD_RadeonPro', f'AMD_RadeonPro_{m.group(1)}' if m else 'AMD_RadeonPro')
    # Vega (integrated or discrete)
    if re.search(r'\bVega\b', name, re.IGNORECASE):
      m = re.search(r'Vega\s+(\d+)', name, re.IGNORECASE)
      return ('AMD_Vega', f'AMD_Vega{m.group(1)}' if m else 'AMD_Vega')
    # Radeon R5/R7/R9 (older discrete)
    if re.search(r'Radeon\s+R[579]\b', name, re.IGNORECASE):
      m = re.search(r'(R[579])', name, re.IGNORECASE)
      fam = f'AMD_{m.group(1).upper()}' if m else 'AMD_R'
      return (fam, fam)
    # Custom GPU (Steam Deck)
    if re.search(r'Custom\s+GPU', name, re.IGNORECASE):
      m = re.search(r'Custom\s+GPU\s+(\w+)', name, re.IGNORECASE)
      return ('AMD_Custom', f'AMD_Custom_{m.group(1)}' if m else 'AMD_Custom')
    # Generic APU (e.g. "AMD Radeon Graphics", "AMD Radeon  Graphics")
    if re.search(r'Radeon\s+Graphics', name, re.IGNORECASE):
      return ('AMD_RadeonGraphics', 'AMD_RadeonGraphics')
    # Numbered Radeon (e.g. "AMD Radeon 660M")
    m = re.search(r'Radeon\s+(\w+)', name, re.IGNORECASE)
    if m:
      return ('AMD_Radeon', f'AMD_Radeon_{m.group(1)}')
    return ('AMD', 'AMD')

  @staticmethod
  def _classify_mali(name, api):
    """Return (vendor, family, model, api) for a Mali GPU name."""
    m = re.match(r'(?i)Mali-([GT])(\d+)', name)
    if m:
      gen = m.group(1).upper()   # G or T
      model = re.sub(r'\s+', '_', name.strip())
      return ('Mali', f'Mali_{gen}', model, api)
    return ('Mali', 'Mali', name, api)

  # ── ANGLE inner GPU name parser ─────────────────────────────────────────

  def _parse_angle_gpu(self, outer_vendor, gpu_api_str):
    """Extract (vendor, family, model) from the middle part of an ANGLE string.

    gpu_api_str is everything between the outer vendor and the driver token,
    e.g. 'Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0'.
    """
    # Strip the API type and shader-profile suffix
    gpu_name = re.sub(
        r'\s+(?:Direct3D\d+|OpenGL\s+[\d.]+|Vulkan\s+[\d.]+)\b.*$',
        '', gpu_api_str, flags=re.IGNORECASE
    ).strip()
    gpu_name = self._strip(gpu_name)

    ov = outer_vendor.lower()
    if 'intel' in ov:
      fam, mod = self._classify_intel(gpu_name)
      return ('Intel', fam, mod)
    if 'nvidia' in ov:
      fam, mod = self._classify_nvidia(gpu_name)
      return ('NVIDIA', fam, mod)
    if 'amd' in ov:
      fam, mod = self._classify_amd(gpu_name)
      return ('AMD', fam, mod)
    if 'microsoft' in ov:
      return ('Microsoft', 'Microsoft_BasicRender', 'Microsoft_BasicRender')
    if 'samsung' in ov:
      return ('Samsung', 'Samsung_Xclipse', gpu_name)
    if 'arm' in ov:
      # ARM = Mali GPU; gpu_name may be a Vulkan wrapper "Vulkan X.Y (Mali-G68 MC4 (0x...))"
      cleaned = re.sub(r'\s*\(0x[0-9a-fA-F]+\)', '', gpu_name).strip()
      vk = re.match(r'(?i)Vulkan\s+[\d.]+\s*\((.+)\)\s*$', cleaned)
      if vk:
        inner = vk.group(1).strip()
        if re.match(r'(?i)Mali-', inner):
          v, fam, mod, _ = self._classify_mali(inner, 'ANGLE_Vulkan')
          return (v, fam, mod)
      if re.match(r'(?i)Mali-', gpu_name):
        v, fam, mod, _ = self._classify_mali(gpu_name, 'ANGLE_Vulkan')
        return (v, fam, mod)
      return ('Mali', 'Mali', gpu_name)
    if 'imagination' in ov or 'powervr' in ov:
      # Imagination Technologies / PowerVR — gpu_name may be "Vulkan 1.3.x (PowerVR ...)"
      cleaned = re.sub(r'\s*\(0x[0-9a-fA-F]+\)', '', gpu_name).strip()
      v, fam, mod, _ = self.normalize_renderer(cleaned)
      if v != cleaned:  # was classified (not the raw-string fallback)
        return (v, fam, mod)
      return ('PowerVR', 'PowerVR', gpu_name)
    # 'unknown' outer vendor — check GPU description for Qualcomm/Adreno or Parallels
    if re.search(r'(?i)Parallels\b', gpu_name):
      return ('Microsoft', 'Microsoft_Parallels', 'Microsoft_Parallels')
    if re.search(r'qualcomm|adreno', gpu_name, re.IGNORECASE):
      am = re.search(r'Adreno\s+(X?\d[\w\-]*)', gpu_name, re.IGNORECASE)
      if am:
        chip = am.group(1)
        if chip.upper().startswith('X'):
          return ('Adreno', 'Adreno_X', f'Adreno_{chip}')
        return ('Adreno', f'Adreno_{chip[0]}00s', f'Adreno_{chip}')
      return ('Adreno', 'Adreno', gpu_name)
    return (outer_vendor, outer_vendor, gpu_name)

  # ── Main normalizer ─────────────────────────────────────────────────────

  def normalize_renderer(self, raw):
    """Classify a WebGL renderer string → (vendor, family, model, api)."""
    if not raw or not isinstance(raw, str):
      v = raw if raw else 'None'
      return (v, v, v, 'unknown')

    s = raw.strip()

    # ── Samsung Xclipse (ANGLE over Vulkan) ──────────────────────────────
    # Formats:  ANGLE (Samsung Xclipse 530) on Vulkan 1.3.279
    #           ANGLE ((Samsung Xclipse 540) on Vulkan 1.3.279)   ← double paren
    #           angle (Samsung Xclipse 920) on Vulkan 1.1.179     ← lowercase
    xm = re.match(r'(?i)angle\s*\(+samsung\s+xclipse\s+(\d+)', s)
    if xm:
      chip = xm.group(1)
      return ('Samsung', 'Samsung_Xclipse', f'Samsung_Xclipse_{chip}', 'ANGLE_Vulkan')

    # ── Virtio-GPU Venus (ANGLE Vulkan paravirt) ─────────────────────────
    # ANGLE (ARM, Vulkan 1.3.269 (Virtio-GPU Venus (Mali-G72) (0x...)))
    # Inner GPU names may contain nested parens: Intel(R), (RADV RAVEN), etc.
    if 'Virtio-GPU Venus' in s:
      vm = re.search(r'Virtio-GPU Venus \(((?:[^()]|\([^()]*\))+?)\)', s)
      outer_m = re.match(r'(?i)ANGLE\s*\(\s*([^,()]+)', s)
      outer_vendor = outer_m.group(1).strip() if outer_m else 'Unknown'
      if vm:
        inner = re.sub(r'\s*\([^)]+\)\s*$', '', self._strip(vm.group(1))).strip()
        if re.match(r'(?i)Mali-', inner):
          return self._classify_mali(inner, 'ANGLE_Vulkan')
        if re.search(r'\bIntel\b', inner, re.IGNORECASE):
          fam, mod = self._classify_intel(inner)
          return ('Intel', fam, mod, 'ANGLE_Vulkan')
        if re.search(r'\bAMD\b', inner, re.IGNORECASE):
          fam, mod = self._classify_amd(inner)
          return ('AMD', fam, mod, 'ANGLE_Vulkan')
        return (outer_vendor, outer_vendor, inner, 'ANGLE_Vulkan')
      return ('Unknown', 'Unknown', 'Virtio-GPU', 'ANGLE_Vulkan')

    # ── virgl (VirtIO GPU passthrough wrapping a real GPU) ───────────────
    # virgl (Mesa Intel(R) UHD Graphics 600 (GLK 2))
    # virgl (Apple M1 Pro (Compat))
    # virgl  (bare, no inner info)
    if re.match(r'(?i)virgl\b', s):
      vm = re.match(r'(?i)virgl\s*\(\s*(.+?)\s*\)\s*$', s)
      if vm:
        inner = vm.group(1)
        # Strip trailing parenthetical (version/compat tags)
        inner_clean = re.sub(r'\s*\([^)]*\)\s*$', '', inner).strip()
        if re.search(r'\bIntel\b', inner_clean, re.IGNORECASE):
          gpu_clean = self._strip(re.sub(r'^Mesa\s+(?:DRI\s+)?', '', inner_clean, flags=re.IGNORECASE))
          gpu_clean = re.sub(r'\s*\([^)]+\)\s*$', '', gpu_clean).strip()
          fam, mod = self._classify_intel(gpu_clean)
          return ('Intel', fam, mod, 'Mesa')
        apple_m2 = re.match(r'Apple\s+(M\d+)((?:\s+\w+)?)', inner_clean)
        if apple_m2:
          gen = apple_m2.group(1)
          variant = apple_m2.group(2).strip()
          mod = f'Apple_{gen}_{variant}' if variant else f'Apple_{gen}'
          return ('Apple', f'Apple_{gen}', mod, 'macOS')
      return ('Unknown', 'virgl', 'virgl', 'Mesa')

    # ── Standard ANGLE (vendor, gpu+api+shader, driver) ──────────────────
    # The driver token is the last comma-separated element inside ANGLE(...)
    if re.match(r'(?i)ANGLE\s*\(', s):
      inner_m = re.match(r'(?i)ANGLE\s*\(\s*([^,()]+?)\s*,\s*(.*)\s*\)\s*$', s)
      if inner_m:
        outer_vendor = inner_m.group(1).strip()
        rest = inner_m.group(2).strip()
        lc = rest.rfind(',')
        if lc >= 0:
          gpu_api_part = rest[:lc].strip()
          driver_part  = rest[lc + 1:].strip()
          dp = driver_part.upper()
          if dp.startswith('D3D11') or 'DIRECT3D11' in gpu_api_part.upper():
            api = 'ANGLE_D3D11'
          elif dp.startswith('D3D9') or 'DIRECT3D9' in gpu_api_part.upper():
            api = 'ANGLE_D3D9'
          elif 'VULKAN' in gpu_api_part.upper() or dp.startswith('VK'):
            api = 'ANGLE_Vulkan'
          elif dp.startswith('GL_') or 'OPENGL' in gpu_api_part.upper():
            api = 'ANGLE_GL'
          elif dp.startswith('MTL') or 'METAL' in dp:
            api = 'ANGLE_Metal'
          else:
            api = 'ANGLE'
          vendor, family, model = self._parse_angle_gpu(outer_vendor, gpu_api_part)
          return (vendor, family, model, api)
      # ANGLE but can't fully parse
      om = re.match(r'(?i)ANGLE\s*\(\s*([^,()]+)', s)
      outer = om.group(1).strip() if om else 'ANGLE'
      return ('Unknown', 'ANGLE', f'ANGLE_{outer}', 'ANGLE')

    # ── Software renderers ───────────────────────────────────────────────
    sl = s.lower()
    if sl.startswith('llvmpipe'):
      return ('software', 'software_llvmpipe', 'software_llvmpipe', 'software')
    if 'swiftshader' in sl:
      return ('software', 'software_SwiftShader', 'software_SwiftShader', 'software')
    if sl.startswith('softpipe'):
      return ('software', 'software_softpipe', 'software_softpipe', 'software')
    if s == 'Apple Software Renderer':
      return ('software', 'software_Apple', 'software_Apple', 'software')

    # Gallium (older Mesa Gallium format: "Gallium 0.4 on llvmpipe ...", "Gallium 0.4 on NVD9")
    gallium_m = re.match(r'(?i)Gallium.*?\bon\s+(\S+)', s)
    if gallium_m:
      target = gallium_m.group(1)
      target_low = target.lower().rstrip('(')
      if 'llvmpipe' in target_low or 'softpipe' in target_low:
        return ('software', 'software_llvmpipe', 'software_llvmpipe', 'software')
      if re.match(r'nv[0-9a-f]{2}', target_low):
        return ('NVIDIA', 'NVIDIA', f'NVIDIA_Nouveau_{target.upper()}', 'Mesa')
      return ('Unknown', f'Gallium_{target}', f'Gallium_{target}', 'Mesa')

    # ── Mesa / Linux open-source ─────────────────────────────────────────
    # Mesa Intel ..., Mesa DRI Intel ..., Mesa Mobile Intel ..., Mesa AMD ..., Mesa Radeon ...
    if re.match(r'Mesa\s+(?:DRI\s+|Mobile\s+|i965\s+)?(?:Intel|AMD|Radeon)', s, re.IGNORECASE):
      is_intel = bool(re.search(r'\bIntel\b', s[:50], re.IGNORECASE))
      gpu_part = re.sub(r'^Mesa\s+(?:DRI\s+|Mobile\s+|i965\s+)?', '', s, flags=re.IGNORECASE)
      gpu_part = re.sub(r'\s*\([^)]+\)\s*$', '', gpu_part).strip()
      gpu_clean = self._strip(gpu_part)
      if is_intel:
        fam, mod = self._classify_intel(gpu_clean)
        return ('Intel', fam, mod, 'Mesa')
      fam, mod = self._classify_amd(gpu_clean)
      return ('AMD', fam, mod, 'Mesa')

    # AMD/Radeon with Mesa parenthetical — radeonsi, amdgpu, or any codename+LLVM pattern
    if re.match(r'(?i)(?:AMD|Radeon)\b', s) and re.search(r'\([^)]*(?:radeonsi|amdgpu|,\s*LLVM\b)', s, re.IGNORECASE):
      gpu_name = s[:s.find('(')].strip()
      fam, mod = self._classify_amd(gpu_name)
      return ('AMD', fam, mod, 'Mesa')

    # AMD codename only: RENOIR (renoir, ...), VANGOGH (vangogh, ...), KABINI (, ...)
    cm = re.match(r'^([A-Z][A-Z0-9]+)\s*\(([a-z][a-z0-9_]+|,)', s)
    if cm:
      codename = cm.group(1)
      return ('AMD', f'AMD_{codename.title()}', f'AMD_{codename.title()}', 'Mesa')

    # ── Mobile GPUs ──────────────────────────────────────────────────────
    # Maleoon (HiSilicon/Huawei Kirin GPU)
    if re.match(r'(?i)Maleoon\b', s):
      mm = re.match(r'(?i)Maleoon\s+(\w+)', s)
      chip = mm.group(1) if mm else ''
      return ('Maleoon', 'Maleoon', f'Maleoon_{chip}' if chip else 'Maleoon', 'mobile')

    # Mali
    if re.match(r'(?i)Mali-', s):
      return self._classify_mali(s, 'mobile')

    # Imagination Technologies (PowerVR maker, appears as bare vendor name)
    if re.match(r'(?i)Imagination\s+Technologies', s):
      return ('PowerVR', 'PowerVR', 'PowerVR', 'mobile')

    # Adreno (TM) with no chip number (generic)
    if re.match(r'(?i)Adreno\s*(?:\(TM\))?\s*$', s):
      return ('Adreno', 'Adreno', 'Adreno', 'mobile')

    # Adreno (TM) XXX
    am = re.match(r'(?i)Adreno\s+(?:\(TM\)\s+)?([\w\-]+)', s)
    if am:
      chip = am.group(1).strip()
      if chip.upper().startswith('X'):
        return ('Adreno', 'Adreno_X', f'Adreno_{chip}', 'mobile')
      series = chip[0] + '00s' if chip[:1].isdigit() else chip
      return ('Adreno', f'Adreno_{series}', f'Adreno_{chip}', 'mobile')

    # PowerVR
    if s.startswith('PowerVR'):
      # Match 1 or 2 words after PowerVR; chip is the last word, series is the first (if 2 words)
      pm = re.match(r'PowerVR\s+(\S+)(?:\s+(\S+))?', s)
      if pm:
        word1 = pm.group(1)
        word2 = pm.group(2) or ''
        chip_word   = word2 if word2 else word1
        series_word = word1 if word2 else ''
        if 'BXM' in word1 or 'BXM' in word2:
          cm2 = re.search(r'(BXM[\w\-]+)', s)
          chip = cm2.group(1) if cm2 else chip_word
          return ('PowerVR', 'PowerVR_BXM', f'PowerVR_{chip}', 'mobile')
        if re.search(r'[DA]XT', word1) or re.search(r'[DA]XT', word2):
          cm2 = re.search(r'([DA]XT[\w\-]+)', s)
          chip = cm2.group(1) if cm2 else chip_word
          return ('PowerVR', 'PowerVR_DXT', f'PowerVR_{chip}', 'mobile')
        fam = f'PowerVR_{series_word}' if series_word else 'PowerVR'
        return ('PowerVR', fam, f'PowerVR_{chip_word}', 'mobile')
      return ('PowerVR', 'PowerVR', s, 'mobile')

    # Vulkan version prefix wrapping a GPU name: "Vulkan 1.3.xxx (PowerVR ...)"
    vk_m = re.match(r'(?i)Vulkan\s+[\d.]+\s*\((.+)\)\s*$', s)
    if vk_m:
      inner = vk_m.group(1).strip()
      # Strip trailing hex ID
      inner = re.sub(r'\s*\(0x[0-9a-fA-F]+\)\s*$', '', inner).strip()
      if re.search(r'\bPowerVR\b', inner, re.IGNORECASE):
        return self.normalize_renderer(inner)  # re-classify
      if re.match(r'(?i)Mali-', inner):
        return self._classify_mali(inner, 'mobile')
      return ('Unknown', 'Unknown', inner, 'unknown')

    # Parallels Display Adapter (VM virtual GPU on macOS)
    if re.search(r'(?i)Parallels', s):
      return ('Microsoft', 'Microsoft_Parallels', 'Microsoft_Parallels', 'ANGLE_D3D11')

    # i915 (chipset: ...) — ancient Intel Mesa
    if re.match(r'(?i)i915\b', s):
      return ('Intel', 'Intel_Graphics', 'Intel_i915', 'Mesa')

    # V3D (Raspberry Pi VideoCore VI)
    if re.match(r'V3D\b', s):
      return ('Broadcom', 'Broadcom_V3D', 'Broadcom_V3D', 'Mesa')

    # FD (Freedreno — Mesa driver for Qualcomm Adreno)
    fd_m = re.match(r'FD(\d+)\s*$', s, re.IGNORECASE)
    if fd_m:
      chip = fd_m.group(1)
      return ('Adreno', 'Adreno_Freedreno', f'Adreno_FD{chip}', 'Mesa')

    # ── Apple Silicon (macOS) ─────────────────────────────────────────────
    apple_m = re.match(r'Apple\s+(M\d+)((?:\s+\w+)?)', s)
    if apple_m:
      gen     = apple_m.group(1)              # M1, M2, M3, M4
      variant = apple_m.group(2).strip()      # Pro, Max, Ultra, or ''
      model   = f'Apple_{gen}_{variant}' if variant else f'Apple_{gen}'
      return ('Apple', f'Apple_{gen}', model, 'macOS')

    # ── macOS Intel OpenGL (non-Mesa, non-ANGLE) ──────────────────────────
    # Intel(R) HD Graphics 6000, Intel HD Graphics 4000 OpenGL Engine, etc.
    if re.match(r'(?i)Intel\b', s):
      clean = self._strip(s)
      clean = re.sub(r'\s+OpenGL Engine.*$', '', clean, flags=re.IGNORECASE).strip()
      fam, mod = self._classify_intel(clean)
      return ('Intel', fam, mod, 'macOS')

    # ── macOS AMD / ATI OpenGL ────────────────────────────────────────────
    if re.match(r'(?i)(?:AMD|ATI)\b', s):
      clean = self._strip(s)
      clean = re.sub(r'\s+OpenGL Engine.*$', '', clean, flags=re.IGNORECASE).strip()
      fam, mod = self._classify_amd(clean)
      return ('AMD', fam, mod, 'macOS')

    # ── NVIDIA Linux (Nouveau codenames, direct OpenGL) ──────────────────
    # Bare Nouveau chip codes: NV106, NVC1, NVE4, NVA8, NV98, etc.
    if re.match(r'NV[0-9A-Fa-f]{2,4}\s*$', s):
      return ('NVIDIA', 'NVIDIA', f'NVIDIA_Nouveau_{s.strip().upper()}', 'Mesa')

    # GeForce/Quadro/NVS .../PCIe/SSE2, or generic /PCIe/SSE2 suffix
    if re.match(r'(?i)(?:GeForce|Quadro|NVS)\b', s) or '/PCIe/SSE2' in s:
      clean = re.sub(r'\s*/PCIe.*$', '', s, flags=re.IGNORECASE).strip()
      fam, mod = self._classify_nvidia(clean)
      return ('NVIDIA', fam, mod, 'Mesa')

    # ── macOS NVIDIA OpenGL ───────────────────────────────────────────────
    if re.match(r'(?i)NVIDIA\b', s):
      clean = self._strip(s)
      clean = re.sub(r'\s+OpenGL Engine.*$', '', clean, flags=re.IGNORECASE).strip()
      fam, mod = self._classify_nvidia(clean)
      return ('NVIDIA', fam, mod, 'macOS')

    # ── Version-prefixed driver strings (rare macOS / Linux) ─────────────
    # "4.6.0 NVIDIA-16.4.3 310.90.10.05b12", "4.1 ATI-...", "4.1 INTEL-..."
    ver_m = re.match(r'(\d+\.\d+)(?:\.\d+)?\s+(NVIDIA|ATI|INTEL)-', s)
    if ver_m:
      brand = ver_m.group(2).upper()
      return {'NVIDIA': ('NVIDIA', 'NVIDIA',  'NVIDIA',  'macOS'),
              'ATI':    ('AMD',    'AMD_ATI', 'AMD_ATI', 'macOS'),
              'INTEL':  ('Intel',  'Intel',   'Intel',   'macOS')}.get(
                  brand, ('Unknown', 'Unknown', 'Unknown', 'macOS'))

    # "4.6.0 NVIDIA 390.xx" (Linux style)
    ver_m2 = re.match(r'(\d+\.\d+\.\d+)\s+NVIDIA\s+([\d.]+)', s)
    if ver_m2:
      return ('NVIDIA', 'NVIDIA', 'NVIDIA', 'Linux')

    # Metal version string: "4.1 Metal - 83.5"
    if re.match(r'\d+\.\d+\s+Metal\s*-', s):
      return ('Unknown', 'Metal', 'Metal', 'macOS')

    # Mesa version string: "4.6.0 Mesa 21.2.6" (unusual)
    if re.match(r'\d+\.\d+.*\bMesa\b', s):
      return ('Unknown', 'Mesa', 'Mesa', 'Mesa')

    # OpenGL ES with ANGLE
    if re.match(r'(?i)OpenGL\s+ES.*ANGLE', s):
      return ('Unknown', 'ANGLE', 'ANGLE_GLES', 'ANGLE')

    # Fallback — keep model as cleaned raw for fingerprinting,
    # but use clean labels for vendor/family
    model_clean = re.sub(r'\s+', '_', s.strip())
    label = self._fallback_label(s)
    return (label, label, model_clean, 'unknown')

  @staticmethod
  def _fallback_label(raw: str) -> str:
    """Return 'Unknown' for garbage/useless, 'Other' for real but unrecognized."""
    s = raw.strip()
    if not s or len(s) <= 3:
      return 'Unknown'
    # Version strings, hex IDs, numeric-only
    if s[0].isdigit():
      return 'Unknown'
    # All-lowercase or contains semicolons (driver debug strings)
    if s.islower() or ';' in s:
      return 'Unknown'
    return 'Other'


class machineModelFilter(Filter):
  """Classify hw_machine_model into three semantic dimensions:

    vendor   — device manufacturer (HP, Dell, Samsung, Apple, Google, …)
    category — form factor (laptop, desktop, mobile, tablet, vm, unknown)
    family   — product line (HP_EliteBook, Dell_OptiPlex, Samsung_GalaxyS, …)

  Writes hw_machine_model_vendor, hw_machine_model_category, and
  hw_machine_model_family onto dataValues.
  """

  _JUNK = re.compile(
    r'(?i)^(?:system\s+product\s+name|to\s+be?\s+filled\s+by\s+o\.?e\.?m\.?|'
    r'all\s+series|default\s+string|by\s+oem|null|none|not\s+applicable|n/?a|'
    r'invalid|standard(?:\s*-?\s*)pc|base\s*board|oem|[-\s]*not\s+specified|'
    r'0x[0-9a-f]+|sku|by\s+\w+|mypc|standard\s+pc|'
    # Additional junk patterns
    r'system\s+sku\S*|asus-notebooksku|type1sku0|empty|'
    r'0{6,}|[0-9a-f]{4}|'  # all-zero or 4-digit hex IDs (0BE0, 0A20, etc.)
    r'default|standard)$'
  )

  # ── Apple Mac##,# → product family lookup ──────────────────────────────
  # Maps "Mac<major>,<minor>" to (category, family).
  # Source: Apple platform identifiers. Covers all Apple Silicon Macs.
  _APPLE_MAC_IDS = {
    # Mac13 — M2 Mac mini, MacBook Pro (2022 pre-release)
    'Mac13,1': ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M2 Pro (early)
    'Mac13,2': ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M2 Max (early)
    # Mac14 — M2 generation
    'Mac14,2':  ('laptop',  'Apple_MacBookAir'),   # MacBook Air 13" M2
    'Mac14,3':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M2 Pro
    'Mac14,5':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M2 Max
    'Mac14,6':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M2 Pro
    'Mac14,7':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 13" M2
    'Mac14,8':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M2 Max
    'Mac14,9':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M2 Max
    'Mac14,10': ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M2 Pro
    'Mac14,12': ('desktop', 'Apple_MacMini'),      # Mac Mini M2
    'Mac14,13': ('desktop', 'Apple_MacStudio'),    # Mac Studio M2 Max
    'Mac14,14': ('desktop', 'Apple_MacStudio'),    # Mac Studio M2 Ultra
    'Mac14,15': ('laptop',  'Apple_MacBookAir'),   # MacBook Air 15" M2
    # Mac15 — M3 generation
    'Mac15,3':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M3 Pro
    'Mac15,4':  ('desktop', 'Apple_iMac'),         # iMac 24" M3
    'Mac15,5':  ('desktop', 'Apple_iMac'),         # iMac 24" M3
    'Mac15,6':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M3 Pro
    'Mac15,7':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M3 Max
    'Mac15,8':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M3 Max
    'Mac15,9':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M3 Max
    'Mac15,10': ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M3 Max
    'Mac15,11': ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M3 Max
    'Mac15,12': ('laptop',  'Apple_MacBookAir'),   # MacBook Air 13" M3
    'Mac15,13': ('laptop',  'Apple_MacBookAir'),   # MacBook Air 15" M3
    'Mac15,14': ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M3
    # Mac16 — M4 generation
    'Mac16,1':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M4 Pro
    'Mac16,2':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M4 Max
    'Mac16,3':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M4 Pro
    'Mac16,4':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M4 Max
    'Mac16,5':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M4 Max
    'Mac16,6':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M4 Max
    'Mac16,7':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 14" M4 Pro
    'Mac16,8':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro 16" M4 Pro
    'Mac16,9':  ('desktop', 'Apple_MacPro'),       # Mac Pro M4 Ultra (placeholder)
    'Mac16,10': ('desktop', 'Apple_iMac'),         # iMac 24" M4
    'Mac16,11': ('desktop', 'Apple_MacMini'),      # Mac Mini M4
    'Mac16,12': ('desktop', 'Apple_MacMini'),      # Mac Mini M4 Pro
    'Mac16,13': ('desktop', 'Apple_MacStudio'),    # Mac Studio M4
    'Mac16,14': ('laptop',  'Apple_MacBookAir'),   # MacBook Air 13" M4
    'Mac16,15': ('laptop',  'Apple_MacBookAir'),   # MacBook Air 15" M4
    # Mac17 — M5 generation
    'Mac17,2':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro M5
    'Mac17,3':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro M5
    'Mac17,4':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro M5
    'Mac17,5':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro M5
    'Mac17,6':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro M5
    'Mac17,7':  ('laptop',  'Apple_MacBookPro'),   # MacBook Pro M5
    'Mac17,8':  ('desktop', 'Apple_MacMini'),      # Mac Mini M5
    'Mac17,9':  ('desktop', 'Apple_MacMini'),      # Mac Mini M5
  }

  def __init__(self, dataValues):
    self.originals = {}
    vendor, category, family = self.normalize(dataValues.hw_machine_model)
    dataValues.hw_machine_model_vendor   = vendor
    dataValues.hw_machine_model_category = category
    dataValues.hw_machine_model_family   = family
    self.applied_effect = True

  def revert(self, dataValues):
    pass

  def normalize(self, raw: str) -> tuple:
    """Returns (vendor, category, family)."""
    s = raw.strip() if raw and raw != "None" else ""
    if not s or self._JUNK.match(s):
      return ("None", "unknown", "None")

    # ── virtual machines ─────────────────────────────────────────────────
    if re.match(r'(?i)^VMware', s):
      return ("VMware", "vm", "VMware_VM")
    if re.search(r'(?i)\bvirtualbox\b|\bvbox\b', s):
      return ("VirtualBox", "vm", "VirtualBox_VM")
    if re.match(r'(?i)^(?:virtual\s+machine|qemu\b|Graviton\b)', s):
      return ("VM", "vm", "VM")
    if re.match(r'(?i)^Standard\s+PC\b', s):
      return ("VM", "vm", "VM_QEMU")
    if re.match(r'(?i)^(?:KVM|HVM)\b', s):
      return ("VM", "vm", "VM_KVM")
    if re.match(r'(?i)^OpenStack\b', s):
      return ("VM", "vm", "VM_OpenStack")
    if re.match(r'(?i)^Parallels', s):
      return ("VM", "vm", "VM_Parallels")
    if re.match(r'(?i)^(?:Alibaba|Aliyun)\b', s):
      return ("VM", "vm", "VM_Alibaba")
    if re.match(r'(?i)^Nutanix\b', s):
      return ("VM", "vm", "VM_Nutanix")
    if re.match(r'(?i)^SVGA3D\b', s):
      return ("VM", "vm", "VMware_VM")

    # ── Samsung ──────────────────────────────────────────────────────────
    if re.match(r'(?i)^samsung\s', s):
      return self._samsung(s)

    # ── HP (and HP sub-brands that omit the "HP" prefix) ────────────────
    if re.match(r'(?i)^HP\b', s) or re.match(r'(?i)^(?:Victus|OMEN|ProLiant|Blade\b.*(?:HP|ProLiant))\b', s):
      return self._hp(s)
    if re.match(r'(?i)^ProLiant\b', s):
      return ("HP", "server", "HP_ProLiant")

    # ── Dell product lines (often appear without "Dell" prefix) ──────────
    if re.match(r'(?i)^(?:OptiPlex|Inspiron|Vostro|Latitude|Precision|XPS|Alienware|PowerEdge|Dell\b)', s):
      return self._dell(s)
    # Dell G-series gaming laptops (G3, G5, G7, G15, G16) without "Dell" prefix
    if re.match(r'^G(?:3|5|7|15|16)\b', s):
      return ("Dell", "laptop", "Dell_Gaming")

    # ── Google Pixel ─────────────────────────────────────────────────────
    if re.match(r'(?i)^Google\s+Pixel\b', s):
      return ("Google", "mobile", "Google_Pixel")

    # ── Apple ────────────────────────────────────────────────────────────
    # New unified Mac##,# identifiers (Apple Silicon Macs)
    mac_m = re.match(r'^(Mac\d+,\d+)$', s)
    if mac_m:
      lookup = self._APPLE_MAC_IDS.get(mac_m.group(1))
      if lookup:
        return ("Apple", lookup[0], lookup[1])
      return ("Apple", "unknown", "Apple_Mac")
    if re.match(r'(?i)^(?:MacBook|iMac|MacPro|MacMini|Macmini)', s):
      return self._apple(s)

    # ── Xiaomi / Redmi / POCO ────────────────────────────────────────────
    if re.match(r'(?i)^Xiaomi\b', s):
      return self._xiaomi(s)
    if re.match(r'(?i)^Redmi\b', s):
      return ("Xiaomi", "mobile", "Xiaomi_Redmi")
    if re.match(r'(?i)^POCO\b', s):
      return ("Xiaomi", "mobile", "Xiaomi_Poco")

    # ── Motorola ─────────────────────────────────────────────────────────
    if re.match(r'(?i)^motorola\b', s):
      return self._motorola(s)

    # ── OPPO ─────────────────────────────────────────────────────────────
    if re.match(r'(?i)^OPPO\b', s):
      return ("OPPO", "mobile", "OPPO")

    # ── OnePlus ──────────────────────────────────────────────────────────
    if re.match(r'(?i)^OnePlus\b', s):
      return ("OnePlus", "mobile", "OnePlus")

    # ── vivo ─────────────────────────────────────────────────────────────
    if re.match(r'(?i)^vivo\b', s):
      return ("Vivo", "mobile", "Vivo")

    # ── realme ───────────────────────────────────────────────────────────
    if re.match(r'(?i)^realme\b', s):
      return ("Realme", "mobile", "Realme")

    # ── HUAWEI ───────────────────────────────────────────────────────────
    if re.match(r'(?i)^HUAWEI\b', s):
      return ("Huawei", "mobile", "Huawei")

    # ── HONOR ────────────────────────────────────────────────────────────
    if re.match(r'(?i)^HONOR\b', s):
      return ("Honor", "mobile", "Honor")

    # ── Sony Xperia ──────────────────────────────────────────────────────
    if re.match(r'(?i)^Sony\b', s):
      return ("Sony", "mobile", "Sony_Xperia")

    # ── LG ───────────────────────────────────────────────────────────────
    if re.match(r'(?i)^LGE?\b', s):
      return ("LG", "mobile", "LG")

    # ── ASUS ─────────────────────────────────────────────────────────────
    if re.match(r'(?i)^(?:ASUS|asus)\s', s) or re.match(r'(?i)^(?:VivoBook|ZenBook|ROG\b|TUF\b|PRIME\b)', s):
      return self._asus(s)
    # ASUS laptop model numbers (X###XX pattern, e.g. X441UA, X555LA)
    if re.match(r'^X[0-9]{3}[A-Z]{1,3}$', s):
      return ("ASUS", "laptop", "ASUS_VivoBook")

    # ── Acer ─────────────────────────────────────────────────────────────
    if re.match(r'(?i)^(?:Aspire|TravelMate|Veriton|Swift|Nitro|Extensa|Predator|Spin|ConceptD)\b', s):
      return self._acer(s)

    # ── Lenovo (named) ───────────────────────────────────────────────────
    if re.match(r'(?i)^(?:LENOVO|Lenovo)\b', s):
      return self._lenovo(s)
    if re.match(r'(?i)^(?:ThinkPad|IdeaPad|IdeaCentre|ThinkCentre|ThinkStation|ThinkBook|ThinkSystem|Legion|Yoga)\b', s):
      return self._lenovo(s)

    # ── Lenovo numeric product codes ─────────────────────────────────────
    # ThinkPad: 20**, 21**  /  ThinkCentre M: 10[A-Z]**  /  ThinkStation: 30**
    # IdeaPad:  80**–84**   /  IdeaCentre:   90**
    # No \b: these codes are standalone continuous alphanumeric strings
    if re.match(r'^(?:2[01][A-Z0-9]{2}|10[A-Z][A-Z0-9]|30[A-Z][A-Z0-9]{2}|8[0-4][A-Z0-9]{2}|90[A-Z][A-Z0-9])', s):
      return self._lenovo_code(s)

    # ── Lenovo C-series workstations (C4400, C6200, etc.) ────────────────
    if re.match(r'^C\d{4}\b', s):
      return ("Lenovo", "desktop", "Lenovo_ThinkStation")

    # ── Lenovo full product codes (LENOVO_MT_xxxx_BU_*_FM_*) ──────────
    lm = re.match(r'^LENOVO_MT_\w+_(?:BU_\w+_)?FM_(\w+)', s)
    if lm:
      brand = lm.group(1)
      if brand in ('ThinkPad', 'ThinkBook'):    return ("Lenovo", "laptop",  f"Lenovo_{brand}")
      if brand in ('IdeaPad',):                 return ("Lenovo", "laptop",  "Lenovo_IdeaPad")
      if brand in ('Legion', 'LOQ'):            return ("Lenovo", "laptop",  "Lenovo_Legion")
      if brand in ('Yoga',):                    return ("Lenovo", "laptop",  "Lenovo_Yoga")
      if brand in ('ThinkCentre',):             return ("Lenovo", "desktop", "Lenovo_ThinkCentre")
      if brand in ('ThinkStation',):            return ("Lenovo", "desktop", "Lenovo_ThinkStation")
      if brand in ('IdeaCentre',):              return ("Lenovo", "desktop", "Lenovo_IdeaCentre")
      return ("Lenovo", "unknown", "Lenovo")
    if re.match(r'^LENOVO_MT_', s):
      return ("Lenovo", "unknown", "Lenovo")

    # ── MSI ──────────────────────────────────────────────────────────────
    if re.match(r'^MS-[A-Z0-9]{4}', s):
      return ("MSI", "desktop", "MSI_Desktop")
    # MSI laptop lines
    if re.match(r'(?i)^(?:GF|GL|GS\d|GP|GE|GV|Modern\b|Creator\b|Stealth\b|Prestige\b)', s):
      return ("MSI", "laptop", "MSI_Laptop")
    if re.match(r'(?i)^(?:Katana|Cyborg|Thin\b|Raider|Sword|Bravo|GamingPC|Crosshair|Vector|Pulse)\b', s):
      return ("MSI", "laptop", "MSI_Laptop")
    if re.match(r'(?i)^(?:MAG\b|MPG\b|MEG\b|MS-Challenger|MS-TZZ)', s):
      return ("MSI", "desktop", "MSI_Desktop")

    # ── Gigabyte / chipset-branded boards ────────────────────────────────
    if re.match(r'(?i)^GA-', s):
      return ("Gigabyte", "desktop", "Gigabyte_Desktop")
    if re.match(r'(?i)^(?:AORUS|GIGABYTE)\b', s):
      return ("Gigabyte", "desktop", "Gigabyte_Desktop")
    # Chipset-prefix boards: H/B/Z/X/A series Intel/AMD motherboards
    if re.match(r'(?i)^(?:H\d{2,3}[A-Z]|B\d{3}[A-Z]?|Z\d{3}[A-Z]?|X\d{3}[A-Z]?|A[35]\d{2}[A-Z])', s):
      return self._gigabyte_or_mobo(s)
    # Bare chipset names (no suffix letter) — e.g. "H81", "H110", "H61", "B85", "X99"
    if re.match(r'^(?:H\d{2,3}|B\d{2,3}|Z\d{2,3}|X\d{2,3}|A\d{3}M?)$', s):
      return ("Desktop", "desktop", "Desktop_Motherboard")
    # Chipset + brand suffix: "AB350-Gaming 3", "B85M-D3H", "Z97X-Gaming 5"
    if re.match(r'^(?:AB?\d{3}|Z\d{2,3}X?|X\d{2,3})-', s):
      return ("Gigabyte", "desktop", "Gigabyte_Desktop")

    # ── Fujitsu ──────────────────────────────────────────────────────────
    if re.match(r'(?i)^(?:ESPRIMO|LIFEBOOK|CELSIUS|STYLISTIC|PRIMERGY|FMVU?[A-Z0-9])', s):
      return self._fujitsu(s)

    # ── Dynabook (formerly Toshiba consumer) ─────────────────────────────
    if re.match(r'(?i)^dynabook\b', s):
      return ("Dynabook", "laptop", "Dynabook")

    # ── Toshiba ──────────────────────────────────────────────────────────
    if re.match(r'(?i)^Satellite\b', s):
      return ("Toshiba", "laptop", "Toshiba_Satellite")
    if re.match(r'(?i)^(?:PORTEGE|TECRA|Qosmio)\b', s):
      return ("Toshiba", "laptop", "Toshiba_Business")

    # ── Microsoft Surface ────────────────────────────────────────────────
    if re.match(r'(?i)^Surface\b', s):
      return self._surface(s)

    # ── Nokia / HMD Global ───────────────────────────────────────────────
    if re.match(r'(?i)^HMD\b', s) or re.match(r'(?i)^Nokia\b', s):
      return ("Nokia", "mobile", "Nokia")

    # ── SHARP ────────────────────────────────────────────────────────────
    if re.match(r'(?i)^SHARP\b', s):
      return ("Sharp", "mobile", "Sharp")

    # ── TCL ──────────────────────────────────────────────────────────────
    if re.match(r'(?i)^TCL\b', s):
      return ("TCL", "mobile", "TCL")

    # ── INFINIX ──────────────────────────────────────────────────────────
    if re.match(r'(?i)^INFINIX\b', s):
      return ("Infinix", "mobile", "Infinix")

    # ── ITEL ─────────────────────────────────────────────────────────────
    if re.match(r'(?i)^ITEL\b', s):
      return ("Itel", "mobile", "Itel")

    # ── TECNO ────────────────────────────────────────────────────────────
    if re.match(r'(?i)^TECNO\b', s):
      return ("Tecno", "mobile", "Tecno")

    # ── ZTE ──────────────────────────────────────────────────────────────
    if re.match(r'(?i)^ZTE\b', s):
      return ("ZTE", "mobile", "ZTE")

    # ── Nubia (ZTE sub-brand) ────────────────────────────────────────────
    if re.match(r'(?i)^nubia\b', s):
      return ("ZTE", "mobile", "ZTE_Nubia")

    # ── Nothing ──────────────────────────────────────────────────────────
    if re.match(r'(?i)^Nothing\b', s):
      return ("Nothing", "mobile", "Nothing")

    # ── Fairphone ────────────────────────────────────────────────────────
    if re.match(r'(?i)^Fairphone\b', s):
      return ("Fairphone", "mobile", "Fairphone")

    # ── Blackview ────────────────────────────────────────────────────────
    if re.match(r'(?i)^Blackview\b', s):
      return ("Blackview", "mobile", "Blackview")

    # ── DOOGEE ───────────────────────────────────────────────────────────
    if re.match(r'(?i)^DOOGEE\b', s):
      return ("DOOGEE", "mobile", "DOOGEE")

    # ── Amazon Fire tablets ───────────────────────────────────────────────
    if re.match(r'(?i)^Amazon\b', s):
      return ("Amazon", "tablet", "Amazon_Fire")

    # ── Samsung Galaxy Book (laptop, e.g. 550XDA) ─────────────────────────
    if re.match(r'^\d{3}X[A-Z]{2,3}', s):
      return ("Samsung", "laptop", "Samsung_GalaxyBook")

    # ── Medion (Akoya brand, sold via Aldi) ──────────────────────────────
    if re.match(r'(?i)^(?:Medion|Akoya)\b', s):
      return ("Medion", "laptop", "Medion")

    # ── Ulefone / OUKITEL / CUBOT / Teclast (budget Android brands) ──────
    if re.match(r'(?i)^Ulefone\b', s): return ("Ulefone", "mobile", "Ulefone")
    if re.match(r'(?i)^OUKITEL\b',  s): return ("OUKITEL", "mobile", "OUKITEL")
    if re.match(r'(?i)^CUBOT\b',    s): return ("CUBOT",   "mobile", "CUBOT")
    if re.match(r'(?i)^Teclast\b',  s): return ("Teclast", "tablet", "Teclast")

    # ── FCNT (Arrows mobile phones, Japan) ───────────────────────────────
    if re.match(r'(?i)^FCNT\b', s):
      return ("FCNT", "mobile", "FCNT_Arrows")

    # ── NEC ──────────────────────────────────────────────────────────────
    if re.match(r'(?i)^NEC\b', s):
      return ("NEC", "unknown", "NEC")

    # ── KYOCERA ──────────────────────────────────────────────────────────
    if re.match(r'(?i)^KYOCERA\b', s):
      return ("Kyocera", "mobile", "Kyocera")

    # ── Positivo (Brazilian brand) ────────────────────────────────────────
    if re.match(r'(?i)^Positivo\b', s):
      return ("Positivo", "laptop", "Positivo")

    # ── Valve Steam Deck ─────────────────────────────────────────────────
    if s in ('Jupiter', 'Galileo'):
      return ("Valve", "handheld", "Valve_SteamDeck")

    # ── Intel NUC mini PCs ───────────────────────────────────────────────
    if re.match(r'(?i)^NUC', s):
      return ("Intel", "desktop", "Intel_NUC")

    # ── ASUS sub-brands not caught by main ASUS block ────────────────────
    if re.match(r'(?i)^ASUSPRO\b', s):
      return ("ASUS", "desktop", "ASUS_Pro")
    if re.match(r'(?i)^ASUS_MB_', s):
      return ("ASUS", "desktop", "ASUS_Desktop")
    if re.match(r'(?i)^(?:ProArt|Strix)\b', s):
      return ("ASUS", "desktop", "ASUS_Desktop")
    if re.match(r'(?i)^Zephyrus\b', s):
      return ("ASUS", "laptop", "ASUS_ROG")
    if re.match(r'(?i)^(?:K[0-9]{2,3}[A-Z]{1,3})\b', s):
      return ("ASUS", "laptop", "ASUS_Laptop")

    # ── Mini PCs (Beelink, MinisForum, etc.) ─────────────────────────────
    if re.match(r'(?i)^(?:SER|EQ|EliteMini|GTR|SEi|EQi)\d', s):
      return ("Beelink", "desktop", "Beelink_MiniPC")
    if re.match(r'(?i)^(?:NucBox|MiniPC|MINIPC)\b', s):
      return ("MiniPC", "desktop", "MiniPC")

    # ── Acer sub-brands without Acer prefix ──────────────────────────────
    if re.match(r'(?i)^EasyNote\b', s):
      return ("Acer", "laptop", "Acer_PackardBell")

    # ── Samsung laptop model codes ───────────────────────────────────────
    if re.match(r'^300E[0-9]', s):
      return ("Samsung", "laptop", "Samsung_Laptop")
    if re.match(r'^950[A-Z]', s):
      return ("Samsung", "laptop", "Samsung_GalaxyBook")

    # ── HP sub-brands without HP prefix ──────────────────────────────────
    if re.match(r'(?i)^Presario\b', s):
      return ("HP", "desktop", "HP_Compaq")
    if re.match(r'(?i)^Blade\b', s) and re.search(r'(?i)\bHP\b|ProLiant', s):
      return ("HP", "server", "HP_ProLiant")

    # ── Xiaomi sub-brands without Xiaomi prefix ──────────────────────────
    if re.match(r'(?i)^RedmiBook\b', s):
      return ("Xiaomi", "laptop", "Xiaomi_RedmiBook")
    if re.match(r'^Mi\s', s):
      return ("Xiaomi", "mobile", "Xiaomi_Mi")
    if re.match(r'(?i)^Galaxy\b', s):
      return ("Samsung", "mobile", "Samsung_Galaxy")

    # ── Additional mobile brands ─────────────────────────────────────────
    if re.match(r'(?i)^(?:BLU|Blu)\b', s):  return ("BLU",      "mobile", "BLU")
    if re.match(r'(?i)^(?:Cat|CAT)\b', s):  return ("Cat",      "mobile", "Cat")
    if re.match(r'(?i)^WIKO\b', s):         return ("WIKO",     "mobile", "WIKO")
    if re.match(r'(?i)^LAVA\b', s):         return ("LAVA",     "mobile", "LAVA")
    if re.match(r'(?i)^UMIDIGI\b', s):      return ("UMIDIGI",  "mobile", "UMIDIGI")
    if re.match(r'(?i)^Unihertz\b', s):     return ("Unihertz", "mobile", "Unihertz")
    if re.match(r'(?i)^OSCAL\b', s):        return ("Blackview","mobile", "Blackview")
    if re.match(r'(?i)^HOTWAV\b', s):       return ("HOTWAV",   "mobile", "HOTWAV")
    if re.match(r'(?i)^Doro\b', s):         return ("Doro",     "mobile", "Doro")
    if re.match(r'(?i)^HTC\b', s):          return ("HTC",      "mobile", "HTC")
    if re.match(r'(?i)^(?:AYN|AYANEO)\b', s): return ("AYANEO", "handheld", "AYANEO")
    if re.match(r'(?i)^Gigaset\b', s):      return ("Gigaset",  "mobile", "Gigaset")
    if re.match(r'(?i)^Crosscall\b', s):    return ("Crosscall","mobile", "Crosscall")
    if re.match(r'(?i)^Alldocube\b', s):    return ("Alldocube","tablet", "Alldocube")
    if re.match(r'(?i)^SHIFT\b', s):        return ("SHIFT",    "mobile", "SHIFT")
    if re.match(r'(?i)^Zebra\b', s):        return ("Zebra",    "mobile", "Zebra")
    if re.match(r'(?i)^Honeywell\b', s):    return ("Honeywell","mobile", "Honeywell")
    if re.match(r'(?i)^TINNO\b', s):        return ("TINNO",    "mobile", "TINNO")
    if re.match(r'(?i)^Wingtech\b', s):     return ("Wingtech", "mobile", "Wingtech")
    if re.match(r'(?i)^HYPE\b', s):         return ("HYPE",     "mobile", "HYPE")
    if re.match(r'(?i)^Luxshare\b', s):     return ("Luxshare", "mobile", "Luxshare")
    if re.match(r'(?i)^wheatek\b', s):      return ("Wheatek",  "mobile", "Wheatek")
    if re.match(r'(?i)^Hisilicon\b', s):    return ("Huawei",   "mobile", "Huawei")
    if re.match(r'(?i)^alps\b', s):         return ("Alps",     "mobile", "Alps")
    if re.match(r'(?i)^Coosea\b', s):       return ("Coosea",   "mobile", "Coosea")
    if re.match(r'(?i)^Droidlogic\b', s):   return ("Droidlogic","mobile","Droidlogic")
    if re.match(r'(?i)^onn\b', s):          return ("Walmart",  "tablet", "Walmart_Onn")

    # ── Desktop PCs / workstations ───────────────────────────────────────
    if re.match(r'(?i)^TERRA_PC\b', s):     return ("TERRA",   "desktop", "TERRA")
    if re.match(r'(?i)^(?:exone|bluechip|BUSINESSline)\b', s):
      return ("Desktop", "desktop", "Desktop_Custom")
    if re.match(r'(?i)^(?:CORSAIR|NZXT)\b', s):
      return ("Desktop", "desktop", "Desktop_Custom")
    if re.match(r'(?i)^Hyrican\b', s):      return ("Hyrican", "desktop", "Hyrican")
    if re.match(r'(?i)^KomplettPC\b', s):   return ("Komplett", "desktop", "Komplett")
    if re.match(r'(?i)^(?:FRONTIER|Endeavor)\b', s):
      return ("Epson", "desktop", "Epson")
    if re.match(r'(?i)^(?:NIRVANA|ABRA)\b', s):
      return ("Casper", "laptop", "Casper")
    if re.match(r'(?i)^Infoway\b', s):
      return ("Positivo", "laptop", "Positivo")
    if re.match(r'(?i)^(?:MyBook|Mybook|MEGABOOK)\b', s):
      return ("MSI", "laptop", "MSI_Laptop")
    if re.match(r'(?i)^(?:IPMH|IPM)\d', s):
      return ("Desktop", "desktop", "Desktop_Motherboard")
    if re.match(r'(?i)^S26361-K', s):
      return ("Fujitsu", "desktop", "Fujitsu_ESPRIMO")

    # ── Samsung laptop numeric codes ─────────────────────────────────────
    if re.match(r'^\d{3}[A-Z]\d[A-Z]', s) and not re.match(r'^\d{3}X', s):
      # Samsung laptop codes like "730QFG", "530U3C" — but not 550XDA (already caught)
      return ("Samsung", "laptop", "Samsung_Laptop")

    # ── Generic fallback ────────────────────────────────────────────────
    label = self._fallback_label(s)
    return (label, "unknown", label)

  _GENERIC_WORDS = frozenset({
    'desktop', 'laptop', 'computer', 'pc', 'work', 'home', 'mypc', 'custom',
    'standard', 'business', 'default', 'empty', 'super', 'pro', 'one', 'all',
    'us', 'by', 'not', 'none', 'unknown', 'invalid', 'mini', 'aio',
  })

  @classmethod
  def _fallback_label(cls, raw: str) -> str:
    """Return 'Unknown' for garbage/generic, 'Other' for real but unrecognized."""
    first = raw.split()[0] if raw.split() else raw
    low = first.lower()
    if low in cls._GENERIC_WORDS:
      return 'Unknown'
    if len(first) <= 3:
      return 'Unknown'
    if first.isdigit():
      return 'Unknown'
    # Hex-like codes (0BE0, 00A1, etc.)
    if re.match(r'^[0-9][0-9A-Fa-f]*$', first):
      return 'Unknown'
    # All-lowercase (user-typed names like "incar", "empty")
    if first.islower():
      return 'Unknown'
    return 'Other'

  # ── Samsung ──────────────────────────────────────────────────────────────

  def _samsung(self, s: str) -> tuple:
    m = re.match(r'(?i)^samsung\s+SM-([A-Z])(\d+)', s)
    if m:
      series = m.group(1).upper()
      _SERIES = {
        'S': ('mobile', 'Samsung_GalaxyS'),
        'A': ('mobile', 'Samsung_GalaxyA'),
        'M': ('mobile', 'Samsung_GalaxyM'),
        'F': ('mobile', 'Samsung_GalaxyZ'),
        'G': ('mobile', 'Samsung_GalaxyS'),   # older Galaxy S series
        'N': ('mobile', 'Samsung_GalaxyNote'),
        'T': ('tablet', 'Samsung_GalaxyTab'),
        'X': ('tablet', 'Samsung_GalaxyTab'),
        'P': ('tablet', 'Samsung_GalaxyTab'),
        'E': ('mobile', 'Samsung_GalaxyE'),
      }
      cat, fam = _SERIES.get(series, ('mobile', 'Samsung_Galaxy'))
      return ("Samsung", cat, fam)
    # Japanese carrier variants (SCG, SC-)
    if re.search(r'(?i)\bSC[G-]\d', s):
      return ("Samsung", "mobile", "Samsung_Galaxy")
    return ("Samsung", "mobile", "Samsung_Galaxy")

  # ── HP ───────────────────────────────────────────────────────────────────

  _HP_FAMILIES = [
    (r'EliteBook\b',              'laptop',  'HP_EliteBook'),
    (r'ProBook\b',                'laptop',  'HP_ProBook'),
    (r'ZBook\b',                  'laptop',  'HP_ZBook'),
    (r'Spectre\b',                'laptop',  'HP_Spectre'),
    (r'Envy\b',                   'laptop',  'HP_Envy'),
    (r'OMEN\b',                   'laptop',  'HP_OMEN'),
    (r'Victus\b',                 'laptop',  'HP_Victus'),
    (r'Pavilion\s+(?:Notebook|Laptop)', 'laptop',  'HP_Pavilion'),
    (r'Pavilion\b',               'desktop', 'HP_Pavilion'),
    (r'EliteDesk\b',              'desktop', 'HP_EliteDesk'),
    (r'ProDesk\b',                'desktop', 'HP_ProDesk'),
    (r'Pro\s+Tower\b',            'desktop', 'HP_ProTower'),
    (r'Pro\s+(?:Mini|SFF|MT)\b',  'desktop', 'HP_ProDesktop'),
    (r'Slim\s+Desktop\b',         'desktop', 'HP_SlimDesktop'),
    (r'ProOne\b',                 'desktop', 'HP_ProOne'),
    (r'ProLiant\b',               'server',  'HP_ProLiant'),
    (r'Compaq\b',                 'desktop', 'HP_Compaq'),
    (r'Z[0-9]\b',                 'desktop', 'HP_ZWorkstation'),
    (r'Z\d{3}\b',                 'desktop', 'HP_ZWorkstation'),
    (r'All-in-One\b',             'desktop', 'HP_AllInOne'),
    (r'\bt[46]\d{2}\b',           'desktop', 'HP_ThinClient'),
    (r'Thin\s+Client\b',          'desktop', 'HP_ThinClient'),
    (r'Stream\b',                 'laptop',  'HP_Stream'),
    (r'Laptop\b',                 'laptop',  'HP_Laptop'),
    (r'Notebook\b',               'laptop',  'HP_Notebook'),
    (r'(?:Microtower|SFF|CMT|TWR|Mini\s+Tower)\b', 'desktop', 'HP_Desktop'),
  ]

  def _hp(self, s: str) -> tuple:
    for pattern, cat, fam in self._HP_FAMILIES:
      if re.search(pattern, s, re.IGNORECASE):
        return ("HP", cat, fam)
    # HP NNN [G\d] → numeric-model desktops (HP 280, HP 290) vs laptops (HP 15)
    m = re.search(r'(?i)\bHP\s+(\d{2,3})\b', s)
    if m:
      num = int(m.group(1))
      return ("HP", "desktop" if num >= 200 else "laptop", f"HP_{m.group(1)}")
    return ("HP", "unknown", "HP")

  # ── Dell ─────────────────────────────────────────────────────────────────

  def _dell(self, s: str) -> tuple:
    if re.match(r'(?i)^OptiPlex\b', s):  return ("Dell", "desktop", "Dell_OptiPlex")
    if re.match(r'(?i)^Vostro\b',   s):  return ("Dell", "desktop", "Dell_Vostro")
    if re.match(r'(?i)^Inspiron\b', s):  return ("Dell", "laptop",  "Dell_Inspiron")
    if re.match(r'(?i)^Latitude\b', s):  return ("Dell", "laptop",  "Dell_Latitude")
    if re.match(r'(?i)^Precision\b', s): return ("Dell", "laptop",  "Dell_Precision")
    if re.match(r'(?i)^XPS\b',      s):  return ("Dell", "laptop",  "Dell_XPS")
    if re.match(r'(?i)^Alienware\b', s): return ("Dell", "laptop",  "Dell_Alienware")
    if re.match(r'(?i)^PowerEdge\b', s): return ("Dell", "server",  "Dell_PowerEdge")
    if re.match(r'(?i)^Dell\s+G\d', s):  return ("Dell", "laptop",  "Dell_Gaming")
    if re.match(r'(?i)^Dell\s+Pro\b', s): return ("Dell", "laptop", "Dell_Pro")
    if re.match(r'(?i)^Dell\s+(?:Tower|Slim)\b', s): return ("Dell", "desktop", "Dell_Desktop")
    if re.match(r'(?i)^Dell\s+\d', s):   return ("Dell", "laptop",  "Dell_Laptop")
    if re.match(r'(?i)^ChengMing\b', s):  return ("Dell", "desktop", "Dell_ChengMing")
    if re.match(r'(?i)^Wyse\b', s):       return ("Dell", "desktop", "Dell_Wyse")
    return ("Dell", "unknown", "Dell")

  # ── Apple ────────────────────────────────────────────────────────────────

  def _apple(self, s: str) -> tuple:
    # Use prefix match only — no \b, since identifiers like "MacBookPro16,1" have no word break
    if re.match(r'(?i)^MacBookPro', s): return ("Apple", "laptop",  "Apple_MacBookPro")
    if re.match(r'(?i)^MacBookAir', s): return ("Apple", "laptop",  "Apple_MacBookAir")
    if re.match(r'(?i)^MacBook',    s): return ("Apple", "laptop",  "Apple_MacBook")
    if re.match(r'(?i)^iMac',       s): return ("Apple", "desktop", "Apple_iMac")
    if re.match(r'(?i)^MacPro',     s): return ("Apple", "desktop", "Apple_MacPro")
    if re.match(r'(?i)^(?:Macmini|MacMini)', s): return ("Apple", "desktop", "Apple_MacMini")
    # Mac14,2 / Mac16,1 style — modern hardware identifier (any form factor)
    return ("Apple", "unknown", "Apple_Mac")

  # ── Xiaomi ───────────────────────────────────────────────────────────────

  def _xiaomi(self, s: str) -> tuple:
    if re.search(r'(?i)\bRedmi\b', s):  return ("Xiaomi", "mobile", "Xiaomi_Redmi")
    if re.search(r'(?i)\bPOCO\b',  s):  return ("Xiaomi", "mobile", "Xiaomi_Poco")
    # "Xiaomi Mi Note" etc. but not raw numeric codes like "Xiaomi 23117RA68G"
    if re.search(r'(?i)\bMi\b', s) and not re.search(r'\bMi\d{5}', s):
      return ("Xiaomi", "mobile", "Xiaomi_Mi")
    return ("Xiaomi", "mobile", "Xiaomi")

  # ── Motorola ─────────────────────────────────────────────────────────────

  def _motorola(self, s: str) -> tuple:
    sl = s.lower()
    if 'moto g' in sl: return ("Motorola", "mobile", "Motorola_MotoG")
    if 'moto e' in sl: return ("Motorola", "mobile", "Motorola_MotoE")
    if 'razr'   in sl: return ("Motorola", "mobile", "Motorola_Razr")
    if 'edge'   in sl: return ("Motorola", "mobile", "Motorola_Edge")
    return ("Motorola", "mobile", "Motorola")

  # ── ASUS ─────────────────────────────────────────────────────────────────

  def _asus(self, s: str) -> tuple:
    if re.search(r'(?i)VivoBook',     s): return ("ASUS", "laptop",  "ASUS_VivoBook")
    if re.search(r'(?i)ZenBook',      s): return ("ASUS", "laptop",  "ASUS_ZenBook")
    if re.search(r'(?i)\bROG\b',      s): return ("ASUS", "laptop",  "ASUS_ROG")
    if re.search(r'(?i)\bTUF\b',      s): return ("ASUS", "laptop",  "ASUS_TUF")
    if re.search(r'(?i)ExpertBook\b', s): return ("ASUS", "laptop",  "ASUS_ExpertBook")
    if re.search(r'(?i)\bPRIME\b',    s): return ("ASUS", "desktop", "ASUS_PRIME")
    if re.search(r'(?i)ZenFone\b|ROG.Phone\b', s): return ("ASUS", "mobile", "ASUS_ZenFone")
    return ("ASUS", "laptop", "ASUS")

  # ── Acer ─────────────────────────────────────────────────────────────────

  def _acer(self, s: str) -> tuple:
    if re.match(r'(?i)^Aspire\b',     s): return ("Acer", "laptop",  "Acer_Aspire")
    if re.match(r'(?i)^TravelMate\b', s): return ("Acer", "laptop",  "Acer_TravelMate")
    if re.match(r'(?i)^Veriton\b',    s): return ("Acer", "desktop", "Acer_Veriton")
    if re.match(r'(?i)^Swift\b',      s): return ("Acer", "laptop",  "Acer_Swift")
    if re.match(r'(?i)^Nitro\b',      s): return ("Acer", "laptop",  "Acer_Nitro")
    if re.match(r'(?i)^Extensa\b',    s): return ("Acer", "laptop",  "Acer_Extensa")
    if re.match(r'(?i)^Predator\b',   s): return ("Acer", "laptop",  "Acer_Predator")
    if re.match(r'(?i)^Spin\b',       s): return ("Acer", "laptop",  "Acer_Spin")
    return ("Acer", "unknown", "Acer")

  # ── Lenovo ───────────────────────────────────────────────────────────────

  def _lenovo(self, s: str) -> tuple:
    # Strip brand prefix (may appear twice: "LENOVO Lenovo TB-...") before matching product line
    s2 = re.sub(r'(?i)^(?:LENOVO|Lenovo)\s+', '', s).strip()
    s2 = re.sub(r'(?i)^(?:LENOVO|Lenovo)\s+', '', s2).strip() or s
    if re.match(r'(?i)^ThinkPad\b',     s2): return ("Lenovo", "laptop",  "Lenovo_ThinkPad")
    if re.match(r'(?i)^IdeaPad\b',      s2): return ("Lenovo", "laptop",  "Lenovo_IdeaPad")
    if re.match(r'(?i)^ThinkBook\b',    s2): return ("Lenovo", "laptop",  "Lenovo_ThinkBook")
    if re.match(r'(?i)^Legion\b',       s2): return ("Lenovo", "laptop",  "Lenovo_Legion")
    if re.match(r'(?i)^Yoga\b',         s2): return ("Lenovo", "laptop",  "Lenovo_Yoga")
    if re.match(r'(?i)^ThinkCentre\b',  s2): return ("Lenovo", "desktop", "Lenovo_ThinkCentre")
    if re.match(r'(?i)^ThinkStation\b', s2): return ("Lenovo", "desktop", "Lenovo_ThinkStation")
    if re.match(r'(?i)^IdeaCentre\b',   s2): return ("Lenovo", "desktop", "Lenovo_IdeaCentre")
    if re.match(r'(?i)^(?:TB|Tab)\b',     s2): return ("Lenovo", "tablet",  "Lenovo_Tab")
    if re.match(r'^TB\d',                 s2): return ("Lenovo", "tablet",  "Lenovo_Tab")
    if re.match(r'(?i)^ThinkSystem\b',    s2): return ("Lenovo", "server",  "Lenovo_ThinkSystem")
    return ("Lenovo", "unknown", "Lenovo")

  def _lenovo_code(self, s: str) -> tuple:
    """Classify Lenovo numeric product codes."""
    if re.match(r'^2[01][A-Z0-9]{2}', s): return ("Lenovo", "laptop",  "Lenovo_ThinkPad")
    if re.match(r'^30[A-Z][A-Z0-9]',  s): return ("Lenovo", "desktop", "Lenovo_ThinkStation")
    if re.match(r'^10[A-Z][A-Z0-9]',  s): return ("Lenovo", "desktop", "Lenovo_ThinkCentre")
    if re.match(r'^8[0-4][A-Z0-9]{2}',s): return ("Lenovo", "laptop",  "Lenovo_IdeaPad")
    if re.match(r'^90[A-Z][A-Z0-9]',  s): return ("Lenovo", "desktop", "Lenovo_IdeaCentre")
    return ("Lenovo", "unknown", "Lenovo")

  # ── Gigabyte / chipset-branded desktop boards ─────────────────────────────

  def _gigabyte_or_mobo(self, s: str) -> tuple:
    if re.search(r'(?i)\bAORUS\b', s):        return ("Gigabyte", "desktop", "Gigabyte_AORUS")
    if re.search(r'(?i)\bDS[23]H?\b', s):     return ("Gigabyte", "desktop", "Gigabyte_Desktop")
    # Pro RS / Pro4 / HDV are ASRock suffixes
    if re.search(r'(?i)\bPro\s*(?:RS|4|4D)\b|\bHDV\b', s): return ("ASRock", "desktop", "ASRock_Desktop")
    return ("Gigabyte", "desktop", "Gigabyte_Desktop")

  # ── Fujitsu ──────────────────────────────────────────────────────────────

  def _fujitsu(self, s: str) -> tuple:
    if re.match(r'(?i)^ESPRIMO\b',  s): return ("Fujitsu", "desktop", "Fujitsu_ESPRIMO")
    if re.match(r'(?i)^LIFEBOOK\b', s): return ("Fujitsu", "laptop",  "Fujitsu_LIFEBOOK")
    if re.match(r'(?i)^CELSIUS\b',  s): return ("Fujitsu", "desktop", "Fujitsu_CELSIUS")
    if re.match(r'(?i)^PRIMERGY\b', s): return ("Fujitsu", "server",  "Fujitsu_PRIMERGY")
    return ("Fujitsu", "laptop", "Fujitsu_FMV")  # FMV* prefix → FMV laptop

  # ── Microsoft Surface ─────────────────────────────────────────────────────

  def _surface(self, s: str) -> tuple:
    if re.search(r'(?i)Surface\s+Laptop\b', s):  return ("Microsoft", "laptop",  "Microsoft_SurfaceLaptop")
    if re.search(r'(?i)Surface\s+Book\b',   s):  return ("Microsoft", "laptop",  "Microsoft_SurfaceBook")
    if re.search(r'(?i)Surface\s+Studio\b', s):  return ("Microsoft", "desktop", "Microsoft_SurfaceStudio")
    if re.search(r'(?i)Surface\s+Go\b',     s):  return ("Microsoft", "tablet",  "Microsoft_SurfaceGo")
    return ("Microsoft", "tablet", "Microsoft_SurfacePro")  # Surface Pro = 2-in-1


class humanReadableValuesFilter(Filter):
  converted_metrics = [
        "hw_any_pointer_type", "hw_pointer_type",
        "screen_color_scheme",
        # "screen_color_gamut", Removed
        "screen_prefers_reduced_motion", "screen_prefers_reduced_transparency", "screen_prefers_contrast",
        "screen_inverted_colors",
        "screen_size_mode",
        "screen_primary_orientation",
        "prefs_cookiebehavior"]

  def __init__(self, dataValues):
    self.originals = {}

    for m in self.converted_metrics:
      self.originals[m] = getattr(dataValues, m)
      setattr(dataValues, m, self.annotated_value_conversion(m, getattr(dataValues, m)))

    self.applied_effect = True

  def revert(self, dataValues):
    for m in self.converted_metrics:
      setattr(dataValues, m, self.originals[m])

  def annotated_value_conversion(self, metric, value):
    val = value # I fucked up and this saves me from rewriting a bunch of code

    if metric in ["hw_any_pointer_type", "hw_pointer_type"]:
      if value == 1:
        return "Coarse Pointer"
      elif value == 2:
        return "Fine Pointer"
      elif value == 3:
        return "Coarse & Fine Pointer"
      elif value == 4:
        return "Hover Pointer"
      elif value == 5:
        return "Coarse & Hover Pointer"
      elif value == 6:
        return "Fine & Hover Pointer"
      elif value == 7:
        return "Coarse, Fine, & Hover Pointer"
    elif metric == "screen_color_scheme":
      if value == 0:
        return "Light"
      elif value == 1:
        return "Dark"
    elif metric == "screen_color_gamut":
      if value == 0:
        return "srgb"
      elif value == 1:
        return "p3"
      elif value == 2:
        return "rec2020"
    elif metric in ["screen_prefers_reduced_motion", "screen_prefers_reduced_transparency", "screen_inverted_colors"]:
      if value == 0:
        return "No Preference"
      elif value == 1:
        return "Prefers"
    elif metric == "screen_primary_orientation":
      ret = ""
      if val == 0:
        return "None"
      if val & 1:
        ret += "Portrait Primary, "
      if val & 2:
        ret += "Portrait Secondary, "
      if val & 4:
        ret += "Landscape Primary, "
      if val & 8:
        ret += "Landscape Secondary, "
      if val & 16:
        ret += "Default"
      return ret
    elif metric == "screen_prefers_contrast":
      if val == 0:
        return "More"
      elif val == 1:
        return "Less"
      elif val == 2:
        return "Custom"
      elif val == 3:
        return "No Preference"
    elif metric == "prefs_cookiebehavior":
      if val == 0:
        return "Allow All"
      elif val == 1:
        return "Reject all 3rd Party"
      elif val == 2:
        return "Reject All"
      elif val == 3:
        return "Limit Foreign"
      elif val == 4:
        return "Reject Tracker"
      elif val == 5:
        return "Reject Tracker & Partition Foreign"
    elif metric == "screen_size_mode":
      if val == 0:
        return "Normal"
      elif val == 1:
        return "Minimized"
      elif val == 2:
        return "Maximized"
      elif val == 3:
        return "Fullscreen"
      elif val == 4:
        return "Invalid"
    return value


class webGLParamFilter(Filter):
  def __init__(self, dataValues):
    self.originals = {}
    if "webgl_params_MAX_VIEWPORT_DIMS" in dir(dataValues):
      self.originals["webgl_params_MAX_VIEWPORT_DIMS"] = dataValues.webgl_params_MAX_VIEWPORT_DIMS
      s = dataValues.webgl_params_MAX_VIEWPORT_DIMS
      s = s.replace("[", "").replace("]", "")
      if s:
        s = s.split(",")
        dataValues.webgl_params_MAX_VIEWPORT_DIMS = s[0].strip()
      else:
        dataValues.webgl_params_MAX_VIEWPORT_DIMS = ""

    if "webgl_params_ALIASED_POINT_SIZE_RANGE" in dir(dataValues):
      s = dataValues.webgl_params_ALIASED_POINT_SIZE_RANGE
      s = s.replace("[", "").replace("]", "")
      if s:
        s = s.split(",")
        dataValues.webgl_params_ALIASED_POINT_SIZE_RANGE_MIN = s[0].strip()
        dataValues.webgl_params_ALIASED_POINT_SIZE_RANGE_MAX = s[1].strip()
      else:
        dataValues.webgl_params_ALIASED_POINT_SIZE_RANGE_MIN = ""
        dataValues.webgl_params_ALIASED_POINT_SIZE_RANGE_MAX = ""

    if "webgl_params_ALIASED_LINE_WIDTH_RANGE" in dir(dataValues):
      s = dataValues.webgl_params_ALIASED_LINE_WIDTH_RANGE
      s = s.replace("[", "").replace("]", "")
      if s:
        s = s.split(",")
        dataValues.webgl_params_ALIASED_LINE_WIDTH_RANGE_MIN = s[0].strip()
        dataValues.webgl_params_ALIASED_LINE_WIDTH_RANGE_MAX = s[1].strip()
      else:
        dataValues.webgl_params_ALIASED_LINE_WIDTH_RANGE_MIN = ""
        dataValues.webgl_params_ALIASED_LINE_WIDTH_RANGE_MAX = ""

    self.applied_effect = True

  def revert(self, dataValues):
    if "webgl_params_MAX_VIEWPORT_DIMS" in self.originals:
      dataValues.webgl_params_MAX_VIEWPORT_DIMS = self.originals["webgl_params_MAX_VIEWPORT_DIMS"]


class webGLParamMetricFilter(Filter):
  def __init__(self, dataValues):
    self.originals = {}

    # Version-aware parsing: WEBGL_PARAM_METRICS changed across Firefox versions.
    # Use the actual array length to determine which version the data came from.
    v1_len = len(dataValues.webgl_params_json) if dataValues.webgl_params_json else 0
    param_list_v1 = _webgl_param_list_for_length(v1_len)
    # Set defaults for all canonical params first
    for param in WEBGL_PARAM_METRICS:
      setattr(dataValues, "webgl_params_" + param, "")
      setattr(dataValues, "webgl_params_" + param + "_software", "")
    # Populate from actual data using the version-appropriate param list
    for i, param in enumerate(param_list_v1):
      if dataValues.webgl_params_json and i < v1_len:
        setattr(dataValues, "webgl_params_" + param, str(dataValues.webgl_params_json[i]))
      slen = len(dataValues.webgl_params_json_software) if dataValues.webgl_params_json_software else 0
      if dataValues.webgl_params_json_software and i < slen:
        setattr(dataValues, "webgl_params_" + param + "_software", str(dataValues.webgl_params_json_software[i]))

    v2_len = len(dataValues.webgl2_params_json) if dataValues.webgl2_params_json else 0
    # The GL2 array is [shared_params...] + [gl2_only_params...].
    # Subtract the GL2-only count to get the shared prefix length,
    # then use that to pick the right version of the shared param list.
    shared_prefix_len = max(0, v2_len - len(WEBGL2_PARAM_METRICS))
    param_list_v2 = _webgl_param_list_for_length(shared_prefix_len) + WEBGL2_PARAM_METRICS
    # Set defaults for all canonical params first
    for param in WEBGL_PARAM_METRICS + WEBGL2_PARAM_METRICS:
      setattr(dataValues, "webgl2_params_" + param, "")
      setattr(dataValues, "webgl2_params_" + param + "_software", "")
    # Populate from actual data
    for i, param in enumerate(param_list_v2):
      if dataValues.webgl2_params_json and i < v2_len:
        setattr(dataValues, "webgl2_params_" + param, str(dataValues.webgl2_params_json[i]))
      slen = len(dataValues.webgl2_params_json_software) if dataValues.webgl2_params_json_software else 0
      if dataValues.webgl2_params_json_software and i < slen:
        setattr(dataValues, "webgl2_params_" + param + "_software", str(dataValues.webgl2_params_json_software[i]))

    self.applied_effect = True

  def revert(self, dataValues):
    pass


class webGLExtensionMetricsFilter(Filter):
  def __init__(self, dataValues):
    self.originals = {}

    webgl_extensions = set(dataValues.webgl_extensions.split()) if dataValues.webgl_extensions else set()
    log_unknown_extensions(webgl_extensions - KNOWN_WEBGL_EXTENSIONS, "webgl_extensions")
    webgl_extensions_software = set(dataValues.webgl_extensions_software.split()) if dataValues.webgl_extensions_software else set()
    log_unknown_extensions(webgl_extensions_software - KNOWN_WEBGL_EXTENSIONS, "webgl_extensions_software")
    webgl2_extensions = set(dataValues.webgl2_extensions.split()) if dataValues.webgl2_extensions else set()
    log_unknown_extensions(webgl2_extensions - KNOWN_WEBGL_EXTENSIONS, "webgl2_extensions")
    webgl2_extensions_software = set(dataValues.webgl2_extensions_software.split()) if dataValues.webgl2_extensions_software else set()
    log_unknown_extensions(webgl2_extensions_software - KNOWN_WEBGL_EXTENSIONS, "webgl2_extensions_software")
    for ext in KNOWN_WEBGL_EXTENSIONS:
      if ext in webgl_extensions:
        setattr(dataValues, "webgl_extensions_" + ext, "1")
      else:
        setattr(dataValues, "webgl_extensions_" + ext, "0")
      if ext in webgl_extensions_software:
        setattr(dataValues, "webgl_extensions_software_" + ext, "1")
      else:
        setattr(dataValues, "webgl_extensions_software_" + ext, "0")

      if ext in webgl2_extensions:
        setattr(dataValues, "webgl2_extensions_" + ext, "1")
      else:
        setattr(dataValues, "webgl2_extensions_" + ext, "0")
      if ext in webgl2_extensions_software:
        setattr(dataValues, "webgl2_extensions_software_" + ext, "1")
      else:
        setattr(dataValues, "webgl2_extensions_software_" + ext, "0")

    webgl_extensions_raw = set(dataValues.webgl_extensions_raw.split()) if dataValues.webgl_extensions_raw else set()
    log_unknown_extensions(webgl_extensions_raw - KNOWN_WEBGL_EXTENSIONS_RAW, "webgl_extensions_raw")
    webgl_extensions_raw_software = set(dataValues.webgl_extensions_raw_software.split()) if dataValues.webgl_extensions_raw_software else set()
    log_unknown_extensions(webgl_extensions_raw_software - KNOWN_WEBGL_EXTENSIONS_RAW, "webgl_extensions_raw_software")
    webgl2_extensions_raw = set(dataValues.webgl2_extensions_raw.split()) if dataValues.webgl2_extensions_raw else set()
    log_unknown_extensions(webgl2_extensions_raw - KNOWN_WEBGL_EXTENSIONS_RAW, "webgl2_extensions_raw")
    webgl2_extensions_raw_software = set(dataValues.webgl2_extensions_raw_software.split()) if dataValues.webgl2_extensions_raw_software else set()
    log_unknown_extensions(webgl2_extensions_raw_software - KNOWN_WEBGL_EXTENSIONS_RAW, "webgl2_extensions_raw_software")
    for ext in KNOWN_WEBGL_EXTENSIONS_RAW:
      if ext in webgl_extensions_raw:
        setattr(dataValues, "webgl_extensions_raw_" + ext, "1")
      else:
        setattr(dataValues, "webgl_extensions_raw_" + ext, "0")
      if ext in webgl_extensions_raw_software:
        setattr(dataValues, "webgl_extensions_raw_software_" + ext, "1")
      else:
        setattr(dataValues, "webgl_extensions_raw_software_" + ext, "0")

      if ext in webgl2_extensions_raw:
        setattr(dataValues, "webgl2_extensions_raw_" + ext, "1")
      else:
        setattr(dataValues, "webgl2_extensions_raw_" + ext, "0")
      if ext in webgl2_extensions_raw_software:
        setattr(dataValues, "webgl2_extensions_raw_software_" + ext, "1")
      else:
        setattr(dataValues, "webgl2_extensions_raw_software_" + ext, "0")

    self.applied_effect = True

  def revert(self, dataValues):
    pass

from fingerprinters import ALL_FINGERPRINTERS_UNION

class minimizeMemoryFilter(Filter):
  def __init__(self, dataValues):
    # Remove all attributes not in the fingerprinters metric list
    for attr in list(vars(dataValues).keys()):
      if attr not in ALL_FINGERPRINTERS_UNION and attr not in ['filters', 'os', 'hw_cpu_arch']:
        delattr(dataValues, attr)

    self.applied_effect = True

  def revert(self, dataValues):
    # This filter does not support reverting
    pass