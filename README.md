# CuteMica

CuteMica provides a fast, opaque, wallpaper-derived Mica Alt material for
PySide6 applications. The renderer, material recipe, cache, and Qt presenter are
shared across platforms. Windows establishes the reference CuteMica appearance;
Linux and macOS reproduce the same output from their platform wallpaper and
display metadata.

CuteMica does not enable a native system backdrop, capture the desktop, or use a
window-decoration framework. It paints a crop of an asynchronously generated,
fully opaque per-screen `QPixmap` during window movement.

## Runtime dependencies

- PySide6 Essentials for application, theme, display, image, and widget integration.
- Pillow for wallpaper decoding, placement reconstruction, and resizing.
- NumPy for the material blur and color pipeline.
- PyObjC Cocoa bindings on macOS for per-display wallpaper metadata.

No window-decoration, themed-widget, native-graphics, or system-backdrop
framework is a CuteMica runtime dependency.

## Setup

On Windows, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The equivalent cross-platform installation is:

```text
python -m venv .venv
python -m pip install -e ".[dev]"
```

## Launch the demo

Windows, macOS, GNOME-family desktops, KDE Plasma, MATE, XFCE, and LXQt can
discover supported image wallpapers:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1
```

Every platform can launch with an explicit wallpaper, including Wayland and
desktop environments without an automatic provider:

```text
python -m cutemica.demo.main --wallpaper /path/to/wallpaper.png
```

Use the theme selector to follow the system or force light or dark mode. Moving
the window only selects and paints a desktop-registered crop from the cached
material. Regeneration occurs when the wallpaper, theme, display topology, or
recipe changes.

System theme following uses the native Qt signal on Windows and macOS. Linux
reads the active desktop setting for GNOME, Cinnamon, MATE, XFCE, KDE Plasma,
and LXQt, then monitors it asynchronously. Settings queries never run during
painting or window movement.

Wallpaper metadata is polled at low frequency outside movement and paint paths.
The shared change detector tracks both source metadata and file revisions, so a
provider can publish a new path or update a stable cache file. Windows reads the
current per-monitor image through `IDesktopWallpaper`, including the current
image selected by a Windows slideshow. GNOME selects its light- or dark-specific
URI, KDE Plasma publishes one source per screen and exposes the current image
saved by its slideshow backend, and macOS reads source, scaling, clipping, and
fill-color metadata for each AppKit screen. Live/video wallpapers and
time-selected frames within dynamic image formats are outside the current
provider contract.

X11, Windows, and macOS expose global window geometry and provide
desktop-registered material. Standard Wayland clients do not receive their
global top-level position; CuteMica reports `screen-local` registration there
and uses a stable screen-local material rather than inventing coordinates.

## Motion presentation

Move events publish one internally consistent native-client/local-size snapshot
and synchronously present the cached material. Smooth subpixel sampling
preserves all four motion phases of a quarter-resolution texture. A pure slice
planner intersects displays in native physical desktop coordinates, then maps
the targets into the current widget paint space. A window crossing displays
therefore uses both cached materials without a whole-window screen switch,
fallback gap, or Qt mixed-DPI anchor jump. Outer window edges retain one source
texel of bilinear-filter support, so wallpaper features enter continuously
instead of appearing late at the edge of a moving window.

The hot path performs no wallpaper/display query, wallpaper decode, composition,
blur, material generation, or large allocation. Windows reads the native client
rectangle once per movement/resize presentation using standard-library Win32
bindings; 10,000 invisible-window reads measured 0.0025 ms median and 0.0026 ms
p95. Paint timing uses a fixed 180-sample window. Worker-produced images become
implicitly shared `QPixmap` textures on the GUI thread, which lets Qt use its
optimized backing-store draw path without duplicating the texture between the
cache and presenter.
The LRU cache retains at most one current material per display. During
regeneration, the presenter keeps the previous generation visible until each
replacement is ready.

At a physical monitor boundary, generation borrows only the neighboring
wallpaper pixels reachable by the active blur kernel. This removes the reflected
edge cut while preserving byte-identical material beyond that finite support.
The halo is discarded before caching, so drag-time memory and painting cost do
not increase.

Run the repeatable renderer and real-widget benchmarks with:

```text
cutemica-benchmark-motion --frames 2000 --p95-budget-ms 1.5
cutemica-benchmark-widget-motion --frames 2000 --p95-budget-ms 1.5
cutemica-benchmark-native-drag --frames 600 --stability-frames 96
```

The renderer benchmark draws into an offscreen `QImage`. The widget benchmark
drives `PortableMicaBackdrop` through Qt's offscreen platform and refuses to run
on a desktop platform plugin. Neither benchmark opens or moves a desktop
window. Across five 2,000-frame runs after mixed-DPI intersection handling, the
renderer measured 0.188–0.193 ms median and 0.226–0.455 ms p95; the real widget
path measured 0.199–0.219 ms median and 0.243–0.484 ms p95. The worst frames
were 2.644 ms and 2.113 ms, respectively, below the 6.94 ms budget for 144 Hz
presentation.

The native-drag probe creates an opacity-zero Qt tool window on a real desktop
platform, drives actual native move events and widget backing-store paints, and
captures only its own material widget. It verifies exact global translation on
Windows, X11, and macOS, stable screen-local output on Wayland, unchanged
`QPixmap` cache identities, bounded timing storage, and zero regeneration or
fallback during movement. It never captures the desktop or other windows. The
default hosted-runner budgets are 10 ms for the complete move cycle, 2 ms for
geometry, and 5 ms each for presentation and paint; exact pixel registration is
still required.

## Reference contract

The versioned `mica-alt-v7-neighbor-halo` recipe defines CuteMica output.
The current Windows reference fixtures cover light and dark themes, mixed DPI,
negative display origins, span wallpaper placement, detailed artwork, and
letterboxed regions. Platform ports must reproduce the same recipe and geometry
contract rather than substituting a system-specific visual effect.

The material pipeline uses:

- Per-screen wallpaper reconstruction in physical-pixel geometry.
- Quarter-resolution center-linear reduction and the CuteMica speed kernel on
  1× displays.
- A validated half-resolution float blur path on scaled displays.
- Float32 luminosity and color blending with a single final 8-bit conversion.
- Atomic GUI-thread publication and cached movement-time painting.
- Finite adjacent-monitor blur halos that are cropped before publication, so
  spanned wallpaper transitions remain continuous without enlarging the cache.

## Verify

On Windows, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify.ps1
```

This checks formatting, linting, strict typing, the complete test suite, both
600-frame cached-motion benchmarks, and a portable GUI smoke sequence. Qt runs
the tests, benchmarks, and smoke sequence on its offscreen platform, so
automated verification never opens or moves a desktop window.

GitHub Actions repeats the deterministic renderer and Qt tests on Windows,
Ubuntu, Apple Silicon macOS, and Intel macOS. Native drag probes exercise the
Windows, X11, and Cocoa platform plugins plus isolated GNOME, Plasma, and
Cinnamon Wayland compositors. Separate jobs exercise real
GNOME/Cinnamon/MATE/XFCE/LXQt settings implementations. Each native macOS job changes
the hosted runner's AppKit wallpaper twice, verifies that the real CuteMica
provider and monitor publish the transition, and restores the original desktop
state. CI also builds and installs distribution artifacts and runs the real
CuteMica launch path inside isolated GNOME, Cinnamon, Plasma, MATE, XFCE, and
LXQt sessions across their supported X11 and Wayland modes. A relaxed
hosted-runner performance sentinel complements these compatibility jobs. The
1.5 ms performance gate remains tied to the reference workstation because
shared CI timing is inherently noisy.

## Code layout

- `src/cutemica/core`: wallpaper composition and material processing.
- `src/cutemica/providers`: isolated platform wallpaper and display discovery.
- `src/cutemica/widgets`: portable Qt presentation.
- `src/cutemica/viewport.py`: pure multi-display presentation geometry.
- `src/cutemica/performance`: offscreen renderer and widget measurements.
- `src/cutemica/demo`: dependency-free standard-window demonstration.
- `tests`: deterministic material, geometry, scheduling, theme, and widget tests.

Project architecture and file-size rules live in `AGENTS.md`. The portable
cross-platform contract lives in `initial_spec.txt`.
