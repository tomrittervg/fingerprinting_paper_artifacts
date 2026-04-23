import ast
import re
from pathlib import Path


def validate_filters_update_combined_hashes():
    """Check that every experiment filter which modifies a combined-hash component
    also modifies the corresponding combined hash.

    Parses configs/metadata_combined_metrics_composition.txt to build the
    component → combined_hash mapping, then AST-walks experiments.py to find
    filters that modify components without their hashes.

    Raises AssertionError if any filter is missing a combined hash update.
    """
    # ── Parse the composition file ───────────────────────────────────────
    comp_file = Path(__file__).parent / 'configs' / 'metadata_combined_metrics_composition.txt'
    component_to_hash = {}  # datavalues attr name → list of combined hash attr names

    # The composition file uses BQ column names (e.g. "canvasdata1") which differ
    # from DataValues attr names (e.g. "canvas_canvasdata01"). We need a name
    # normalization map. Build it from the _DEFAULT_SUBSET_BASE in datavalues.py.
    # Instead, use a simpler approach: parse the file for hash→components, then
    # try to match component names to DataValues attributes by prefix/suffix rules.

    current_hash = None
    raw_mapping = {}  # combined_hash_name → [bq_component_names]
    with open(comp_file) as f:
        for line in f:
            line = line.rstrip()
            if not line or line.startswith('=') or line.startswith('Combined') or line.startswith('Source'):
                current_hash = None
                continue
            m = re.match(r'^(\S+)\s+\(\d+ components?\)', line)
            if m:
                current_hash = m.group(1)
                raw_mapping[current_hash] = []
                continue
            if current_hash and line.startswith('    '):
                raw_mapping[current_hash].append(line.strip())

    # ── Map BQ component names → DataValues attribute names ──────────────
    # Convention: BQ "canvasdata1" → DV "canvas_canvasdata01"
    #             BQ "fonts_variant_a_allowlisted" → DV same
    #             BQ "mathml1" → DV "mathml_1"
    #             BQ "math_ops" → DV individual "math_op_0"..."math_op_23"
    # For the validation, we care about the individual attrs that a filter
    # might modify, not the raw JSON blobs. Build the mapping manually for
    # the known patterns.

    def bq_to_dv_attrs(hash_name, bq_name):
        """Convert a BQ component name to the DataValues attribute name(s)."""
        # Canvas: canvasdata1 → canvas_canvasdata01
        if bq_name.startswith('canvasdata') and not bq_name.endswith('software'):
            suffix = bq_name[len('canvasdata'):]
            # e.g. "1" → "01", "11_webgl" stays
            num_part = suffix.split('_')[0]
            rest = suffix[len(num_part):]
            return [f'canvas_canvasdata{int(num_part):02d}{rest}']
        if bq_name.startswith('canvasdata') and bq_name.endswith('_software'):
            base = bq_name[:-len('_software')]
            suffix = base[len('canvasdata'):]
            num_part = suffix.split('_')[0]
            rest = suffix[len(num_part):]
            return [f'canvassoftware_canvasdata{int(num_part):02d}{rest}']

        # Clientrects: already match DV names
        if bq_name.startswith('clientrects_'):
            return [bq_name]

        # MathML: mathml1 → mathml_1
        m = re.match(r'^mathml(\d+)$', bq_name)
        if m:
            return [f'mathml_{m.group(1)}']

        # Math ops: "math_ops" is a JSON blob that gets exploded to math_op_0..23
        if bq_name == 'math_ops':
            return [f'math_op_{i}' for i in range(24)]
        if bq_name == 'math_ops_fdlibm':
            return [f'math_op_fdlibm_{i}' for i in range(24)]
        if bq_name == 'math_ops_fdlibm_2':
            return [f'math_op_diag_{i}' for i in range(36)]

        # Fonts variants: already match
        if bq_name.startswith('fonts_variant_'):
            return [bq_name]

        # CSS: "css_system_colors" → DV "font_css_system_colors"
        if bq_name == 'css_system_colors':
            return ['font_css_system_colors']
        if bq_name == 'css_system_fonts':
            return ['font_css_system_fonts']

        # WebGL params: raw JSON blobs → individual param attrs
        # gl_params → webgl_params (raw text2), but also individual webgl_params_* attrs
        if bq_name == 'gl_params':
            return ['webgl_params']
        if bq_name == 'gl_params_software':
            return ['webgl_params_software']
        if bq_name == 'gl2_params':
            return ['webgl2_params']
        if bq_name == 'gl2_params_software':
            return ['webgl2_params_software']
        if bq_name == 'gl_params_extensions':
            return ['webgl_params_extensions']
        if bq_name == 'gl_params_extensions_software':
            return ['webgl_params_extensions_software']
        if bq_name == 'gl2_params_extensions':
            return ['webgl2_params_extensions']
        if bq_name == 'gl2_params_extensions_software':
            return ['webgl2_params_extensions_software']

        # Media
        if bq_name.startswith('media_capabilities_'):
            if bq_name == 'media_capabilities_h264':
                return ['media_h264']
            return [bq_name]

        # MathML diag
        if bq_name == 'mathml_diag_values':
            return [f'mathml_diag_{i}' for i in range(1, 20)]

        # WGPU: already match
        if bq_name.startswith('wgpu_'):
            return [bq_name]

        return [bq_name]  # fallback: assume same name

    for hash_name, bq_components in raw_mapping.items():
        for bq in bq_components:
            for dv_attr in bq_to_dv_attrs(hash_name, bq):
                component_to_hash.setdefault(dv_attr, []).append(hash_name)

    # ── AST-walk experiments.py to find all attrs each filter modifies ──
    exp_path = Path(__file__).parent / 'experiments.py'
    with open(exp_path) as f:
        source = f.read()
    tree = ast.parse(source)

    problems = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not node.name[0].islower():
            continue  # filter classes start lowercase

        # Collect statically-known modified attributes
        modified_attrs = set()

        # Also resolve class-level lists (e.g. _canvas_attrs = [...])
        class_lists = {}  # name → list of string values
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and isinstance(child.value, ast.List):
                        vals = [elt.value for elt in child.value.elts
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
                        if vals:
                            class_lists[target.id] = vals

        for child in ast.walk(node):
            # Direct: dataValues.X = ...
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if (isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == 'dataValues'):
                        modified_attrs.add(target.attr)
                    # Also: self.originals[key] = ... where key tells us what's saved
                    if (isinstance(target, ast.Subscript)
                            and isinstance(target.value, ast.Attribute)
                            and isinstance(target.slice, ast.Constant)
                            and isinstance(target.slice.value, str)):
                        # This is saving an original — the attr name in the key
                        modified_attrs.add(target.slice.value)

            # setattr(dataValues, constant_string, ...)
            if (isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == 'setattr'
                    and len(child.args) >= 2
                    and isinstance(child.args[0], ast.Name)
                    and child.args[0].id == 'dataValues'):
                if isinstance(child.args[1], ast.Constant):
                    modified_attrs.add(child.args[1].value)

            # for attr in self._canvas_attrs: ... setattr(dataValues, attr, ...)
            # Detect: iteration over a class list used in setattr
            if isinstance(child, ast.For):
                iter_node = child.iter
                if (isinstance(iter_node, ast.Attribute)
                        and isinstance(iter_node.value, ast.Name)
                        and iter_node.value.id == 'self'):
                    list_name = iter_node.attr
                    if list_name in class_lists:
                        modified_attrs.update(class_lists[list_name])
                # Also: for attr in self._vendor_attrs + self._renderer_attrs
                if isinstance(iter_node, ast.BinOp) and isinstance(iter_node.op, ast.Add):
                    for operand in [iter_node.left, iter_node.right]:
                        if (isinstance(operand, ast.Attribute)
                                and isinstance(operand.value, ast.Name)
                                and operand.value.id == 'self'
                                and operand.attr in class_lists):
                            modified_attrs.update(class_lists[operand.attr])

        # Check: any modified attr is a combined-hash component without its hash also modified?
        for attr in modified_attrs:
            if attr in component_to_hash:
                for h in component_to_hash[attr]:
                    if h not in modified_attrs:
                        problems.append((node.name, attr, h))

    if problems:
        msg = "Experiment filters modify combined-hash components without updating the hash:\n"
        for filt, attr, h in problems:
            msg += f"  {filt}: modifies {attr} but not {h}\n"
        raise AssertionError(msg)


def _load_datavalues_for_validation(max_users=50):
    """Load DataValues from cache for filter validation.
    Returns a list (may be empty if no cache is available)."""
    import glob
    import pickle as _pickle
    cache_base = Path('/work/sandbox-cache')
    if not cache_base.exists():
        cache_base = Path(__file__).parent.parent / 'sandbox-cache'
    if not cache_base.exists():
        return []

    from datavalues import DataValues, Struct

    result = []
    # Try multiple partition bins to get diverse users (different OS, etc.)
    bins = sorted(glob.glob(str(cache_base / '*/days/*/raw_rows_*.bin')))
    for bin_path in bins:
        if len(result) >= max_users:
            break
        try:
            with open(bin_path, 'rb') as f:
                rows = _pickle.load(f)
            for row in rows:
                if len(result) >= max_users:
                    break
                try:
                    result.append(DataValues(Struct(**row)))
                except Exception:
                    continue
        except Exception:
            continue
    return result


def backup_timezone(s):
  timezone_offsets = {
    "America/Buenos_Aires": -10800,
    "America/Catamarca": -10800,
    "America/Cordoba": -10800,
    "America/Godthab": -3600,
    "America/Indianapolis": -14400,
    "America/Mendoza": -10800,
    "Asia/Calcutta": 19800,
    "Asia/Dacca": 21600,
    "Asia/Katmandu": 20700,
    "Asia/Rangoon": 23400,
    "Asia/Saigon": 25200,
    "Atlantic/Faeroe": 3600,
    "Australia/Queensland": 36000,
    "Australia/Victoria": 36000,
    "Brazil/East": -10800,
    "Brazil/West": -14400,
    "Canada/Atlantic": -10800,
    "Canada/Central": -18000,
    "Canada/Eastern": -14400,
    "Canada/Mountain": -21600,
    "Canada/Newfoundland": -9000,
    "Canada/Pacific": -25200,
    "Canada/Saskatchewan": -21600,
    "Chile/Continental": -14400,
    "Eire": 3600,
    "Europe/Kiev": 10800,
    "Europe/Zaporozhye": 10800,
    "GB": 3600,
    "GMT0": 0,
    "Iceland": 0,
    "Israel": 10800,
    "Japan": 32400,
    "Mexico/General": -21600,
    "NZ": 43200,
    "Navajo": -21600,
    "PRC": 28800,
    "Pacific/Ponape": 39600,
    "Poland": 7200,
    "ROC": 28800,
    "Singapore": 28800,
    "Turkey": 10800,
    "US/Arizona": -25200,
    "US/Central": -18000,
    "US/Eastern": -14400,
    "US/Hawaii": -36000,
    "US/Michigan": -14400,
    "US/Mountain": -21600,
    "US/Pacific": -25200,
    "W-SU": 10800,
    "AEST": 36000,
    "Asia/Beijing": 28800,
    "CST": -18000,
    "China Standard Time": 28800,
    "Coordinated Universal Time": 0,
    "E. South America Standard Time": -10800,
    "EST3": -14400,
    "Eastern Standard Time": -14400,
    "Egypt Standard Time": 10800,
    "GMT-05:00": -18000,
    "GTB, normaltid": 10800,
    "India Standard Time": 19800,
    "Iran Standard Time": 12600,
    "Maroc": 3600,
    "Pacific Standard Time": -25200,
    "Paris, Madrid": 7200,
    "Romance Standard Time": 7200,
    "Russia TZ 4 Standard Time": 14400,
    "SE Asia Daylight Time": 25200,
    "Türkiye Standart Saati": 10800,
    "W. Europe Standard Time": 7200,
    "West-Europa (standaardtijd)": 7200,
    "Hora Padrão da Argentina": -10800,             # America/Argentina/Buenos_Aires (UTC−3)
    "Hora est. Pacífico, Sudamérica": -14400,       # America/Santiago (Chile/Continental) (UTC−4 in June)
    "Hora est. Sudamérica Pacífico": -14400,        # same as above
    "Hora estándar Montañas, EE.UU": -21600,        # America/Denver (Mountain Time with DST: UTC−6 in June)
    "Hora estándar Pacífico (México": -25200,       # America/Tijuana (Pacific Time with DST: UTC−7 in June)
    "Hora oficial do Brasil": -10800,               # America/Sao_Paulo (Brasília Time UTC−3)
  }
  if s in timezone_offsets:
    return timezone_offsets[s]
  return None