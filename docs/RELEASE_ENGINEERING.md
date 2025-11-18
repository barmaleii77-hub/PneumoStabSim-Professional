# Release Engineering Guide

This document describes how PneumoStabSim Professional packages are produced,
verified, and published across Linux, Windows, and macOS platforms.

## 1. Prerequisites

The packaging toolchain is managed by [`uv`](https://github.com/astral-sh/uv)
and relies on PyInstaller for Linux/Windows builds and cx_Freeze for macOS.
Before creating a build locally:

1. Install `uv` (see `docs/CI.md` for the standard bootstrap flow).
2. Materialise the locked release environment:
   ```bash
   make uv-sync
   uv sync --frozen --extra release
   ```
3. Ensure the signing key material is available to `gpg`:
   ```bash
   gpg --import path/to/release-private.key
   gpg --import path/to/release-public.key
   ```

> **Note:** The CI pipelines expect the signing material to be supplied via the
> `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`, and `GPG_PUBLIC_KEY` secrets.

## 2. Building Packages Locally

Use the unified make target to trigger platform-aware packaging:

```bash
make package-all
```

This delegates to `python -m tools.packaging.build_packages`, which inspects the
host platform and invokes the appropriate builder:

- **Linux / Windows:** PyInstaller (windowed, one-dir layout)
- **macOS:** cx_Freeze universal2 bundle

Artifacts are written to `dist/packages/` and include:

- Platform-specific archives (`.tar.gz` or `.zip`)
- SHA-256 checksum files (`.sha256`)
- Detached ASCII-armored signatures (`.asc`)
- Build metadata manifests (`.json`)

## 3. Verifying Build Outputs

Always validate both integrity and authenticity before distributing binaries:

```bash
cd dist/packages
shasum -a 256 --check *.sha256
for sig in *.asc; do
  gpg --verify "$sig"
  # gpg resolves the matching archive automatically
done
```

On Windows, the checksum command can be replaced with PowerShell:

```powershell
Set-Location dist/packages
Get-ChildItem -Filter *.sha256 | ForEach-Object {
  Get-FileHash ($_.FullName -replace '\\.sha256$') -Algorithm SHA256
}
Get-ChildItem -Filter *.asc | ForEach-Object {
  & gpg --verify $_.FullName ($_.FullName -replace '\\.asc$')
}
```

## 4. Continuous Integration and Release Automation

The GitHub Actions workflow at `.github/workflows/release.yml` orchestrates
packaging for tagged builds and also runs on pushes to any `feature/*` branch
(including the long-lived `feature/hdr-assets-migration`) to validate release
artifacts before promotion:

1. Each OS runner installs the locked environment (`uv sync --extra release`).
2. `make package-all` generates the platform bundle.
3. GPG signing is performed on every archive, using the imported private key.
4. Both SHA-256 checksums and GPG signatures are verified on the same runner.
5. Build outputs (`.zip`, `.tar.gz`, `.sha256`, `.asc`, `.json`) are uploaded as
   job artifacts.

A final `publish` job downloads all artifacts, re-imports the release public key,
re-validates checksums and signatures, and then publishes them as release assets.

## 5. Manual Release Checklist

When preparing a production release:

1. Update version metadata and changelog entries as required.
2. Tag the repository (`git tag vX.Y.Z`) and push the tag to trigger CI.
3. Monitor the `Release Packaging` workflow for successful packaging/signing on
   all platforms.
4. Download the published artifacts and perform an out-of-band verification if
   mandated by your compliance process.
5. Announce availability through the appropriate communication channels once the
   release is live.

Following these steps ensures every distribution artifact is built reproducibly
and verified cryptographically before it reaches end users.
