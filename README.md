![version](https://img.shields.io/badge/version-18%2B-EB8E5F)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm&color=blue)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-window-control-v2)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-window-control-v2/total)

# 4d-plugin-window-control-v2

Controls a native macOS window's title-bar buttons, its "document edited" indicator, its proxy (represented-file) icon, and its minimized/miniaturized state, by driving Cocoa's `NSWindow` directly. Button states are read and written as `Longint`, and the icon is read and written as a `Picture`.

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
