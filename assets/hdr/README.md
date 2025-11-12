# HDR Environment Inventory

This directory stores the canonical high dynamic range (HDR) environment maps that feed
image-based lighting for PneumoStabSim Professional. Keeping the authoritative copies
here ensures that lighting presets stay consistent between the editor, automated tests
and packaged builds.

## Required production HDRIs

`assets/hdr/hdr_manifest.json` mirrors the HDR panorama list from the technical
specification. The manifest powers automated checksum validation and should be
treated as the source of truth for licensing data. The table below summarises the
expected files and their primary usage inside PneumoStabSim:

| File | Resolution | Source | License | Attribution | Primary use |
| --- | --- | --- | --- | --- | --- |
| `abandoned_factory_canteen_01_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/abandoned_factory_canteen_01) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Abandoned factory cafeteria interior. |
| `abandoned_greenhouse_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/abandoned_greenhouse) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Overgrown greenhouse with diffused lighting. |
| `abandoned_hall_01_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/abandoned_hall_01) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Tall abandoned hall with skylight. |
| `abandoned_hopper_terminal_04_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/abandoned_hopper_terminal_04) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Industrial terminal exterior with overcast light. |
| `adams_place_bridge_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/adams_place_bridge) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Urban bridge underpass. |
| `aerodynamics_workshop_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/aerodynamics_workshop) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Wind tunnel workshop interior. |
| `aircraft_workshop_01_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/aircraft_workshop_01) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Aircraft maintenance hangar. |
| `approaching_storm_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/approaching_storm) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Outdoor field with dramatic skies. |
| `auto_service_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/auto_service) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Automotive service bay. |
| `ballawley_park_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/ballawley_park) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Forest park clearing. |
| `charolettenbrunn_park_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/charlottenbrunn_park) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | European park walkway. |
| `circus_maximus_2_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/circus_maximus_2) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Historic Roman plaza. |
| `dancing_hall_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/dancing_hall) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Bright dance hall interior. |
| `empty_warehouse_01_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/empty_warehouse_01) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Large empty warehouse. |
| `flower_road_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/flower_road) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Suburban road lined with flowers. |
| `goegap_road_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/goegap_road) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Desert road in Goegap reserve. |
| `hochsal_field_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/hochsal_field) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Rural field with soft sky. |
| `machine_shop_02_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/machine_shop_02) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Machine shop interior. |
| `metro_vijzelgracht_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/metro_vijzelgracht) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Amsterdam metro station. |
| `old_depot_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/old_depot) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Weathered industrial depot. |
| `piazza_martin_lutero_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/piazza_martin_lutero) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Urban plaza at golden hour. |
| `rural_asphalt_road_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/rural_asphalt_road) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Country asphalt road. |
| `squash_court_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/squash_court) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Indoor squash court. |
| `studio_small_09_2k.hdr` | 2K (2048×1024) | [Poly Haven](https://polyhaven.com/a/studio_small_09) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Poly Haven | Neutral studio lighting. |

_The manifest must be updated whenever the asset list changes. Duplicates such
as `ballawley_park_2k (1).hdr` are not part of the catalogue and should be
removed immediately._

## Integrity audit (2025-11-10)

- Verification command: `python tools/verify_hdr_assets.py --fetch-missing`
- Result: all 24 manifest entries matched their published SHA-256 hashes; every
  download passed the Radiance header check and no duplicate `.hdr`/`.exr`
  assets were detected across `assets/hdr/` and `assets/qml/assets/`.
- Audit cache: `.cache/hdr_assets/` now contains validated copies for offline
  development; CI consumes the same cache path when available.

## ✅ Path Unification (v5.0.0)

**All HDR paths are now normalized to `file://` URLs through centralized processing.**

### How paths are processed

1. **Settings storage**: Use relative paths in `config/app_settings.json`
   ```json
   {
     "environment": {
       "ibl_source": "../hdr/studio_small_09_2k.hdr"
     }
   }
   ```

2. **Automatic normalization**: `MainWindow.normalizeHdrPath()` converts to canonical `file://` URL
   - Searches in: `assets/hdr/`, `assets/qml/`, `assets/`, `project_root/`
   - Returns: `file:///C:/.../assets/hdr/studio_small_09_2k.hdr`
   - Logs warnings if file not found

3. **QML usage**: Always use normalized paths
   ```qml
   IblProbeLoader {
       primarySource: window.normalizeHdrPath(rawPath)
   }
   ```

### Supported path formats

| Input format | Example | Result |
|--------------|---------|--------|
| Relative | `../hdr/studio.hdr` | `file:///.../assets/hdr/studio.hdr` |
| Absolute | `C:/path/file.hdr` | `file:///C:/path/file.hdr` |
| file:// URL | `file:///path/file.hdr` | `file:///path/file.hdr` (validated) |
| Remote URL | `http://server/file.hdr` | `http://server/file.hdr` (unchanged) |

**See also**: `docs/HDR_PATHS_UNIFIED.md`, `docs/HDR_PATHS_QUICK_START.md`

### Discovery paths and UI warnings

`GraphicsPanel` индексирует HDR/EXR файлы из трёх каталогов по умолчанию:

1. `assets/hdr/` — основной каталог репозитория
2. `assets/hdri/` — внешние наборы, поставляемые art-командой
3. `assets/qml/assets/` — ассеты, расположенные рядом с QML-сценами

Виджет `FileCyclerWidget` формирует выпадающий список с уникальными именами и
подсвечивает отсутствующие файлы красным индикатором. При смене значения статус
`⚠ файл не найден` отображается рядом с селектором и передаётся в tooltip. Это
поведение реализовано в `EnvironmentTab._discover_hdr_files()` и
`EnvironmentTab._refresh_hdr_status()` и покрыто модульными тестами
`tests/unit/ui/test_hdr_discovery.py` и
`tests/unit/ui/test_main_window_hdr_paths.py`.

Функция `normalizeHdrPath()` в слое Python (`src/ui/main_window_pkg/_hdr_paths.py`)
выстраивает последовательность кандидатных путей (`assets/qml/`, `assets/hdr/`,
`assets/`, корень проекта) и возвращает `file://` URL только при успешном
нахождении файла. Если ни один кандидат не найден, в лог попадает предупреждение
`normalizeHdrPath: HDR asset not found (input=…, candidates=…)`, а в UI
очищается поле пути, что немедленно сигнализирует о проблеме с размещением
ассета.

## Installation workflow

1. Download the required HDR files from the sources listed above.
2. Place the originals in `assets/hdr/` and keep the filenames unchanged.
3. Reference in settings using relative paths: `../hdr/filename.hdr`
4. Let `normalizeHdrPath()` handle the rest automatically
5. Commit the updated inventory table whenever new lighting profiles are added.

## HDR dynamic range calibration

- Bloom controls expose the HDR headroom directly inside the Effects tab. Use
  the `HDR Maximum (glowHDRMaximumValue)` slider to clamp peak energy between
  `0.0` and `10.0` (step `0.1`) and the `HDR Scale (glowHDRScale)` slider to
  rescale incoming radiance between `1.0` and `5.0` (step `0.1`). The Python
  panel serialises these values as `bloom_hdr_max` and `bloom_hdr_scale`, while
  `SceneEnvironmentController.qml` applies them to the Qt Quick 3D scene.
- When QA captures regression screenshots, log `bloom.hdr_max` and
  `bloom.hdr_scale` events from `logs/graphics/session_*.jsonl` alongside the
  HDR filename. This ensures bloom behaviour can be reproduced even after the
  dynamic range sliders are retuned.

## Texture persistence & recovery

- HDR selections are persisted via the graphics settings payload.
  `SettingsManager` normalises `ibl_source` paths before committing them to
  `config/app_settings.json`, so a valid relative path (`../hdr/*.hdr`) will be
  restored on the next launch even if the project moves to a different
  workspace.
- The `EnvironmentTab` reads the stored value, checks it against the discovered
  HDR catalogue, and updates the UI status label. Missing files trigger the
  fallback workflow (`normalizeHdrPath` warning + FileCyclerWidget indicator)
  without clearing the persisted path, allowing texture packages to be restored
  later without losing user preferences.

## Verification tooling

- Run `python tools/verify_hdr_assets.py --fetch-missing` to download the
  manifest entries into `.cache/hdr_assets/`, confirm their SHA-256 checksums and
  validate the Radiance headers.
- CI executes the same script through `make check` to ensure no duplicate or
  untracked HDR files appear under `assets/hdr/` or `assets/qml/assets/`.
- Update `assets/hdr/hdr_manifest.json` when adding or retiring panoramas so the
  automated checks stay authoritative.

## Curation policy

- Do not commit temporary placeholder files. Missing HDRIs should surface as
  configuration warnings during testing so we notice broken lighting pipelines
  early.
- Large raw captures (for example, `DSC_9975.NEF`) must stay in the external
  art source archive. Reference them in documentation or manifests, but do not
  add them to this repository.
- When introducing a new HDRI, update the table above and attach licensing
  details so downstream teams can validate redistribution rights.
- **Always use relative paths** in configs (e.g., `../hdr/file.hdr`) for portability

## Diagnostics

**IBL Logger** tracks all HDR loading events in timestamped logs:
```
logs/ibl/ibl_signals_YYYYMMDD_HHMMSS.log
```

Check logs for loading issues:
```bash
Get-Content logs/ibl/ibl_signals_*.log -Tail 20
```

Expected output:
```log
INFO  | IblProbeLoader | Primary source changed: file:///.../hdr/studio_small_09_2k.hdr
INFO  | IblProbeLoader | Texture status: Loading
SUCCESS | IblProbeLoader | HDR probe LOADED successfully
```

**See also**: `docs/IBL_LOGGING_GUIDE.md`
