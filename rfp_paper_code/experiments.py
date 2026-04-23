import datetime
import json
import zoneinfo
from filters import Filter, CorrectionFilter
import hashlib

from utility import backup_timezone
from webgl_constants import BACKWARD_TIMEZONE_MAPPINGS, NON_BACKWARD_TIMEZONE_MAPPINGS, tz_abbr_to_utc_offset

# ====================================================================================================================
class noProcessorCountFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['hw_processor_count']

    def __init__(self, dataValues):
        self.rPC_originals = {}

        self.applied_effect = False
        found_correction_filter = False
        for filter_obj in dataValues.filters:
            if isinstance(filter_obj, CorrectionFilter):
                found_correction_filter = True
                self.rPC_originals['hw_processor_count'] = dataValues.hw_processor_count

                original_processor_count = filter_obj.originals['hw_processor_count']
                dataValues.hw_processor_count = original_processor_count
                self.applied_effect = True
                break
        assert found_correction_filter, "noProcessorCountFilter requires CorrectionFilter to be applied first"

    def revert(self, dataValues):
        dataValues.hw_processor_count = self.rPC_originals['hw_processor_count']

class noWebGLRendererSanitizing(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['webgl_renderer']

    def __init__(self, dataValues):
        self.wgl_renderer_originals = {}
        self.wgl_renderer_originals['webgl_renderer'] = dataValues.webgl_renderer

        dataValues.webgl_renderer = dataValues.webgl_renderer_raw
        self.applied_effect = True

    def revert(self, dataValues):
        dataValues.webgl_renderer = self.wgl_renderer_originals['webgl_renderer']

class removeMinorVersionProtection(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['user_agent']

    def __init__(self, dataValues):
        self.mv_originals = {}
        self.mv_originals['user_agent'] = dataValues.user_agent

        major = dataValues.version.split(".")[0]
        search_for = f"{major}.0"

        dataValues.user_agent = dataValues.user_agent.replace(search_for, dataValues.version)
        self.applied_effect = dataValues.user_agent != self.mv_originals['user_agent']

    def revert(self, dataValues):
        dataValues.user_agent = self.mv_originals['user_agent']

# ── Inverse Phase 0 filters: re-apply protections on top of baked-in raw values ──
class addProcessorCountProtection(Filter):
    """Re-apply processor count capping (inverse of noProcessorCountFilter).
    Caps hw_processor_count at 128, matching CorrectionFilter's logic."""
    @classmethod
    def affected_metrics(cls):
        return ['hw_processor_count']

    def __init__(self, dataValues):
        self.originals = {'hw_processor_count': dataValues.hw_processor_count}
        if dataValues.hw_processor_count > 128:
            dataValues.hw_processor_count = 128
        self.applied_effect = dataValues.hw_processor_count != self.originals['hw_processor_count']

    def revert(self, dataValues):
        dataValues.hw_processor_count = self.originals['hw_processor_count']

class addWebGLRendererSanitizing(Filter):
    """Re-apply WebGL renderer sanitization (inverse of noWebGLRendererSanitizing).
    Restores the sanitized webgl_renderer from the baked-in noWebGLRendererSanitizing filter."""
    @classmethod
    def affected_metrics(cls):
        return ['webgl_renderer']

    def __init__(self, dataValues):
        self.originals = {'webgl_renderer': dataValues.webgl_renderer}
        for f in dataValues.filters:
            if isinstance(f, noWebGLRendererSanitizing):
                dataValues.webgl_renderer = f.wgl_renderer_originals['webgl_renderer']
                self.applied_effect = True
                return
        # If noWebGLRendererSanitizing not found, no-op
        self.applied_effect = False

    def revert(self, dataValues):
        dataValues.webgl_renderer = self.originals['webgl_renderer']

class addMinorVersionProtection(Filter):
    """Re-apply minor version protection (inverse of removeMinorVersionProtection).
    Restores the protected user_agent from the baked-in removeMinorVersionProtection filter."""
    @classmethod
    def affected_metrics(cls):
        return ['user_agent']

    def __init__(self, dataValues):
        self.originals = {'user_agent': dataValues.user_agent}
        for f in dataValues.filters:
            if isinstance(f, removeMinorVersionProtection):
                dataValues.user_agent = f.mv_originals['user_agent']
                self.applied_effect = True
                return
        # If removeMinorVersionProtection not found, no-op
        self.applied_effect = False

    def revert(self, dataValues):
        dataValues.user_agent = self.originals['user_agent']

# ====================================================================================================================
class addGamePadProtection(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['hw_gamepads']

    def __init__(self, dataValues):
        self.gp_originals = {}
        self.gp_originals['hw_gamepads'] = dataValues.hw_gamepads

        dataValues.hw_gamepads = ""
        self.applied_effect = True

    def revert(self, dataValues):
        dataValues.hw_gamepads = self.gp_originals['hw_gamepads']

class addMediaCountProtection(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['hw_camera_count', 'hw_microphone_count']

    def __init__(self, dataValues):
        self.mc_originals = {}
        self.mc_originals['hw_camera_count'] = dataValues.hw_camera_count
        self.mc_originals['hw_microphone_count'] = dataValues.hw_microphone_count

        dataValues.hw_camera_count = 1
        dataValues.hw_microphone_count = 1
        self.applied_effect = True

    def revert(self, dataValues):
        dataValues.hw_camera_count = self.mc_originals['hw_camera_count']
        dataValues.hw_microphone_count = self.mc_originals['hw_microphone_count']

# ====================================================================================================================

class screenAvailFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['screen_primary_avail', 'screen_primary_avail_diff']

    def __init__(self, dataValues):
        self.sa_originals = {}
        self.sa_originals['screen_primary_avail'] = dataValues.screen_primary_avail
        self.sa_originals['screen_primary_avail_diff'] = dataValues.screen_primary_avail_diff

        dataValues.screen_primary_avail = dataValues.screen_primary_resolution
        dataValues.screen_primary_avail_diff = "0x0"
        self.applied_effect = True

    def revert(self, dataValues):
        dataValues.screen_primary_avail = self.sa_originals['screen_primary_avail']
        dataValues.screen_primary_avail_diff = self.sa_originals['screen_primary_avail_diff']


class mathmlFilter(Filter):
    """Blank all MathML metrics and their combined hashes."""
    @classmethod
    def affected_metrics(cls):
        return list(cls._attrs)

    _attrs = (
        [f'mathml_{i}' for i in range(1, 11)]
        + ['combined_mathml_hash', 'mathml_diag_font_family', 'mathml_diag_prefs_modified',
           'mathml_diag_values', 'combined_mathml_diag_hash']
        + [f'mathml_diag_{i}' for i in range(1, 20)]
    )

    def __init__(self, dataValues):
        self.originals = {}
        for attr in self._attrs:
            self.originals[attr] = getattr(dataValues, attr)
            setattr(dataValues, attr, "")
        self.applied_effect = True

    def revert(self, dataValues):
        for attr, val in self.originals.items():
            setattr(dataValues, attr, val)


class cssSystemColorsFilter(Filter):
    """Blank CSS system color metrics and their combined hash."""
    @classmethod
    def affected_metrics(cls):
        return list(cls._attrs)

    _attrs = [
        'font_css_system_colors', 'combined_css_colors_hash',
        'css_color_accentcolor', 'css_color_accentcolortext',
        'css_color_activeborder', 'css_color_activecaption', 'css_color_activetext',
        'css_color_appworkspace', 'css_color_background',
        'css_color_buttonborder', 'css_color_buttonface',
        'css_color_buttonhighlight', 'css_color_buttonshadow', 'css_color_buttontext',
        'css_color_canvas', 'css_color_canvastext', 'css_color_captiontext',
        'css_color_field', 'css_color_fieldtext', 'css_color_graytext',
        'css_color_highlight', 'css_color_highlighttext',
        'css_color_inactiveborder', 'css_color_inactivecaption', 'css_color_inactivecaptiontext',
        'css_color_infobackground', 'css_color_infotext',
        'css_color_linktext', 'css_color_mark', 'css_color_marktext',
        'css_color_menu', 'css_color_menutext',
        'css_color_scrollbar', 'css_color_selecteditem', 'css_color_selecteditemtext',
        'css_color_threeddarkshadow', 'css_color_threedface',
        'css_color_threedhighlight', 'css_color_threedlightshadow', 'css_color_threedshadow',
        'css_color_visitedtext', 'css_color_window', 'css_color_windowframe', 'css_color_windowtext',
    ]

    def __init__(self, dataValues):
        self.originals = {}
        for attr in self._attrs:
            self.originals[attr] = getattr(dataValues, attr)
            setattr(dataValues, attr, "")
        self.applied_effect = True

    def revert(self, dataValues):
        for attr, val in self.originals.items():
            setattr(dataValues, attr, val)


class voicesFilter(Filter):
    """Blank all speech synthesis voices metrics."""
    @classmethod
    def affected_metrics(cls):
        return list(cls._attrs)

    _attrs = [
        'voices_all_ssdeep', 'voices_count', 'voices_default',
        'voices_local_count', 'voices_local_ssdeep', 'voices_nonlocal_ssdeep',
        'voices_sample', 'voices_sha1',
    ]

    def __init__(self, dataValues):
        self.originals = {}
        for attr in self._attrs:
            self.originals[attr] = getattr(dataValues, attr)
            setattr(dataValues, attr, "")
        self.applied_effect = True

    def revert(self, dataValues):
        for attr, val in self.originals.items():
            setattr(dataValues, attr, val)


class letterboxingFilter(Filter):
    """Simulate RFP letterboxing: round inner window dimensions down to stepped sizes.

    Uses the same algorithm as Firefox's RFPHelper.sys.mjs steppedSize():
      - dim <= 50:     no rounding
      - dim 51-500:    round down to nearest 50
      - dim 501-1600:  round down to nearest 200 (width) or 100 (height)
      - dim > 1600:    round down to nearest 200
    """

    @classmethod
    def affected_metrics(cls):
        return list(cls._attrs)

    @staticmethod
    def _stepped_size(dimension, is_width=False):
        if dimension <= 50:
            return dimension
        elif dimension <= 500:
            stepping = 50
        elif dimension <= 1600:
            stepping = 200 if is_width else 100
        else:
            stepping = 200
        return dimension - (dimension % stepping)

    _attrs = [
        'screen_web_inner',
        'screen_web_inner_width',
        'screen_web_inner_height',
        'screen_web_inner_diff',
        'screen_web_inner_width_diff',
        'screen_web_inner_height_diff',
    ]

    def __init__(self, dataValues):
        self.originals = {}
        for attr in self._attrs:
            self.originals[attr] = getattr(dataValues, attr)

        try:
            w = int(dataValues.screen_web_inner_width)
            h = int(dataValues.screen_web_inner_height)
        except (ValueError, TypeError):
            return  # can't parse dimensions

        new_w = self._stepped_size(w, is_width=True)
        new_h = self._stepped_size(h, is_width=False)

        if new_w == w and new_h == h:
            return  # no change needed

        dataValues.screen_web_inner = f"{new_w}x{new_h}"
        dataValues.screen_web_inner_width = str(new_w)
        dataValues.screen_web_inner_height = str(new_h)

        # Recompute diffs (screen resolution - inner)
        try:
            screen_w, screen_h = dataValues.screen_primary_resolution.split('x')
            dataValues.screen_web_inner_width_diff = str(int(screen_w) - new_w)
            dataValues.screen_web_inner_height_diff = str(int(screen_h) - new_h)
            dataValues.screen_web_inner_diff = f"{dataValues.screen_web_inner_width_diff}x{dataValues.screen_web_inner_height_diff}"
        except (ValueError, TypeError, AttributeError):
            pass

        self.applied_effect = True

    def revert(self, dataValues):
        for attr, val in self.originals.items():
            setattr(dataValues, attr, val)


class procCountFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['hw_processor_count']

    def __init__(self, dataValues):
        self.pc_originals = {}
        self.pc_originals['hw_processor_count'] = dataValues.hw_processor_count

        if dataValues.hw_processor_count >= 8:
           dataValues.hw_processor_count = 8
        else:
           dataValues.hw_processor_count = 4

        self.applied_effect = True

    def revert(self, dataValues):
        dataValues.hw_processor_count = self.pc_originals['hw_processor_count']


class fdlibmFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return [f'math_op_{i}' for i in range(24)] + ['combined_math_ops_hash']

    def __init__(self, dataValues):
        self.fd_originals = {}
        self.applied_effect = False

        if dataValues.os == "WINNT":
            # Replace individual math_op values with fdlibm equivalents
            for i in range(24):
                math_op_key = f'math_op_{i}'
                fdlibm_key = f'math_op_fdlibm_{i}'

                self.fd_originals[math_op_key] = getattr(dataValues, math_op_key, None)
                if (
                    getattr(dataValues, math_op_key, None) != getattr(dataValues, fdlibm_key, "None")
                    and getattr(dataValues, fdlibm_key, "None") != "None"
                ):
                    setattr(dataValues, math_op_key, getattr(dataValues, fdlibm_key))
                    self.applied_effect = True

            # Replace the combined hash with the fdlibm variant so fingerprinters
            # that use combined_math_ops_hash (e.g. FPJSv2) see the change
            fdlibm_hash = getattr(dataValues, 'combined_math_ops_fdlibm_hash', 'None')
            if fdlibm_hash != 'None':
                self.fd_originals['combined_math_ops_hash'] = dataValues.combined_math_ops_hash
                dataValues.combined_math_ops_hash = fdlibm_hash
                self.applied_effect = True

    def revert(self, dataValues):
        for key, val in self.fd_originals.items():
            setattr(dataValues, key, val)


class fontProtectionsFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['fonts_fpjs_nonallowlisted', 'fonts_variant_a_nonallowlisted',
                'fonts_variant_b_nonallowlisted', 'combined_fonts_variants_nonallowlisted_hash']

    def __init__(self, dataValues):
        self.fp_originals = {}
        self.fp_originals['fonts_fpjs_nonallowlisted'] = dataValues.fonts_fpjs_nonallowlisted
        self.fp_originals['fonts_variant_a_nonallowlisted'] = dataValues.fonts_variant_a_nonallowlisted
        self.fp_originals['fonts_variant_b_nonallowlisted'] = dataValues.fonts_variant_b_nonallowlisted
        self.fp_originals['combined_fonts_variants_nonallowlisted_hash'] = dataValues.combined_fonts_variants_nonallowlisted_hash

        dataValues.fonts_fpjs_nonallowlisted = ""
        dataValues.fonts_variant_a_nonallowlisted = ""
        dataValues.fonts_variant_b_nonallowlisted = ""
        dataValues.combined_fonts_variants_nonallowlisted_hash = ""
        self.applied_effect = True

    def revert(self, dataValues):
        for key, val in self.fp_originals.items():
            setattr(dataValues, key, val)


class shippingMissingFontsFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['fonts_fpjs_allowlisted', 'fonts_variant_a_allowlisted',
                'fonts_variant_b_allowlisted', 'combined_fonts_variants_allowlisted_hash']

    def __init__(self, dataValues):
        self.sm_originals = {}
        self.sm_originals['fonts_fpjs_allowlisted'] = dataValues.fonts_fpjs_allowlisted
        self.sm_originals['fonts_variant_a_allowlisted'] = dataValues.fonts_variant_a_allowlisted
        self.sm_originals['fonts_variant_b_allowlisted'] = dataValues.fonts_variant_b_allowlisted
        self.sm_originals['combined_fonts_variants_allowlisted_hash'] = dataValues.combined_fonts_variants_allowlisted_hash

        dataValues.fonts_fpjs_allowlisted = ""
        dataValues.fonts_variant_a_allowlisted = ""
        dataValues.fonts_variant_b_allowlisted = ""
        dataValues.combined_fonts_variants_allowlisted_hash = ""
        self.applied_effect = True

    def revert(self, dataValues):
        for key, val in self.sm_originals.items():
            setattr(dataValues, key, val)


class fontListUpdatesFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['fonts_fpjs_allowlisted']

    # ordered list
    fpjs_checked_but_kept_fonts = [
        "calibri",
        "marlett",
        "microsoft uighur",
        "ms ui gothic",
    ]

    # fonts I will remove from the allowlist
    removed_fonts = set([
        "arabic typesetting",
        "batang",
        "leelawadee",
        "levenim mt",
        "meiryo ui",
        "ms mincho",
        "pmingliu",
        "segoe ui light",
        "simhei",
        "vrinda"
    ])
    def __init__(self, dataValues):
        self.fl_originals = {}
        self.fl_originals['fonts_fpjs_allowlisted'] = dataValues.fonts_fpjs_allowlisted
        # No fingerprinter uses this
        #self.fl_originals['fonts_variant_a_allowlisted'] = dataValues.fonts_variant_a_allowlisted
        #self.fl_originals['fonts_variant_b_allowlisted'] = dataValues.fonts_variant_b_allowlisted

        if dataValues.os == "WINNT":
            if self.removed_fonts & set(dataValues.missing_fonts):
                new_missing_allowlisted_fonts = []
                for f in self.fpjs_checked_but_kept_fonts:
                    new_missing_allowlisted_fonts.append(f)
                dataValues.fonts_fpjs_allowlisted = hashlib.sha256("".join(new_missing_allowlisted_fonts).encode('utf-8')).hexdigest().lower()

                self.applied_effect = True

    def revert(self, dataValues):
        dataValues.fonts_fpjs_allowlisted = self.fl_originals['fonts_fpjs_allowlisted']
        #dataValues.fonts_variant_a_allowlisted = self.fl_originals['fonts_variant_a_allowlisted']
        #dataValues.fonts_variant_b_allowlisted = self.fl_originals['fonts_variant_b_allowlisted']

class fontListUpdatesFilterLocaleConsideration(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['fonts_fpjs_allowlisted']

    per_font_settings = {
        "arabic typesetting": {"ar": "StartsWith", "fa": "StartsWith"},
        "batang": {"ko": "StartsWith"},
        "leelawadee": {"th": "StartsWith"},
        "levenim mt": {"he": "StartsWith", "en-il": "Exact"},
        "meiryo ui": {"ja": "StartsWith"},
        "microsoft uighur": {"ar": "StartsWith", "fa": "StartsWith"},
        "ms mincho": {"ja": "StartsWith"},
        "pmingliu": {"zh-hant": "StartsWith"},
        "simhei": {"zh-hans": "StartsWith"}
    }
    fonts_that_are_allowlisted_but_could_also_be_missing = [
        "calibri",
        "marlett",
        "ms ui gothic",
        "segoe ui light",
        "vrinda",
    ]

    def __init__(self, dataValues):
        self.fl2_originals = {}
        self.fl2_originals['fonts_fpjs_allowlisted'] = dataValues.fonts_fpjs_allowlisted

        if dataValues.os == "WINNT":
            new_missing_allowlisted_fonts = []
            for font in dataValues.missing_fonts:
                if font in self.fonts_that_are_allowlisted_but_could_also_be_missing:
                    new_missing_allowlisted_fonts.append(font)

            for font in self.per_font_settings:
                if font in set(dataValues.missing_fonts):
                    for locale in self.per_font_settings[font]:
                        setting = self.per_font_settings[font][locale]
                        if setting == "StartsWith":
                            if dataValues.locale_accept_language.startswith(locale):
                                new_missing_allowlisted_fonts.append(font)
                                break
                        elif setting == "Exact":
                            if dataValues.locale_accept_language == locale:
                                new_missing_allowlisted_fonts.append(font)
                                break

            dataValues.fonts_fpjs_allowlisted = hashlib.sha256("".join(new_missing_allowlisted_fonts).encode('utf-8')).hexdigest().lower()
            self.applied_effect = True

    def revert(self, dataValues):
        dataValues.fonts_fpjs_allowlisted = self.fl2_originals['fonts_fpjs_allowlisted']


class timezoneFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['intl_timezone', 'intl_timezoneoffset', 'intl_timezone_web', 'intl_timezone_offset_web']

    def __init__(self, dataValues):
        self.tz_originals = {}
        self.tz_originals['intl_timezone'] = dataValues.intl_timezone
        self.tz_originals['intl_timezoneoffset'] = dataValues.intl_timezoneoffset
        self.tz_originals['intl_timezone_web'] = dataValues.intl_timezone_web
        self.tz_originals['intl_timezone_offset_web'] = dataValues.intl_timezone_offset_web

        # While an offset doesn't make sense as a Timezone name, we can pretend we map the Timezone name to the most popular value for this offset
        # We've already
        #  (a) Ensured that timezone string is one of the recognized values, and if not - set it to GMT
        #  (b) Calculated an offset for that value
        # Now we're going to take the offset and go backwards to a single timezone that has that offset at the present day
        # We're going to simulate this by just assigning the offset as the timezone name
        dataValues.intl_timezone = dataValues.intl_timezoneoffset
        # Apply the same collapsing to the web-exposed attributes (what fingerprinters see)
        dataValues.intl_timezone_web = dataValues.intl_timezone_offset_web
        self.applied_effect = True
        return

        def convert_timezone_to_normalized_offset(timezone_name):
            new_value = None
            if timezone_name in BACKWARD_TIMEZONE_MAPPINGS:
                timezone_name = BACKWARD_TIMEZONE_MAPPINGS[timezone_name]

            for tz_map in NON_BACKWARD_TIMEZONE_MAPPINGS:
                if timezone_name in tz_map:
                    new_value = tz_map[timezone_name]
                    is_numeric = new_value.replace(":", "").lstrip("+-").isdigit()
                    if not is_numeric:
                        new_value = tz_abbr_to_utc_offset(new_value)
                        if new_value:
                            new_value = convert_minutes_offset_to_string(int(new_value))
            return new_value


        def convert_seconds_offset_to_string(offset):
            sign = "-" if offset < 0 else ""
            offset = abs(offset)
            hours = offset // 3600
            minutes = (offset % 3600) // 60
            offset = f"{sign}{hours}{minutes:02d}"
            return offset

        def convert_minutes_offset_to_string(offset):
            sign = "-" if offset < 0 else ""
            offset = abs(offset)
            hours = offset // 60
            minutes = offset % 60
            offset = f"{sign}{hours}{minutes:02d}"
            return offset

        # If the timezone from the user is nonsense, then we corrected the offset (but not the timezone name) during loading
        # However that offset won't mesh with the values we write in this filter, so we have to re-do that logic
        try:
            tz = zoneinfo.ZoneInfo(dataValues.intl_timezone)

            # If we did get a valid timezone, that's great, but we don't care.  We're going to normalize from the timezone
            # name
            new_value = convert_timezone_to_normalized_offset(dataValues.intl_timezone)
            if new_value:
                dataValues.intl_timezoneoffset = new_value
            else:
                # Okay what the hell. I guess we'll normalize from the offset then...
                now_in_tz = datetime.now(tz)
                offset_timedelta = now_in_tz.utcoffset()
                offset = convert_seconds_offset_to_string(offset_timedelta.total_seconds())
                dataValues.intl_timezoneoffset = offset
        except Exception as e:
            # It's possible, but unlikely, the unknown timezone name is an actally defined Zone name, so double check
            # If it is, use the resulting value.
            new_value = convert_timezone_to_normalized_offset(dataValues.intl_timezone)
            if new_value:
                dataValues.intl_timezoneoffset = new_value
            else:
                # Unsurprisingly, it's not.  Go to the last-ditch conversion table
                o = backup_timezone(dataValues.intl_timezone)
                if o:
                    # Here we wind up with an offset in seconds.  Convert it to HHMM format
                    dataValues.intl_timezoneoffset = convert_seconds_offset_to_string(o)
                else:
                    # Otherwise the offset is 0
                    dataValues.intl_timezoneoffset = 0

        dataValues.intl_timezoneoffset = str(dataValues.intl_timezoneoffset).replace(".0", "").replace("+", "")


        #print(f"{dataValues.intl_timezone}: {self.tz_originals['intl_timezoneoffset']} -> {dataValues.intl_timezoneoffset}")

        self.applied_effect = True

    def revert(self, dataValues):
        dataValues.intl_timezone = self.tz_originals['intl_timezone']
        dataValues.intl_timezoneoffset = self.tz_originals['intl_timezoneoffset']
        dataValues.intl_timezone_web = self.tz_originals['intl_timezone_web']
        dataValues.intl_timezone_offset_web = self.tz_originals['intl_timezone_offset_web']


class touchPointFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['hw_max_touch_points']

    def __init__(self, dataValues):
        self.tp_originals = {}
        self.tp_originals['hw_max_touch_points'] = dataValues.hw_max_touch_points

        if dataValues.hw_max_touch_points > 0:
            if dataValues.hw_max_touch_points > 10:
                dataValues.hw_max_touch_points = 10
            else:
                dataValues.hw_max_touch_points = 1
            self.applied_effect = True

    def revert(self, dataValues):
        dataValues.hw_max_touch_points = self.tp_originals['hw_max_touch_points']


class acceptLanguageLimitFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['locale_accept_language', 'locale_languages']

    def __init__(self, dataValues):
        self.al_originals = {}
        self.al_originals['locale_accept_language'] = dataValues.locale_accept_language
        self.al_originals['locale_languages'] = dataValues.locale_languages

        if "," in dataValues.locale_accept_language:
            dataValues.locale_accept_language = dataValues.locale_accept_language.split(",")[0]
            self.applied_effect = True

        if "," in dataValues.locale_languages:
            dataValues.locale_languages = dataValues.locale_languages.split(",")[0]
            self.applied_effect = True

    def revert(self, dataValues):
        dataValues.locale_accept_language = self.al_originals['locale_accept_language']
        dataValues.locale_languages = self.al_originals['locale_languages']


class acceptLanguageLimitAndCollapseFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['locale_accept_language', 'locale_languages']

    def __init__(self, dataValues):
        self.ac_originals = {}
        self.ac_originals['locale_accept_language'] = dataValues.locale_accept_language
        self.ac_originals['locale_languages'] = dataValues.locale_languages

        if "," in dataValues.locale_accept_language:
            dataValues.locale_accept_language = dataValues.locale_accept_language.split(",")[0]
            self.applied_effect = True

        if "-" in dataValues.locale_accept_language:
            dataValues.locale_accept_language = dataValues.locale_accept_language.split("-")[0]
            self.applied_effect = True

        if "," in dataValues.locale_languages:
            dataValues.locale_languages = dataValues.locale_languages.split(",")[0]
            self.applied_effect = True

        if "-" in dataValues.locale_languages:
            dataValues.locale_languages = dataValues.locale_languages.split("-")[0]
            self.applied_effect = True

    def revert(self, dataValues):
        dataValues.locale_accept_language = self.ac_originals['locale_accept_language']
        dataValues.locale_languages = self.ac_originals['locale_languages']


class acceptLanguageCollapseFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['locale_accept_language', 'locale_languages']

    def __init__(self, dataValues):
        self.ac_originals = {}
        self.ac_originals['locale_accept_language'] = dataValues.locale_accept_language
        self.ac_originals['locale_languages'] = dataValues.locale_languages

        def collapse(s):
            return ",".join(x.strip().split("-")[0] for x in s.split(","))

        dataValues.locale_accept_language = collapse(dataValues.locale_accept_language)
        dataValues.locale_languages = collapse(dataValues.locale_languages)
        self.applied_effect = True

    def revert(self, dataValues):
        dataValues.locale_accept_language = self.ac_originals['locale_accept_language']
        dataValues.locale_languages = self.ac_originals['locale_languages']

class storageQuotaFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return ['storage_quota']

    def __init__(self, dataValues):
        self.original = dataValues.storage_quota
        dataValues.storage_quota = '10240'
        self.applied_effect = dataValues.storage_quota != self.original

    def revert(self, dataValues):
        dataValues.storage_quota = self.original


class outerEqualsInnerFilter(Filter):
    """Set outer dimensions equal to inner dimensions, eliminating browser
    chrome size as a fingerprinting signal."""

    @classmethod
    def affected_metrics(cls):
        return [
            'screen_web_outer', 'screen_web_outer_width', 'screen_web_outer_height',
            'screen_web_outer_diff', 'screen_web_outer_width_diff', 'screen_web_outer_height_diff',
        ]

    def __init__(self, dataValues):
        self.originals = {m: getattr(dataValues, m) for m in self.affected_metrics()}

        dataValues.screen_web_outer = dataValues.screen_web_inner
        dataValues.screen_web_outer_width = dataValues.screen_web_inner_width
        dataValues.screen_web_outer_height = dataValues.screen_web_inner_height
        dataValues.screen_web_outer_diff = dataValues.screen_web_inner_diff
        dataValues.screen_web_outer_width_diff = dataValues.screen_web_inner_width_diff
        dataValues.screen_web_outer_height_diff = dataValues.screen_web_inner_height_diff

        self.applied_effect = any(
            getattr(dataValues, m) != self.originals[m] for m in self.affected_metrics()
        )

    def revert(self, dataValues):
        for m, v in self.originals.items():
            setattr(dataValues, m, v)


class mediaCapabilitiesFilter(Filter):
    """Normalize media capabilities to reduce fingerprinting surface.

    For each H.264 profile the user supports, clamp to the lowest tested level
    (4.0 / 0x28). Blank not_efficient and not_smooth (report all codecs as
    efficient and smooth). Recompute the combined hash. Leave unsupported and
    profile presence untouched so decode capability is not misrepresented."""

    _LOWEST_LEVEL = "28"  # H.264 level 4.0

    @classmethod
    def affected_metrics(cls):
        return [
            'media_h264',
            'media_capabilities_not_efficient',
            'media_capabilities_not_smooth',
            'combined_media_capabilities_hash',
        ]

    def __init__(self, dataValues):
        self.originals = {m: getattr(dataValues, m) for m in self.affected_metrics()}
        self.applied_effect = False

        # Clamp H.264 levels to lowest for each reported profile
        h264_raw = dataValues.media_h264
        if h264_raw and h264_raw not in ("None", "undefined", "{}"):
            try:
                h264 = json.loads(h264_raw)
                if isinstance(h264, dict) and h264:
                    clamped = {profile: self._LOWEST_LEVEL for profile in h264}
                    dataValues.media_h264 = json.dumps(clamped, separators=(',', ':'))
            except (json.JSONDecodeError, TypeError):
                pass

        # Blank not_efficient and not_smooth
        dataValues.media_capabilities_not_efficient = "[]"
        dataValues.media_capabilities_not_smooth = "[]"

        # Recompute combined hash (same formula as datavalues.py)
        dataValues.combined_media_capabilities_hash = hashlib.sha256(
            json.dumps(
                [None if v == "None" else v for v in [
                    dataValues.media_capabilities_not_efficient,
                    dataValues.media_capabilities_not_smooth,
                    dataValues.media_capabilities_unsupported,
                    dataValues.media_h264]],
                separators=(',', ':')).encode()
        ).hexdigest()

        self.applied_effect = any(
            getattr(dataValues, m) != self.originals[m] for m in self.affected_metrics()
        )

    def revert(self, dataValues):
        for m, v in self.originals.items():
            setattr(dataValues, m, v)


class webGLParamLiesFilter(Filter):
    @classmethod
    def affected_metrics(cls):
        return list(cls.webgl_params) + list(cls._combined_hashes)

    webgl_params = [
            "webgl_params_SHADING_LANGUAGE_VERSION",
    "webgl2_params_SHADING_LANGUAGE_VERSION",
    "webgl_precision_fragment",
    "webgl2_precision_fragment",
    "webgl_precision_vertex",
    "webgl2_precision_vertex",
    "webgl2_params_ALIASED_LINE_WIDTH_RANGE",
    "webgl2_params_ALIASED_POINT_SIZE_RANGE",
    "webgl2_params_MAX_3D_TEXTURE_SIZE",
    "webgl2_params_MAX_ARRAY_TEXTURE_LAYERS",
    "webgl2_params_MAX_CLIENT_WAIT_TIMEOUT_WEBGL",
    "webgl2_params_MAX_COLOR_ATTACHMENTS",
    "webgl2_params_MAX_COMBINED_FRAGMENT_UNIFORM_COMPONENTS",
    "webgl2_params_MAX_COMBINED_TEXTURE_IMAGE_UNITS",
    "webgl2_params_MAX_COMBINED_UNIFORM_BLOCKS",
    "webgl2_params_MAX_COMBINED_VERTEX_UNIFORM_COMPONENTS",
    "webgl2_params_MAX_CUBE_MAP_TEXTURE_SIZE",
    "webgl2_params_MAX_DRAW_BUFFERS",
    "webgl2_params_MAX_ELEMENTS_INDICES",
    "webgl2_params_MAX_ELEMENTS_VERTICES",
    "webgl2_params_MAX_ELEMENT_INDEX",
    "webgl2_params_MAX_FRAGMENT_INPUT_COMPONENTS",
    "webgl2_params_MAX_FRAGMENT_UNIFORM_BLOCKS",
    "webgl2_params_MAX_FRAGMENT_UNIFORM_COMPONENTS",
    "webgl2_params_MAX_FRAGMENT_UNIFORM_VECTORS",
    "webgl2_params_MAX_PROGRAM_TEXEL_OFFSET",
    "webgl2_params_MAX_RENDERBUFFER_SIZE",
    "webgl2_params_MAX_SAMPLES",
    "webgl2_params_MAX_SERVER_WAIT_TIMEOUT",
    "webgl2_params_MAX_TEXTURE_IMAGE_UNITS",
    "webgl2_params_MAX_TEXTURE_LOD_BIAS",
    "webgl2_params_MAX_TEXTURE_SIZE",
    "webgl2_params_MAX_TRANSFORM_FEEDBACK_INTERLEAVED_COMPONENTS",
    "webgl2_params_MAX_TRANSFORM_FEEDBACK_SEPARATE_ATTRIBS",
    "webgl2_params_MAX_TRANSFORM_FEEDBACK_SEPARATE_COMPONENTS",
    "webgl2_params_MAX_UNIFORM_BLOCK_SIZE",
    "webgl2_params_MAX_UNIFORM_BUFFER_BINDINGS",
    "webgl2_params_MAX_VARYING_COMPONENTS",
    "webgl2_params_MAX_VARYING_VECTORS",
    "webgl2_params_MAX_VERTEX_ATTRIBS",
    "webgl2_params_MAX_VERTEX_OUTPUT_COMPONENTS",
    "webgl2_params_MAX_VERTEX_TEXTURE_IMAGE_UNITS",
    "webgl2_params_MAX_VERTEX_UNIFORM_BLOCKS",
    "webgl2_params_MAX_VERTEX_UNIFORM_COMPONENTS",
    "webgl2_params_MAX_VERTEX_UNIFORM_VECTORS",
    "webgl2_params_MAX_VIEWPORT_DIMS",
    "webgl2_params_MIN_PROGRAM_TEXEL_OFFSET",
    #"webgl2_params_SHADING_LANGUAGE_VERSION",
    "webgl2_params_UNIFORM_BUFFER_OFFSET_ALIGNMENT",
    "webgl_params_ALIASED_LINE_WIDTH_RANGE",
    "webgl_params_ALIASED_POINT_SIZE_RANGE",
    "webgl_params_MAX_COMBINED_TEXTURE_IMAGE_UNITS",
    "webgl_params_MAX_CUBE_MAP_TEXTURE_SIZE",
    "webgl_params_MAX_FRAGMENT_UNIFORM_VECTORS",
    "webgl_params_MAX_RENDERBUFFER_SIZE",
    "webgl_params_MAX_TEXTURE_IMAGE_UNITS",
    "webgl_params_MAX_TEXTURE_SIZE",
    "webgl_params_MAX_VARYING_VECTORS",
    "webgl_params_MAX_VERTEX_ATTRIBS",
    "webgl_params_MAX_VERTEX_TEXTURE_IMAGE_UNITS",
    "webgl_params_MAX_VERTEX_UNIFORM_VECTORS",
    "webgl_params_MAX_VIEWPORT_DIMS",
    #"webgl_params_SHADING_LANGUAGE_VERSION",
    "webgl_params_extensions",
    "webgl2_params_extensions",

    ]
    # Combined hashes that must be cleared when individual params are blanked
    _combined_hashes = [
        "combined_webgl_extensions_hash",
        "combined_webgl2_extensions_hash",
    ]

    def __init__(self, dataValues):
        self.wgl_lie_originals = {}
        for param in self.webgl_params:
            self.wgl_lie_originals[param] = getattr(dataValues, param, None)
            setattr(dataValues, param, "")
        for h in self._combined_hashes:
            self.wgl_lie_originals[h] = getattr(dataValues, h)
            setattr(dataValues, h, "")
        self.applied_effect = True

    def revert(self, dataValues):
        for param, val in self.wgl_lie_originals.items():
            setattr(dataValues, param, val)

class webGLVendorRendererFilter(Filter):
    _vendor_attrs = ['webgl_vendor', 'webgl2_vendor', 'webgl_vendor_raw', 'webgl2_vendor_raw']
    _renderer_attrs = ['webgl_renderer', 'webgl2_renderer']

    @classmethod
    def affected_metrics(cls):
        return cls._vendor_attrs + cls._renderer_attrs

    def __init__(self, dataValues):
        self.originals = {}
        for attr in self._vendor_attrs + self._renderer_attrs:
            self.originals[attr] = getattr(dataValues, attr)

        for attr in self._vendor_attrs:
            setattr(dataValues, attr, "WebGL Vendor")
        for attr in self._renderer_attrs:
            setattr(dataValues, attr, "WebGL Renderer")
        self.applied_effect = True

    def revert(self, dataValues):
        for attr, val in self.originals.items():
            setattr(dataValues, attr, val)


class _ClientRectsRoundingFilter(Filter):
    """Base class for rounding clientrects JSON float values to N decimal places.

    Subclasses set _decimals to control rounding precision.
    Rounds all float values in the JSON objects stored in clientrects_*
    attributes, then recomputes the combined_clientrects_*_hash values.
    """
    _decimals = 0  # override in subclasses

    # Individual JSON-valued clientrects attributes
    _individual_attrs = (
        [f'clientrects_element_gbcr_{i:02d}' for i in range(1, 13)]
        + [f'clientrects_element_gcr_{i:02d}' for i in range(1, 13)]
        + [f'clientrects_range_gbcr_{i:02d}' for i in range(1, 13)]
        + [f'clientrects_range_gcr_{i:02d}' for i in range(1, 13)]
        + [f'clientrects_emoji_{i:02d}' for i in range(1, 7)]
        + ['clientrects_ghost_dimensions', 'clientrects_known_dimensions']
    )

    # Combined hash attributes that must be recomputed
    _combined_hash_attrs = [
        'combined_clientrects_element_gbcr_hash',
        'combined_clientrects_element_gcr_hash',
        'combined_clientrects_range_gbcr_hash',
        'combined_clientrects_range_gcr_hash',
        'combined_clientrects_emoji_hash',
    ]

    @classmethod
    def affected_metrics(cls):
        return list(cls._individual_attrs) + list(cls._combined_hash_attrs)

    @staticmethod
    def _round_json(json_str, decimals):
        """Parse a JSON string, round all float values, return canonical JSON."""
        if json_str == "None" or not json_str:
            return json_str
        try:
            obj = json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return json_str
        if isinstance(obj, dict):
            obj = {k: round(v, decimals) if isinstance(v, float) else v
                   for k, v in obj.items()}
        elif isinstance(obj, list):
            obj = [round(v, decimals) if isinstance(v, float) else v for v in obj]
        return json.dumps(obj, sort_keys=True, separators=(',', ':'))

    @staticmethod
    def _recompute_combined_hash(dataValues, prefix, count):
        """Recompute a combined_clientrects_*_hash from individual attrs."""
        vals = [None if getattr(dataValues, f'{prefix}_{i:02d}') == "None"
                else getattr(dataValues, f'{prefix}_{i:02d}')
                for i in range(1, count + 1)]
        s = json.dumps(vals, separators=(',', ':'))
        return hashlib.sha256(s.encode()).hexdigest()

    def __init__(self, dataValues):
        self.originals = {}
        self.applied_effect = False
        d = self._decimals

        # Round individual attributes
        for attr in self._individual_attrs:
            val = getattr(dataValues, attr)
            rounded = self._round_json(val, d)
            if rounded != val:
                self.originals[attr] = val
                setattr(dataValues, attr, rounded)
                self.applied_effect = True

        # Recompute combined hashes if any individual values changed
        if self.applied_effect:
            for hash_attr in self._combined_hash_attrs:
                self.originals[hash_attr] = getattr(dataValues, hash_attr)

            dataValues.combined_clientrects_element_gbcr_hash = self._recompute_combined_hash(
                dataValues, 'clientrects_element_gbcr', 12)
            dataValues.combined_clientrects_element_gcr_hash = self._recompute_combined_hash(
                dataValues, 'clientrects_element_gcr', 12)
            dataValues.combined_clientrects_range_gbcr_hash = self._recompute_combined_hash(
                dataValues, 'clientrects_range_gbcr', 12)
            dataValues.combined_clientrects_range_gcr_hash = self._recompute_combined_hash(
                dataValues, 'clientrects_range_gcr', 12)
            dataValues.combined_clientrects_emoji_hash = self._recompute_combined_hash(
                dataValues, 'clientrects_emoji', 6)

    def revert(self, dataValues):
        for attr, val in self.originals.items():
            setattr(dataValues, attr, val)


class clientRectsRound2Filter(_ClientRectsRoundingFilter):
    """Round clientrects values to 2 decimal places."""
    _decimals = 2


class clientRectsRound1Filter(_ClientRectsRoundingFilter):
    """Round clientrects values to 1 decimal place."""
    _decimals = 1


class clientRectsRound0Filter(_ClientRectsRoundingFilter):
    """Round clientrects values to 0 decimal places (integers)."""
    _decimals = 0


class canvasToSoftwareFilter(Filter):
    _canvas_attrs = [
        'canvas_canvasdata01', 'canvas_canvasdata02', 'canvas_canvasdata03',
        'canvas_canvasdata04', 'canvas_canvasdata05', 'canvas_canvasdata06',
        'canvas_canvasdata07', 'canvas_canvasdata08', 'canvas_canvasdata09',
        'canvas_canvasdata10', 'canvas_canvasdata11_webgl',
        'canvas_canvasdata12_fingerprintjs1', 'canvas_canvasdata13_fingerprintjs2',
    ]

    @classmethod
    def affected_metrics(cls):
        return list(cls._canvas_attrs) + ['combined_canvas_hardware_hash']

    def __init__(self, dataValues):
        self.cs_originals = {}
        for attr in self._canvas_attrs:
            self.cs_originals[attr] = getattr(dataValues, attr)
            setattr(dataValues, attr, getattr(dataValues, attr.replace('canvas_', 'canvassoftware_', 1)))

        # Update combined hash to match the software canvas values
        self.cs_originals['combined_canvas_hardware_hash'] = dataValues.combined_canvas_hardware_hash
        dataValues.combined_canvas_hardware_hash = dataValues.combined_canvas_software_hash

        self.applied_effect = True

    def revert(self, dataValues):
        for key, val in self.cs_originals.items():
            setattr(dataValues, key, val)
