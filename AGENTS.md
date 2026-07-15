# AGENTS.md

## Mission

CuteMica provides a high-performance, cross-platform PySide6 Mica Alt material.
The shared CuteMica renderer is the reference implementation on every platform.
Correct visual registration, predictable fallback behavior, responsiveness,
and maintainable architecture take priority over static screenshot tricks.

## Environment and commands

- Windows 11 and PowerShell are the primary development environment.
- Use the repository virtual environment for every Python command.
- Bootstrap with `powershell -ExecutionPolicy Bypass -File .\setup.ps1`.
- Launch with `powershell -ExecutionPolicy Bypass -File .\run_demo.ps1`.
- Run all gates with `powershell -ExecutionPolicy Bypass -File .\verify.ps1`.
- Do not run project tests, Ruff, or mypy through global Python.
- Use Windows paths and PowerShell syntax; do not introduce Bash-only scripts.

## Architecture

- Keep dependency direction explicit:
  - Public API: stable consumer-facing types and controllers.
  - Widgets: Qt presentation and paint integration.
  - Core: material generation, geometry, caching, scheduling, and theme policy.
  - Providers: operating-system wallpaper and display adapters.
- Platform providers may depend on core models. Core rendering must not depend
  on a platform provider or a window-decoration library.
- Runtime material generation reads wallpaper sources and never captures other
  windows or the desktop.
- Native physical coordinates and Qt device-independent coordinates are
  different types of data. Preserve their names and convert only at explicit
  screen-binding boundaries.
- Image decoding, reconstruction, blur, tint, and allocation stay outside paint
  and movement events. Movement may select and draw cached source rectangles.

## Small, focused source files

- Every source file owns one coherent concern and one primary reason to change.
- Target at most 250 non-blank source lines per hand-written module. Treat 300
  lines as a mandatory design review point and split before 350 lines unless the
  file is a declarative table, generated output, or a narrow native interface
  whose cohesion is clearer when kept together.
- A file must be split earlier when it mixes policy, I/O, rendering, widget
  composition, scheduling, or diagnostics, even if it is below the line target.
- Prefer one primary class per module. Small supporting value types may remain
  with their owner when they do not introduce a separate change reason.
- Do not create generic `utils.py`, `helpers.py`, or catch-all service modules.
  Name modules after the concern they own.
- Keep functions short enough that invariants and side effects are visible in
  one reading. Extract a named collaborator when a function begins coordinating
  unrelated stages.
- Complete refactors: update all call sites, remove obsolete paths, and avoid
  internal compatibility shims.

## Code quality

- Write expressive, self-documenting names and concise functions.
- Use inline comments only for non-obvious platform behavior or invariants.
- Add concise docstrings to public modules, classes, functions, and methods.
- Use strict typing for all production code. Avoid `Any`; isolate unavoidable
  untyped third-party or native boundaries behind typed adapters.
- Prefer immutable dataclasses for snapshots, recipes, requests, and cache
  entries. Keep the public material preset stable and versioned.
- Preserve exception context. Catch narrow exceptions and include actionable,
  structured context in logs.
- Never log full wallpaper paths by default; use a redacted name or hash.

## Material and performance rules

- The portable material is fully opaque.
- The reference recipe is versioned and testable. Optional visual stages remain
  disabled until cross-platform fixtures show that they improve the material.
- Never perform file I/O, wallpaper queries, image decoding, scaling, blur,
  tinting, full-screen allocation, or Python per-pixel loops during movement or
  paint.
- Keep the previous valid material visible during asynchronous regeneration and
  promote completed images to implicitly shared `QPixmap` textures and publish
  them atomically on the GUI thread.
- Movement publishes one native-client/local-size snapshot, synchronously
  presents the cached material, and uses smooth subpixel sampling. It must not
  regenerate material.
- Generation borrows adjacent-screen wallpaper only within the selected blur
  backend's finite support. Crop halos before publication so cached texture
  dimensions and the movement hot path remain unchanged.
- Spanning displays intersect in native physical desktop coordinates and paint
  one registered slice per screen in current widget coordinates. Do not derive
  Windows native position from Qt's transitional mixed-DPI anchor state or
  hard-switch the whole window.
- Profile before introducing GPU, Qt Quick, OpenCV, or native acceleration.
- Windows reference changes require explicit visual and performance fixtures;
  Linux and macOS must reproduce that same documented CuteMica output.

## Testing and verification

- Add or update tests with every behavior change.
- Keep tests deterministic and isolated. Use synthetic images for placement and
  geometry assertions.
- Cover success, failure, stale-result, theme-change, mixed-DPI, negative-origin,
  opacity, boundary continuity, unchanged material outside neighbor support, and
  no-regeneration-on-move behavior.
- Prefer real Qt behavior through pytest-qt where practical. Mock only operating
  system and capture boundaries.
- Cross-platform visual fixtures must record platform, display scale, wallpaper
  placement, theme, recipe version, and expected CuteMica output.
- Required gates are:
  - `.\.venv\Scripts\ruff.exe format --check .`
  - `.\.venv\Scripts\ruff.exe check .`
  - `.\.venv\Scripts\mypy.exe --strict src tests`
  - `.\.venv\Scripts\python.exe -m pytest -q`
- A launch smoke test is required before reporting the demo complete.
- Performance tests and GUI smoke checks must use Qt's offscreen platform and
  must not open or move a real desktop window during automated verification.
- The offscreen motion benchmark must keep p95 cached presentation at or below
  1.5 ms on the reference workstation. Enforce the same budget through the real
  offscreen `PortableMicaBackdrop` path.

## Documentation

- Describe the product directly as it exists now.
- Keep setup, launch, controls, current limitations, and verification commands
  accurate in `README.md`.
- Do not describe removed approaches or imaginary backend choices as user-facing
  product behavior.

## Definition of done

- The requested behavior works through the real launch path.
- Source ownership and file size rules remain satisfied.
- New behavior is typed, documented where public, observable, and tested.
- Formatting, lint, strict typing, tests, and launch smoke all pass.
- Known limitations are reported precisely without overstating parity.
