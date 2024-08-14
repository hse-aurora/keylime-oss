import re

class Router:
    def __init__(self):
        self._routes = []
        self._controllers = {}

    # path-absolute = "/" [ segment-nz *( "/" segment ) ]
    # segment       = *pchar
    # segment-nz    = 1*pchar
    # pchar = unreserved / pct-encoded / sub-delims / ":" / "@"
    # unreserved = ALPHA / DIGIT / "-" / "." / "_" / "~"
    # pct-encoded = "%" HEXDIG HEXDIG
    # sub-delims = "!" / "$" / "&" / "'" / "(" / ")" / "*" / "+" / "," / ";" / "="

    UNRESERVED = "[A-Za-z0-9-._~]"
    PCT_ENCODED = "%[0-9A-Fa-f]{2}"
    SUB_DELIMS = "[!$&'()*+,;=]"
    PCHAR = f"{UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS}|[:@]"
    SEGMENT = f"(?:{PCHAR})*"
    SEGMENT_NZ = f"(?:{PCHAR})+"
    PATH_ABSOLUTE = f"\\/(?:{SEGMENT_NZ}(?:\\/{SEGMENT})*){{0,1}}"
    PATH_ABSOLUTE_REGEX = re.compile(f"^{PATH_ABSOLUTE}$")

    @classmethod
    def validate_abs_path(cls, path):
        if Router.PATH_ABSOLUTE_REGEX.match(path):
            return True
        else:
            return False

    @classmethod
    def capture_groups_from_path(cls, pattern, path):
        if not Router.validate_abs_path(pattern):
            raise InvalidPathOrPattern(f"Pattern {pattern} is not a valid URI")

        if not Router.validate_abs_path(path):
            raise InvalidPathOrPattern(f"Path {path} is not a valid URI")

        capture_groups = {}
        pattern_segments = pattern.split("/")
        path_segments = path.split("/")

        if len(pattern_segments) != len(path_segments):
            raise PatternMismatch()

        for i in range(len(pattern_segments)):
            delimiter_count = pattern_segments[i].count(":")

            # Multiple capture groups in a single segment (e.g., "/:one:two") would be
            # ambiguous, so this is not allowed. 
            if delimiter_count > 1:
                raise InvalidPathOrPattern(f"Pattern {pattern} contains multiple capture groups in a single segment")

            # If there are no delimiters in this segment of the pattern, the segment
            # contains no capture groups and should therefore match the corresponding
            # segment of the path.
            if delimiter_count <= 0:
                if pattern_segments[i] == path_segments[i]:
                    continue
                else:
                    raise PatternMismatch()

            parts = pattern_segments[i].split(":")
            prefix = parts[0]
            group_name = parts[1]

            # A capture group delimiter must be followed by a name (e.g., "/:/example" is not allowed).
            if len(group_name) <= 0:
                raise InvalidPathOrPattern(f"Pattern {pattern} contains a capture group with no name")

            # Any substring that precedes a capture group in a path segment should
            # match the corresponding substring in the pattern verbatim.
            if path_segments[i][0:len(prefix)] != prefix:
                raise PatternMismatch()

            captured_value = path_segments[i][len(prefix):]

            # A capture group should capture at least one character in order for the
            # pattern to be considered matching.
            if len(captured_value) <= 0:
                raise PatternMismatch()

            capture_groups[group_name] = captured_value

        return capture_groups

    @classmethod
    def pattern_matches_path(cls, pattern, path):
        try:
            Router.capture_groups_from_path(pattern, path)
        except PatternMismatch:
            return False
        except RouterError:
            raise

        return True

    def append_route(self, method, pattern, controller, action):
        if controller in self._controllers:
            controller_inst = self._controllers[controller]
        else:
            controller_inst = controller()
            self._controllers[controller] = controller_inst

        route = {'method': method.lower(), 'pattern': pattern, 'controller': controller, 'action': action}
        self.routes.append(route)

    @property
    def routes(self):
        return self._routes

    # @routes.setter
    # def routes(self, routes):
    #     self._routes = routes

    @property
    def controllers(self):
        return self._controllers

class RouterError(Exception):
    pass

class InvalidPathOrPattern(RouterError):
    pass

class PatternMismatch(RouterError):
    pass

class ActionMissing(RouterError):
    pass