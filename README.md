![version](https://img.shields.io/badge/version-18%2B-EB8E5F)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm&color=blue)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-window-control-v2)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-window-control-v2/total)

# 4d-plugin-window-control-v2

Controls a native macOS window's title-bar buttons, its "document edited" indicator, its proxy (represented-file) icon, and its minimized/miniaturized state, by driving Cocoa's `NSWindow` directly. Button states are read and written as `Longint`, and the icon is read and written as a `Picture`.

## Manual version and release workflows

There are exactly two independent manual release Actions entries:

| Entry | Built-in ref selector | Custom inputs | Effect |
|---|---|---|---|
| **Bump version** | Select a branch | One required `mode`: `patch` (default), `minor`, or `major` | Commits source metadata to that branch only |
| **Build** | Select a branch or tag | None | Builds the selected immutable commit and creates a new release |

Bump never creates a tag, starts Build, or dispatches another workflow. Run Build
separately after selecting the desired bumped branch. Build can also release an
already-versioned source commit; it does not increment its version. Neither entry
is triggered by branch pushes, PRs, or tag pushes. No default-branch-only restriction
is added. All checkouts use the dispatch's `github.sha`, not a moving branch name.

The separate **Ownership** workflow runs unsigned synthetic regressions on relevant
pushes to `master` and the audit branch. It does not build the plugin, manipulate
real windows/images, sign, package, or publish anything. See the
[native ownership audit](.github/tests/ownership-audit.md) for source provenance,
baseline reproduction, dormant-helper scope and remaining contract limits.

### Source authority and preservation

The committed Bump header at intake
`c7dcedc8af73dfc03753ae4698eb8e24158afc90` explicitly coordinates
`MARKETING_VERSION`, `CURRENT_PROJECT_VERSION`, and source plist versions. The
earlier marketing-only/current-fallback headers are superseded by the explicit
coordination change `ab6b4cbe4c3458d819906615562ec4035ceee816`; that commit's
message also confirms the contract. Its marketing-only implementation was a bug,
not authority to preserve stale coordinated settings.

The authoritative files are `Window Control for Mac.xcodeproj/project.pbxproj`
(six assignments per version setting: target and project, each with Development,
Deployment, and Default), `Info.plist`, and the **source**
`English.lproj/InfoPlist.strings`. Xcode's Resources phase copies that localization
to `Contents/Resources/English.lproj/InfoPlist.strings`. The migration does not
increment the intake version: it repairs only six stale current-version tokens
and the two copied-source localization tokens to the existing marketing/source
short version, `2.2.5`. The source plist is unchanged.

Source `CFBundleShortVersionString` is required. Only `CFBundleVersion` is optional;
its original absence remains absence. Known `$(MARKETING_VERSION)`,
`${MARKETING_VERSION}`, `$(CURRENT_PROJECT_VERSION)`, and
`${CURRENT_PROJECT_VERSION}` references remain references. Invalid, cyclic,
unresolved, duplicate, noncanonical or drifted metadata fails before a bump writes.
Edits address actual value-token spans, preserving encoding/BOM, UTF-16 endian,
individual mixed line endings, modes, quotes, and unrelated bytes. The helper also
tests historical marketing-only/current-fallback policies: independent current/build
metadata stays independent even when numerically equal to marketing at intake;
those historical policies are not the live coordinated contract.

Prebuilt bundle metadata (including its stale UTF-16 localization), Windows
payload, libraries, frameworks, resources, manifests, 4D database/project/schema,
and native configuration are not source version authority and are not rewritten.
The actual original workflow has only a macOS native job, notwithstanding its old
Windows-first comment and dormant `.sln`/`.vcxproj` files. No Windows build,
artifact merge, PowerShell, CMD, i386 rejection, or runtime-dylib gate is invented.
The dormant Windows project's Release/x64 output remains exactly
`test/plugins/Window Control.bundle/contents/windows64/Window Control.4DX`
with toolset `v140`; it is not an Actions output.

Build retains Default configuration, `arm64 x86_64`, deployment override `10.13`,
frameworks/dependencies/resources, signing identity lookup, strict signature
verification, archive formats, secret **names**, and the notary/staple sequence.
Default already sets `SYMROOT` to `test/Plugins`, but unlike Development/Deployment
does not override `CONFIGURATION_BUILD_DIR`; the workflow explicitly pins that
directory to `$PWD/test/Plugins` so verification uses one canonical output.
Only generated executable/plist/copied localization/signature and target-specific
intermediates are removed. Whole bundles, Resources, Windows payloads, dependencies,
and Default sibling resources are never deleted. Fresh built plist/localization
(XML, binary, or UTF-16 strings) must equal selected source; each required
architecture must be an exact token, without an invented two-slice-only limit.
Both notary commands must exit successfully **and** return JSON `Accepted`, and
stapling must succeed before publication.

### Guarded branch updates and create-only publication

Bump requires clean exact selected HEAD and matching remote branch SHA. It creates
one nonempty source-only single-direct-parent commit with the Copilot co-author
trailer. The mandatory executable pre-push guard is checked initially and after
the final remote read. It validates receive-pack's advertised old SHA, exact ref,
literal new SHA, HEAD, parent and exactly one update, rejecting advance, rewind,
deletion and zero-update/same-result races. Push is nonforce, with both
`push.followTags=false` and `--no-follow-tags`, even if local annotated tags exist.

Build uses one constant cross-ref publication concurrency group, with cancellation
disabled. Before native work, authenticated, fully paginated release enumeration
(including drafts) and exact remote tag absence must both succeed. After all
native/sign/notary/staple gates, those checks repeat. Authentication, 404, network,
malformed-response and later-page failures are errors, never interpreted as
absence. Selected HEAD and unchanged source/config are checked at both stages.
Initial preflight requires a globally clean checkout; final `check` and `publish`
allow only the tracked generated executable, plist, copied localization and
signature dirt. They never reset those generated bytes to fake a clean checkout.

Publication performs a separate create-only tag-ref POST at selected SHA, verifies
the advertised remote SHA, then POSTs a **new public, non-prerelease** release
with explicit tag/name/target and empty body, followed by separate exact zip/dmg
uploads to its newly returned ID. The original softprops configuration specified
only tag, name and files: no prose or generated release notes are added.
There is no combined `gh release create`, existing-release reuse, PATCH, DELETE,
overwrite/clobber, rollback or automatic retry.

**Recovery:** any failure stops the job and retains the created tag, release and
already uploaded assets. Read the failed step's logs and inspect those objects,
their SHA, new release ID and asset names before taking action. A failure or
ambiguous response may already have created remote state. Do not redispatch Build
expecting it to repair an existing version or delete/recreate anything. A maintainer
must decide how to handle retained partial state outside this automation; a safe
new publication uses Bump on the desired branch and a separately selected Build
of a new version. Branch-race failures require inspecting the branch and selecting
its current commit again, not forcing a push.

### Offline verification and pinned reference provenance

Run `actionlint .github/workflows/*.yml` and
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/tests -v`
(Python 3 with PyYAML). Tests use temporary local bare Git remotes, fake `gh`,
and literal extracted workflow Bash with a closed PATH of native stubs; they do
not perform a native build, use signing credentials, contact notarization/4D,
dispatch Actions, or mutate production tags/releases. There are no absent-platform
test skips or CMD adapters. Preservation fixtures read immutable intake history,
not a mutable original-HEAD alias, and the same suite works after genuine bumps.

All workflows, helpers, hooks and tests were read at these six immutable references
and adapted to this repository's authority, counts, topology and paths:

| Repository | Commit |
|---|---|
| `miyako/4d-plugin-native-encoding-detection` | `c42ca565857f674bde5ea6ed3435c87375eda4a7` |
| `miyako/4d-plugin-file-information` | `19848973601acfd3a2b5070230fa40cdc7e4edb2` |
| `miyako/4d-plugin-common-string-algorithm` | `2606a68201866ec9fcbb38b51462d79215f504ef` |
| `miyako/4d-plugin-window-button` | `3f14facb9aaaaff0e22eeb8e07531163680c3a8a` |
| `miyako/4d-plugin-raw-picture-data` | `8144537fdc8dcc3d0c053dfe97aff0a8c0c3a6f9` |
| `miyako/4d-plugin-PRNG` | `522f62e1e9f388be0f3f226c1d4c39362dad2491` |

## Commands

| Command | Returns | Purpose |
|---|---|---|
| [WINDOW SET ENABLED](#window-set-enabled) | — | Enable/disable a window's close, minimize, or zoom button, or set its "document edited" indicator |
| [WINDOW Get enabled](#window-get-enabled) | Longint | Read the enabled state of a window's close, minimize, or zoom button, or its "document edited" indicator |
| [WINDOW SET ICON](#window-set-icon) | — | Set a window's title-bar proxy icon |
| [WINDOW Get icon](#window-get-icon) | Picture | Read a window's title-bar proxy icon |
| [WINDOW MINIATURIZE](#window-miniaturize) | — | Minimize (miniaturize) a window to the Dock |
| [WINDOW DEMINIATURIZE](#window-deminiaturize) | — | Restore a minimized window from the Dock |
| [WINDOW Is miniaturized](#window-is-miniaturized) | Longint | Check whether a window is currently minimized |

**Platforms:** macOS only (Intel and Apple Silicon). There is no Windows implementation — this plugin does not expose these commands on Windows at all.

---

## Requirements & platform notes

- **Requires 4D v18 or later** (per the plugin's own version badge).
- **macOS only.** There is no Windows build of this plugin; don't expect these commands to be available in a Windows-hosted 4D application.
- **Every command silently does nothing if the window reference doesn't resolve to a currently open window.** None of the seven commands raise a 4D error for an invalid, closed, or out-of-range window reference — traced directly from the source, there is no error-throwing call anywhere in the plugin. Concretely:
  - The two "set"-style commands (`WINDOW SET ENABLED`, `WINDOW SET ICON`) and the two minimize commands (`WINDOW MINIATURIZE`, `WINDOW DEMINIATURIZE`) simply do nothing.
  - The three "get"-style commands (`WINDOW Get enabled`, `WINDOW Get icon`, `WINDOW Is miniaturized`) return a safe default instead of an error: `0` for the two Longint-returning commands, and an empty `Picture` for `WINDOW Get icon`. **This default-return behavior is forward-looking**: it reflects a fix applied during code review to guarantee these commands always return a value; confirm it's present in whatever compiled binary you're actually running before relying on it, since the original source had a path where two of these three commands could fail to return a value at all when given an invalid window reference.
- **The window reference (`window`, parameter 1 in every command) is a 4D window number** — the same kind of value returned by 4D's own window commands (e.g. `Current form window`, or the number returned when you open a window). This isn't a pointer or handle you construct yourself.
- **The button constant (parameter 2 of `WINDOW SET ENABLED` / `WINDOW Get enabled`) has no named 4D constants shipped with this plugin** — the manifest declares no constants, so you pass the literal integer values documented below. Any value other than `0`, `1`, or `2` is treated as a request to read/write the window's **document-edited indicator** (the small dot 4D shows in a window's close button when a document has unsaved changes) rather than a button — so `3` and any other out-of-range value all land on that same behavior.
- **All commands are safe to call from any process** — the plugin dispatches every one of them onto 4D's main process internally, so you don't need to wrap calls in your own main-process check.

---

## WINDOW SET ENABLED

### Syntax

```4d
WINDOW SET ENABLED(window; button; enabled)
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | The window number, as returned by 4D's own window commands. |
| `button` | Longint | Which title-bar element to change: `0` = close button, `1` = minimize button, `2` = zoom (full screen/maximize) button. Any other value sets the document-edited indicator instead (see note above). |
| `enabled` | Longint | `1` to enable the button (or mark the document as edited, for the document-edited case), `0` to disable it (or clear the edited mark). |

### Description

Enables or disables one of a window's three standard title-bar buttons (close, minimize, zoom), or toggles the window's document-edited indicator, matching Cocoa's `NSWindow` button-enabling behavior. Disabling a button dims it and makes it unclickable, but doesn't hide it.

If `window` doesn't resolve to a currently open window, the command does nothing — no error is raised.

### Example

```4d
var $window : Longint
$window:=Current form window

// disable the close button so the user can't close this window directly
WINDOW SET ENABLED($window; 0; 0)

// disable minimize and zoom too, leaving only a plain title bar
WINDOW SET ENABLED($window; 1; 0)
WINDOW SET ENABLED($window; 2; 0)
```

```4d
// mark the current window as having unsaved changes
WINDOW SET ENABLED(Current form window; 3; 1)
```

---

## WINDOW Get enabled

### Syntax

```4d
$state:=WINDOW Get enabled(window; button)
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | The window number. |
| `button` | Longint | Which title-bar element to query: `0` = close, `1` = minimize, `2` = zoom. Any other value queries the document-edited indicator instead. |
| Result | Longint | `1` if the button is enabled (or the document-edited flag is set), `0` otherwise. |

### Description

Reads back the current enabled state set by `WINDOW SET ENABLED`, or the window's document-edited state.

If `window` doesn't resolve to a currently open window, the command returns `0` rather than raising an error — this is indistinguishable from "the button is genuinely disabled," so don't use this command to detect whether a window reference is valid.

### Example

```4d
var $window; $isEnabled : Longint
$window:=Current form window
$isEnabled:=WINDOW Get enabled($window; 0)

If ($isEnabled=1)
	ALERT("The close button is currently enabled.")
End if
```

---

## WINDOW SET ICON

### Syntax

```4d
WINDOW SET ICON(window; icon)
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | The window number. |
| `icon` | Picture | The image to use as the window's title-bar proxy icon. |

### Description

Sets a window's proxy icon — the small icon macOS shows next to a window's title (also draggable, and shown when Command-clicking the title). This is the same UI element normally driven by giving a document window a represented file URL.

The plugin accepts whatever picture format `icon` is currently stored as; internally it's converted to a native `CGImage` before being applied, so you don't need to convert the picture yourself first.

If `window` doesn't resolve to a currently open window, the command does nothing.

### Example

```4d
var $window : Longint
var $icon : Picture

$window:=Current form window
READ PICTURE FILE("/Users/me/Desktop/icon.png"; $icon)
WINDOW SET ICON($window; $icon)
```

---

## WINDOW Get icon

### Syntax

```4d
$icon:=WINDOW Get icon(window)
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | The window number. |
| Result | Picture | The window's current title-bar proxy icon. |

### Description

Reads back a window's proxy icon. Internally, the returned picture is always encoded as TIFF, regardless of the format `WINDOW SET ICON` was originally given — traced directly from the plugin's source, which builds the return value through a TIFF image destination rather than preserving the original format. 4D's `Picture` type abstracts over this for you, so you generally don't need to care, but if you ever inspect the raw picture data (e.g. via a picture-format-conversion command) expect TIFF, not PNG/JPEG/whatever you originally set.

**Returns an empty picture, not an error, in two cases:** the window has no custom proxy icon set (the default state for most windows — most windows never call `WINDOW SET ICON`), or `window` doesn't resolve to a currently open window. These two cases are indistinguishable from the return value alone.

### Example

```4d
var $window : Longint
var $icon : Picture

$window:=Current form window
$icon:=WINDOW Get icon($window)

If (Picture width($icon)=0)
	ALERT("This window has no custom proxy icon set.")
End if
```

---

## WINDOW MINIATURIZE

### Syntax

```4d
WINDOW MINIATURIZE(window)
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | The window number. |

### Description

Minimizes (miniaturizes) a window to the Dock, identical to clicking its yellow minimize button — including the genie/scale window-minimize animation.

Note that `WINDOW SET ENABLED(window; 1; 0)` (disabling the minimize *button*) does not prevent this command from minimizing the window programmatically — the two are independent.

If `window` doesn't resolve to a currently open window, the command does nothing.

### Example

```4d
WINDOW MINIATURIZE(Current form window)
```

---

## WINDOW DEMINIATURIZE

### Syntax

```4d
WINDOW DEMINIATURIZE(window)
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | The window number. |

### Description

Restores a minimized window from the Dock back to its previous position on screen, identical to clicking its Dock icon.

If `window` doesn't resolve to a currently open window (which, in practice, also covers "the window was never minimized"), the command does nothing.

### Example

```4d
var $window : Longint
$window:=Current form window

If (WINDOW Is miniaturized($window)=1)
	WINDOW DEMINIATURIZE($window)
End if
```

---

## WINDOW Is miniaturized

### Syntax

```4d
$miniaturized:=WINDOW Is miniaturized(window)
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | The window number. |
| Result | Longint | `1` if the window is currently minimized, `0` otherwise. |

### Description

Reports whether a window is currently minimized to the Dock. Also returns `0` (rather than raising an error) if `window` doesn't resolve to a currently open window, so this command can't distinguish "not minimized" from "not a real window" either.

### Example

```4d
If (WINDOW Is miniaturized(Current form window)=1)
	ALERT("This window is minimized.")
End if
```

---

## Error handling & troubleshooting

- **No command in this plugin ever raises a 4D error.** An invalid, closed, or out-of-range window number is always handled silently: "set"-style commands (`WINDOW SET ENABLED`, `WINDOW SET ICON`, `WINDOW MINIATURIZE`, `WINDOW DEMINIATURIZE`) do nothing, and "get"-style commands (`WINDOW Get enabled`, `WINDOW Get icon`, `WINDOW Is miniaturized`) return a safe default (`0`, or an empty picture) instead. Don't use any of these return values to test whether a window reference is valid — check with your own window-tracking logic first.
- **`WINDOW Get icon` returning an empty picture is normal**, not just a failure signal — most windows never have a custom proxy icon set via `WINDOW SET ICON`, so an empty result is the expected case for an ordinary window, not evidence something went wrong.
- **The proxy icon comes back as TIFF**, regardless of the format you originally passed to `WINDOW SET ICON`. If you round-trip the picture through a format-specific operation, account for this.
- **The document-edited indicator and "button 3" are the same thing.** `button=3` (or any value other than `0`/`1`/`2`) in both `WINDOW SET ENABLED` and `WINDOW Get enabled` targets the window's document-edited dot, not a fourth button — there is no fourth title-bar button on macOS.
- **These commands have no effect on Windows** — there's no Windows build of this plugin at all; don't call these commands from Windows-hosted code paths.
- **Minimum 4D version is 18.** Older versions aren't supported by this build.

---

## Quick reference

```4d
var $window : Longint
$window:=Current form window

// buttons
WINDOW SET ENABLED($window; 0; 0)   // disable close
WINDOW SET ENABLED($window; 1; 1)   // enable minimize
WINDOW SET ENABLED($window; 2; 1)   // enable zoom
$enabled:=WINDOW Get enabled($window; 0)

// document-edited indicator
WINDOW SET ENABLED($window; 3; 1)
$edited:=WINDOW Get enabled($window; 3)

// icon
WINDOW SET ICON($window; $myIcon)
$icon:=WINDOW Get icon($window)

// minimize state
WINDOW MINIATURIZE($window)
If (WINDOW Is miniaturized($window)=1)
	WINDOW DEMINIATURIZE($window)
End if
```
