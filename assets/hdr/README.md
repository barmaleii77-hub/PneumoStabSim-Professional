# HDR Environment Inventory

This directory stores the canonical high dynamic range (HDR) environment maps that feed
image-based lighting for PneumoStabSim Professional. Keeping the authoritative copies
here ensures that lighting presets stay consistent between the editor, automated tests
and packaged builds.

## Required production HDRIs

| File name | Resolution | Source | License | Purpose |
| --- | --- | --- | --- | --- |
| `studio_small_09_2k.hdr` | 2048×1024 | https://polyhaven.com/a/studio_small_09 | CC0 1.0 | Default fallback for the workshop lighting preset. |

_Store additional HDRIs in this directory using the same table format so that the
renovation plan can track coverage at a glance._

## ✅ Path Unification (v4.9.6)

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

## Installation workflow

1. Download the required HDR files from the sources listed above.
2. Place the originals in `assets/hdr/` and keep the filenames unchanged.
3. Reference in settings using relative paths: `../hdr/filename.hdr`
4. Let `normalizeHdrPath()` handle the rest automatically
5. Commit the updated inventory table whenever new lighting profiles are added.

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
