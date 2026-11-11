# Window Control native ownership audit

## Provenance and complete tracked-source inventory

Baseline: `97289f110f7e9f89acdfe242098cb2d08e8b979e` (`master`).
Canonical guidance: `miyako/skills@e6b492fcb81e5e1a7f7db723594b420e63bf6eb9`,
`4d-skills/skills/4dplugin/SKILL.md`, read through the immutable GitHub API.
Issue: #3.

Both source and committed bundle manifests are blob
`d8d3e92b4780720ccead7dc7c47780e34c6bba69`. All seven commands are marked
thread-safe: SET ENABLED takes three Longints; Get enabled takes two Longints
and returns Longint; SET ICON takes Longint/Picture; Get icon takes Longint
and returns Picture; MINIATURIZE/DEMINIATURIZE take Longint; Is miniaturized
takes Longint and returns Longint. There are no text or array signatures.
The inventory includes internal and dormant code, not just exported commands.

| Tracked native surface | Build membership and ownership finding |
|---|---|
| `4DPlugin-Window-Control.cpp/.h` | Xcode and all four dormant MSBuild configurations. Seven main-process dispatcher commands operate on integer/picture parameters. SET ICON borrows its picture, releases the created native image, temporary NSImage/URL and leaves the input alive. Get icon transfers its newly created picture to the result and releases its temporary image destination/data/dictionary. No text-array transfer or owned-string alias is present in these command bodies. |
| `4D Plugin API/Classes/C_TEXT.cpp/.h` | Dormant: absent from both native projects. Owns an independent C++ string; already noncopyable. Copies input before mutation; scalar outputs use the content setter, not descriptor-transfer assignment. Explicit byte/UTF-16 lengths in conversion paths are retained. Path helpers are synthetic in the host. |
| `Classes/ARRAY_TEXT.cpp/.h` | Dormant in both projects. Copies borrowed array elements into C++ strings. Successful output insertion already transfers without post-transfer disposal. Its owned heap vector permitted shallow copy/assignment; those operations are now deleted, following C_TEXT. |
| `Classes/C_BLOB.cpp/.h` | Dormant in both projects. CBytes holds bytes by value; C_BLOB owns a heap CBytes. Shallow wrapper copy/assignment is now deleted. Replacement allocates/fills before releasing the caller's old handle, preserving it on allocation failure. |
| `Classes/C_LONGINT.cpp/.h`, `C_TYPES.h` | Dormant integer value wrapper and shared byte/UTF-16 string/vector aliases. All four actual wrapper implementations compile in the synthetic host. |
| `support/4DPlugin-JSON.cpp/.h` | Dormant: not listed in either project or called by the actual dispatcher. Four string setter overloads and one picture setter overwrite owning empties. Four property getters omit successful owning result/mismatch cleanup and inspect failed unspecified values. Stringify needs immediate copy/command error capture and separate argument/result cleanup. Matching collection handoff and object/collection setter transfer remain intact. |
| Complete `4DPluginAPI.c`, API/ABI headers and `.def` | SDK is compiled whole in both projects and the host, never replaced with fragments. Source says v14, Flags says v13; these are not verified upstream release identifiers. Windows `.def` exports FourDPackex, whose actual implementation initializes the callback then invokes PluginMain. SDK internals and ABI headers are unchanged. |
| `include/json/{allocator,assertions,autolink,config,features,forwards,json,reader,value,version,writer}.h` | Vendor JsonCpp declarations/templates, not alternate PA wrappers; neither application's current include graph uses JsonCpp. `a/libjsoncpp.a`, `lib/windows/jsoncpp.lib`, `lib/windows64/jsoncpp.lib` are opaque vendor binaries, unchanged and not behavior-certified. |
| Xcode project/shared scheme, `.sln`, `.vcxproj`, `.vcxproj.filters` | Only SDK and Window-Control.cpp are source members. Scheme launch/profile/archive use Deployment. No wrapper/helper was silently promoted into production membership by this patch. |
| Committed bundle, ZIP/DMG, `test/Project` methods/forms, database/logs/resources | Prebuilt artifacts and existing 4D fixture application are not run or modified. Native fixtures are public synthetic in-memory literals only. |

No CPicture wrapper, picture setBytes/createCopy converter, pointer-reference
wrapper constructor, worker or separate application callback implementation is
present in the complete tracked native/build inventory. CBytes::setBytes copies
into a vector; it does not allocate pictures. No byte-returning createCopy
converter requires a UTF-16-unit correction in this target. The two wrapper
copy defects are latent: explicit named copy probes demonstrate them; no
production copy call or exported-command crash reproduction is claimed.

SDK blobs are checked before every host build:

| File in `4D Plugin API/` | Git blob |
|---|---|
| `4DPluginAPI.c` | `62f745e91d81ef2c3c901c656ea8e175d3b173e8` |
| `4DPluginAPI.h` | `528bf1d2552df08d6a8b1bc95011a9b72934ad5c` |
| `4DPluginAPI.def` | `5bbdb82fb724b6f8e307feb01d9f158b802de89d` |
| `EntryPoints.h` | `da428d5f6ca23b0a30371c7288a01d29aa3c466a` |
| `Flags.h` | `7a5a35539f27430a3fd9cb711d6b789051316471` |
| `PrivateTypes.h` | `a3098cb662cdbc43ba574fdef72a059c4c6d1cd4` |
| `PublicTypes.h` | `9ae20b001bff9128f690fff3e6c3f873b6238333` |

Application/wrapper baseline blobs:

| File | Git blob |
|---|---|
| `4DPlugin-Window-Control.cpp` | `3725b37a8edd575826669493492ca6c3c42568c8` |
| `4DPlugin-Window-Control.h` | `9611f3781d117a37e7d53bacb7db0d32e70cedf9` |
| `support/4DPlugin-JSON.cpp` | `74c880fb70dccb2d707fc8372880ff5c3492de41` |
| `support/4DPlugin-JSON.h` | `3e1c00dfc1e62766e9b235576ffd4621da057022` |
| `Classes/ARRAY_TEXT.cpp` | `534855e0959020ce9a66cef08f8434799c174495` |
| `Classes/ARRAY_TEXT.h` | `cf8a458fc8519b824c726a59d346c44d4c26e845` |
| `Classes/C_BLOB.cpp` | `27bea3172ce90e4da339991c9b318a71ea8609b2` |
| `Classes/C_BLOB.h` | `d181534e5a2e9bd46de492a040c1538ed81bf45a` |
| `Classes/C_LONGINT.cpp` | `005b83a4aec2c1466b8b219cb27ab845eb58de91` |
| `Classes/C_LONGINT.h` | `71e24df633aed7155cba1ffddc07d6a1dfc12fa9` |
| `Classes/C_TEXT.cpp` | `45ea6432dff52b681a5c6a7cea58ad5fc15df66b` |
| `Classes/C_TEXT.h` | `6967390757db569ffcd3cfea8696bf14045cc748` |
| `Classes/C_TYPES.h` | `972cf3f597a8c21881a8c9aa69bc1699455be373` |

## Exact SDK contracts and surgical changes

CreateVariable (3920-4066) creates an owned empty string/picture; scalar setters
(4254-4259, 4280-4285) shallow-assign without releasing it. Five helper
destinations now begin Undefined. Their final ClearVariable still disposes
the transferred input; this is not blanket removal of scalar cleanup.
Object/collection initial null references have no corresponding empty-owner leak.

GetObjectProperty (636-651) and GetCollectionElement (586-600) explicitly
return owning variables to clear. The application has four property getters
and no collection-element wrapper. Each captures error immediately before
kind inspection/adoption, clears every successful non-handed-off result, and
preserves matching owning collection handoff. Failed returns can be unspecified
poison or raw fType 0; UnifyVarKind (1713-1735) maps raw 0 to Unistring, making
even a kind check before error capture unsafe.

Stringify invokes the same OB Copy command directly, preserving the returned
descriptor until its error and kind are checked. Successful mismatches are
cleared; failed unspecified values are not adopted. The successful copied
object becomes the independent synchronous argument, cleared after stringify
while its error is captured first. Successful stringify returns are separately
cleared after use, including mismatches; failed unspecified returns are not
read/cleared. The original borrowed object argument to OB Copy is not cleared.

Existing failure outputs remain: text unchanged, boolean/number/reference
getters false/zero/null; ob_get_a still reports property existence. No new
exception, worker throw or error channel is introduced. These dormant helpers
have no error-reporting interface, and cleanup can reset SDK last error.
That observability gap remains documented, not presented as new success/error
reporting. Arbitrary host failures and C++ allocation exceptions are not certified.

SetStringInArray (4933-4947) accepts Unicode kind, non-null data, index
0..fNbElements inclusive and non-null descriptor pointer; it disposes the old
element then shallow-transfers the input. Rejection retains caller ownership.
GetStringInArray (4738-4755) is borrowed. Accepted index zero, rejected
kind/index/data/descriptor, independent copies, repeated replacement, churn,
shrink and final cleanup are controls. The already-correct success transfer
is unchanged. PA_SetUnistring (289-299) forwards content to the engine instead.

## Isolated reproduction and measured results

Run only the narrow unsigned checks:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/tests -p 'test_ownership*.py'
PYTHONDONTWRITEBYTECODE=1 python3 .github/tests/test_repository_contract.py
actionlint .github/workflows/ownership.yml
```

The host compiles the complete unchanged SDK, all four actual wrapper sources,
the entire actual JSON helper and actual Window-Control dispatcher. ASan/UBSan
are enabled, excluding alignment for packed SDK ABI structs; macOS LSan is
disabled and explicit string/picture/handle/object/collection/platform owner
balances must all reach zero.

Forced-include stubs replace NSWindow/NSButton/NSImage/NSURL, CFURL path
functions, image encoding/data/dictionary/release boundaries, and SDK graphics
transforms before compilation. Synthetic byte buffers stand in for TIFF
encoding; no actual image/window operation occurs. Unknown engine and
Objective-C selectors fail closed. Before any dispatch, nm rejects real
graphics/UI/path/system/filesystem/network imports and Foundation classes
outside NSObject/NSString/NSMutableString. Only in-memory Foundation text
conversion is used. No private documents, settings, input capture/injection,
user files, platform discovery, native plugin install or 4D host is accessed.

All actual consumers also receive forced-Windows-helper-branch syntax-only
compilation with trap-only conversion declarations. The dispatcher has no
Windows implementation: this compilation does not invent one. It does not
validate Windows SDK/wchar_t/ABI behavior, execute Windows code, or reproduce
a Windows 4D crash.

The same final harness runs against sources extracted with
`git archive 97289f110f7e9f89acdfe242098cb2d08e8b979e`, without another checkout.
OWNERSHIP_SOURCE_ROOT selects that immutable directory. Baseline-only unsafe
copy/assignment probes additionally define OWNERSHIP_BASELINE_COPY=1.
The baseline test enforces exact named failure identities, not merely a
nonzero exit, and requires four ASan heap-use-after-free diagnostics.

| Group | Common cases | Baseline failures | Fixed failures |
|---|---:|---:|---:|
| Four string setters and picture setter | 33 | 17 | 0 |
| Four property getters | 64 | 39 | 0 |
| Stringify/copy success, mismatch, failure | 23 | 10 | 0 |
| Actual dispatcher, wrappers, arrays, failure predicates, controls, traits | 30 | 2 | 0 |
| Total common | 150 | 68 | 0 |
| Baseline-only unsafe copies/assignments | 4 | 4 ASan UAF | Not compiled on noncopyable fixed types |

Baseline: 154 runs, 82 pass, 72 fail. Fixed: 150 pass, zero failures.
Six repository preservation/workflow contract tests also pass. ASCII, BMP,
supplementary surrogate pairs and empty text cover both allocated and null
engine empties, exact UTF-16 units/UTF-8 bytes, capacity, termination and
independently copied content. Eight dispatcher cases cover modern, 15R3,
unsupported legacy and absent windows with both empty representations;
all seven commands execute against synthetic objects, including edited/default
button choices, miniature state and empty/nonempty synthetic icon returns.

Named failures include unreleased string/picture/reference owners,
`caller handle released after failed allocation`, invalid-kind UBSan,
`reading failed/non-string variable`, `stringify dead argument`, and four
ASan shallow-copy probes. Matching owning collection handoff, null-empty
setters, synchronous argument independence and the actual dispatcher are
passing baseline controls, not evidence that allocated empties are safe.
Logs/results are retained as session artifacts, not tracked executables.

## Deferred contracts and non-release boundary

SDK PA_ResizeArray (4566-4603) updates fNbElements even when SetHandleSize
fails; shrink may dispose elements before resize succeeds. ARRAY_TEXT trusts
that metadata. Wrapper array OOM/capacity preservation requires separate
SDK/host contract work and is explicitly not certified. Tests prove low-level
allocation/resize failure predicates, not array-wrapper OOM safety. Failed
string creation/unspecified host metadata, real image allocation/finalization
failure behavior and opaque vendor binaries remain outside the verified contract.

Existing workflows/scripts and project phases were read before validation.
Build and Bump version are manual-only. Xcode Deployment signs, packages,
notarizes/uploads; the shared launch/profile/archive actions select Deployment.
No project build, launch, tag, release, signing, notarization, binary packaging,
publication, manual dispatch or rerun is performed.
Repository metadata reports has_pages=false; Pages API returns 404; hook
inventory is empty. No automatic existing deployment trigger was found.

The new Ownership workflow is unsigned, read-only, path-filtered, push-only
on the exact audit branch and master. Full-history checkout supports immutable
baseline and existing preservation checks. Only the four explicitly fixed
native files were added to the existing preservation allowlist. SDK/ABI headers,
manifests, projects, release workflows, version metadata and binaries are unchanged.

The first CI run passed the fixed and baseline sanitizer steps but failed the
preservation step with `ModuleNotFoundError: No module named 'yaml'`. The
workflow now installs that existing test dependency, pinned PyYAML 6.0.3, into
an isolated runner-temporary virtual environment. No global installation or
application dependency change is needed; the failed run is not rerun.

Harness/helper prior art was read via immutable API from
`miyako/4d-plugin-unicode-normalize@88faf72ab80b31a07f3ba88f2baff1b75fa05640`.
This target's real window dispatcher, synthetic image/window boundaries,
complete native memberships and measured counts were established here rather
than copied from that repository.
