# Code Style and Quality Standards

This document summarises the automated quality gates enforced for the project.
All contributors should run the commands described in each section before
opening a pull request.

## Python

Python code is formatted and linted with [Ruff](https://docs.astral.sh/ruff/) and
checked with [mypy](https://mypy-lang.org/).

- Configuration lives in [`ruff.toml`](../ruff.toml) and [`mypy.ini`](../mypy.ini).
- Run the format and lint checks locally:

  ```bash
  ruff format src tests tools app.py
  ruff check src tests tools app.py
  ```

- Keep static typing healthy by running mypy against the curated target list:

  ```bash
  python -m mypy --config-file mypy.ini $(tr '\n' ' ' < mypy_targets.txt)
  ```

The targets in `mypy_targets.txt` track modules that must always type-check
cleanly. Add new modules here as soon as they are ready for enforcement.

## .NET / C# (`PneumoStabSim.Core`)

C# code in `src/PneumoStabSim.Core` follows the rules encoded in
[`stylecop.json`](../src/PneumoStabSim.Core/stylecop.json) and the repository
`.editorconfig`.

- The project references `StyleCop.Analyzers` and treats all warnings as errors
  to guarantee consistent style.
- Use `dotnet format` to apply the conventions and verify CI compliance:

  ```bash
  dotnet format src/PneumoStabSim.Core/PneumoStabSim.Core.csproj
  dotnet format src/PneumoStabSim.Core/PneumoStabSim.Core.csproj --verify-no-changes --severity error
  ```

Running `dotnet build` locally is recommended because the analyzers execute
on every compilation.

## QML

We lint our QML entry points with `qmllint` (or `pyside6-qmllint`). The list of
files and directories to check is defined in
[`qmllint_targets.txt`](../qmllint_targets.txt).

```bash
make qml-lint QML_LINTER=pyside6-qmllint
```

Update `qmllint_targets.txt` whenever new UI components need coverage.

## Continuous Integration

The `Continuous Integration` workflow in `.github/workflows/ci.yml` runs all of
these checks (Ruff, mypy, `qmllint`, and `dotnet format --verify-no-changes`)
for every push and pull request. A failing job signals a regression in one of
these quality gates. Keep local environments aligned with the documented
commands to avoid surprises in CI.
