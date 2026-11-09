"""Source-only metadata, governed by the committed Bump header, not its buggy body."""

import argparse
from pathlib import Path
import plistlib
import re
from xml.parsers.expat import ExpatError


PROJECT = Path("Window Control for Mac.xcodeproj/project.pbxproj")
PLIST = Path("Info.plist")
LOCALIZED = Path("English.lproj/InfoPlist.strings")
SOURCE_PATHS = (PROJECT, PLIST, LOCALIZED)
AUTHORITY = "coordinated"
SETTING_COUNT = 6
KEYS = ("MARKETING_VERSION", "CURRENT_PROJECT_VERSION")
VERSION = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
BUILD_VERSION = r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){0,2}"
REFERENCES = {f"$({key})": key for key in KEYS}
REFERENCES.update({f"${{{key}}}": key for key in KEYS})
PROJECT_TOKEN = re.compile(
    r'/\*.*?\*/|//[^\r\n]*|"(?:\\.|[^"\\])*"|\$\([^)\r\n]*\)|\$\{[^}\r\n]*\}'
    r'|[^\s"=;{}(),/]+|[^\s]',
    re.DOTALL,
)
SETTING = re.compile(
    r'(?m)^([ \t]*(MARKETING_VERSION|CURRENT_PROJECT_VERSION)[ \t]*=[ \t]*)([^;\n]*)(;)'
)
LOCALIZED_TOKEN = re.compile(
    r'\s+|/\*.*?\*/|//[^\r\n]*|'
    r'(?P<key>"[A-Za-z_][A-Za-z_0-9]*"|[A-Za-z_][A-Za-z_0-9]*)'
    r'\s*=\s*"(?P<value>(?:\\.|[^"\\])*)"\s*;', re.DOTALL,
)
LOCALIZED_SHORT = re.compile(
    r'(?m)^([ \t]*(?:"CFBundleShortVersionString"|CFBundleShortVersionString)'
    r'[ \t]*=[ \t]*")([^"]*)("[ \t]*;[ \t]*)$'
)
LOCALIZED_INFO = re.compile(
    r'(?m)^([ \t]*(?:"CFBundleGetInfoString"|CFBundleGetInfoString)'
    r'[ \t]*=[ \t]*"Window Control for Mac version )'
    r'([^,"]*)(, Copyright 2021 miyako\."[ \t]*;[ \t]*)$'
)
PLIST_VERSION = re.compile(
    r"(<key>CFBundle(?:ShortVersionString|Version)</key>\s*<string>)([^<]*)(</string>)"
)


class UniqueDictionary(dict):
    def __setitem__(self, key, value):
        if key in self:
            raise ValueError(f"Duplicate source plist key: {key}")
        super().__setitem__(key, value)


def unquote(value):
    return value[1:-1] if value.startswith('"') and value.endswith('"') else value


def decode(data):
    for bom, encoding in ((b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be"),
                          (b"\xef\xbb\xbf", "utf-8")):
        if data.startswith(bom):
            return data[len(bom):].decode(encoding), bom, encoding
    return data.decode("utf-8"), b"", "utf-8"


def text(path):
    return decode(path.read_bytes())[0].replace("\r\n", "\n").replace("\r", "\n")


def rendered(path, transform):
    decoded, bom, encoding = decode(path.read_bytes())
    endings = re.findall(r"\r\n|\r|\n", decoded)
    updated = transform(decoded.replace("\r\n", "\n").replace("\r", "\n"))
    if updated.count("\n") != len(endings):
        raise ValueError("Metadata rewrite changed line structure")
    iterator = iter(endings)
    return bom + re.sub("\n", lambda _: next(iterator), updated).encode(encoding)


def localized_fields(value):
    offset = 0
    fields = UniqueDictionary()
    while offset < len(value):
        token = LOCALIZED_TOKEN.match(value, offset)
        if token is None:
            raise ValueError("Unsupported strings serialization")
        if token["key"] is not None:
            fields[unquote(token["key"])] = token["value"]
        offset = token.end()
    return fields


def expected_localized(version):
    return {
        "CFBundleShortVersionString": version,
        "CFBundleGetInfoString":
            f"Window Control for Mac version {version}, Copyright 2021 miyako.",
    }


def validate_localized(value, version, message):
    fields = localized_fields(value)
    if any(fields.get(key) != wanted for key, wanted in expected_localized(version).items()):
        raise ValueError(message)


def project_settings(project):
    tokens = [match for match in PROJECT_TOKEN.finditer(project)
              if not match[0].startswith(("/*", "//"))]
    fields = {key: [] for key in KEYS}
    for index, token in enumerate(tokens[:-1]):
        key = unquote(token[0])
        if key not in KEYS or tokens[index + 1][0] != "=":
            continue
        if index + 3 >= len(tokens) or tokens[index + 3][0] != ";":
            raise ValueError(f"Invalid source assignment for {key}")
        value = tokens[index + 2]
        fields[key].append((value.start(), value.end(), unquote(value[0])))
    for key in KEYS:
        count = SETTING_COUNT
        if AUTHORITY == "current" and key == "MARKETING_VERSION":
            count = 0
        if len(fields[key]) != count:
            raise ValueError(f"Expected {count} source assignments for {key}")
    return fields


def metadata(root, contents=None):
    def payload(path):
        return (root / path).read_bytes() if contents is None else contents[path]

    def normalized(path):
        return decode(payload(path))[0].replace("\r\n", "\n").replace("\r", "\n")

    fields = project_settings(normalized(PROJECT))
    values = {key: [value for _, _, value in assignments]
              for key, assignments in fields.items() if assignments}

    def resolve(key, index, seen=()):
        if key not in values or key in seen:
            raise ValueError("Invalid, cyclic or unresolved source version reference")
        value = values[key][index]
        if value in REFERENCES:
            return resolve(REFERENCES[value], index, (*seen, key))
        if not re.fullmatch(BUILD_VERSION, value):
            raise ValueError(f"{key} is invalid")
        return value

    resolved = {}
    for key in values:
        unique = {resolve(key, index) for index in range(SETTING_COUNT)}
        if len(unique) != 1:
            raise ValueError(f"{key} has drifted across configurations")
        resolved[key] = unique.pop()
    authority = "CURRENT_PROJECT_VERSION" if AUTHORITY == "current" else "MARKETING_VERSION"
    version = resolved[authority]
    if not re.fullmatch(VERSION, version):
        raise ValueError("Source display version must be strict canonical X.Y.Z")
    if AUTHORITY == "coordinated" and any(value != version for value in resolved.values()):
        raise ValueError("Coordinated version settings have drifted")
    try:
        plist = plistlib.loads(payload(PLIST), dict_type=UniqueDictionary)
    except (plistlib.InvalidFileException, ExpatError, UnicodeError) as exc:
        raise ValueError("Source Info.plist has invalid serialization") from exc
    if not isinstance(plist, dict):
        raise ValueError("Source Info.plist must be a dictionary")
    if "CFBundleShortVersionString" not in plist:
        raise ValueError("Required CFBundleShortVersionString is missing")
    serialized = list(PLIST_VERSION.finditer(normalized(PLIST)))
    if len(serialized) != 1 + ("CFBundleVersion" in plist):
        raise ValueError("Source plist versions must be editable XML strings")
    for key in ("CFBundleShortVersionString", "CFBundleVersion"):
        if key not in plist:
            continue
        value = plist[key]
        target = version if key == "CFBundleShortVersionString" or AUTHORITY == "coordinated" \
            else resolved["CURRENT_PROJECT_VERSION"]
        if not isinstance(value, str) or resolved.get(REFERENCES.get(value), value) != target:
            raise ValueError(f"{key} is invalid, unresolved or has drifted")
        if [m[2] for m in serialized if f"<key>{key}</key>" in m[1]] != [value]:
            raise ValueError(f"{key} has unsupported XML serialization")
    validate_localized(normalized(LOCALIZED), version,
                       "Localized source version is missing, invalid or has drifted")
    return version, resolved, fields, plist


def read(root=Path(".")):
    return metadata(Path(root))[0]


def verify_bundle(bundle, root=Path(".")):
    root = Path(root)
    version, resolved, _, source_plist = metadata(root)
    contents = Path(bundle) / "Contents"
    data = plistlib.loads((contents / "Info.plist").read_bytes(), dict_type=UniqueDictionary)
    if not isinstance(data, dict) or data.get("CFBundleShortVersionString") != version:
        raise ValueError("Built bundle display version differs from selected source")
    if ("CFBundleVersion" in source_plist) != ("CFBundleVersion" in data):
        raise ValueError("Built bundle build version differs from selected source")
    if "CFBundleVersion" in source_plist:
        value = source_plist["CFBundleVersion"]
        if data["CFBundleVersion"] != resolved.get(REFERENCES.get(value), value):
            raise ValueError("Built bundle build version differs from selected source")
    serialized = (contents / "Resources/English.lproj/InfoPlist.strings").read_bytes()
    decoded = None if serialized.startswith(b"bplist00") else decode(serialized)[0]
    if decoded is None or decoded.lstrip().startswith(("<?xml", "<plist")):
        localized = plistlib.loads(serialized, dict_type=UniqueDictionary)
    else:
        localized = localized_fields(decoded)
    if not isinstance(localized, dict) or any(
        localized.get(key) != wanted for key, wanted in expected_localized(version).items()
    ):
        raise ValueError("Built localized display differs from selected source")


def replace_spans(value, replacements):
    for start, end, new in sorted(replacements, reverse=True):
        value = value[:start] + new + value[end:]
    return value


def bump(mode, root=Path(".")):
    root = Path(root)
    current, _, fields, _ = metadata(root)
    index = ("major", "minor", "patch").index(mode)
    parts = list(map(int, current.split(".")))
    parts[index] += 1
    parts[index + 1:] = [0] * (2 - index)
    new = ".".join(map(str, parts))

    def project(value):
        replacements = []
        for key, assignments in fields.items():
            if AUTHORITY == "marketing" and key == "CURRENT_PROJECT_VERSION":
                continue
            for start, end, literal in assignments:
                if literal not in REFERENCES:
                    old = value[start:end]
                    replacements.append((start, end, f'"{new}"' if old.startswith('"') else new))
        return replace_spans(value, replacements)

    def plist(value):
        def replace(match):
            if match[2] in REFERENCES or (
                AUTHORITY == "marketing" and "<key>CFBundleVersion</key>" in match[1]
            ):
                return match[0]
            return f"{match[1]}{new}{match[3]}"
        return PLIST_VERSION.sub(replace, value)

    def localized(value):
        replacements = []
        for match in LOCALIZED_TOKEN.finditer(value):
            key = unquote(match["key"] or "")
            if key == "CFBundleShortVersionString":
                replacements.append((*match.span("value"), new))
            elif key == "CFBundleGetInfoString":
                start = match.start("value") + len("Window Control for Mac version ")
                replacements.append((start, start + len(current), new))
        return replace_spans(value, replacements)

    updates = {path: rendered(root / path, transform) for path, transform in (
        (PROJECT, project), (PLIST, plist), (LOCALIZED, localized),
    )}
    if metadata(root, updates)[0] != new:
        raise ValueError("Planned metadata bump does not advance source authority")
    for path, data in updates.items():
        (root / path).write_bytes(data)
    if read(root) != new:
        raise ValueError("Bumped metadata did not validate")
    return new


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--bump", choices=("patch", "minor", "major"))
    operation.add_argument("--verify-bundle", type=Path)
    args = parser.parse_args()
    if args.verify_bundle:
        verify_bundle(args.verify_bundle)
    else:
        print(bump(args.bump) if args.bump else read())
