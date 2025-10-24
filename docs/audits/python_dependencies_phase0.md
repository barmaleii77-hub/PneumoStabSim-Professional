# Phase 0 Dependency Snapshot

Generated via `python -m pipdeptree` on the renovation container to capture the
current Python dependency graph. The environment reflects the repository's
editable install (`PneumoStabSim-Professional==0.1.0`).

## High-Level Findings

- Tooling stack already includes `ruff`, `mypy`, `pytest`, and `pyright`,
  confirming static analysis coverage.
- Core runtime relies on `PySide6 6.10.0` with the expected `shiboken6`
  bindings and OpenGL acceleration packages (`PyOpenGL`, `PyOpenGL-accelerate`).
- Scientific computation dependencies are constrained to `numpy 2.3.4` and
  `scipy 1.16.2`.
- `pipdeptree` reported duplicate metadata for the editable project package,
  indicating that the source directory is already on the interpreter path;
  no action required beyond monitoring during packaging.

## Dependency Graph Extract

```
Warning!!! Duplicate package metadata found:
"/workspace/PneumoStabSim-Professional/src"
  PneumoStabSim-Professional       0.1.0            (using 0.1.0, "/root/.pyenv/versions/3.13.3/lib/python3.13/site-packages")
NOTE: This warning isn't a failure warning.
------------------------------------------------------------------------
black==25.1.0
├── click [required: >=8.0.0, installed: 8.2.1]
├── mypy_extensions [required: >=0.4.3, installed: 1.1.0]
├── packaging [required: >=22.0, installed: 25.0]
├── pathspec [required: >=0.9.0, installed: 0.12.1]
└── platformdirs [required: >=2, installed: 4.4.0]
isort==6.0.1
jsonschema==4.25.1
├── attrs [required: >=22.2.0, installed: 25.4.0]
├── jsonschema-specifications [required: >=2023.03.6, installed: 2025.9.1]
│   └── referencing [required: >=0.31.0, installed: 0.37.0]
│       ├── attrs [required: >=22.2.0, installed: 25.4.0]
│       └── rpds-py [required: >=0.7.0, installed: 0.28.0]
├── referencing [required: >=0.28.4, installed: 0.37.0]
│   ├── attrs [required: >=22.2.0, installed: 25.4.0]
│   └── rpds-py [required: >=0.7.0, installed: 0.28.0]
└── rpds-py [required: >=0.7.1, installed: 0.28.0]
mypy==1.17.1
├── typing_extensions [required: >=4.6.0, installed: 4.15.0]
├── mypy_extensions [required: >=1.0.0, installed: 1.1.0]
└── pathspec [required: >=0.9.0, installed: 0.12.1]
pipdeptree==2.29.0
├── packaging [required: >=25, installed: 25.0]
└── pip [required: >=25.2, installed: 25.2]
PneumoStabSim-Professional==0.1.0
├── numpy [required: >=1.24.0,<3.0, installed: 2.3.4]
├── scipy [required: >=1.10.0,<2.0, installed: 1.16.2]
│   └── numpy [required: >=1.25.2,<2.6, installed: 2.3.4]
├── PySide6 [required: >=6.10.0,<7.0.0, installed: 6.10.0]
│   ├── shiboken6 [required: ==6.10.0, installed: 6.10.0]
│   ├── PySide6_Essentials [required: ==6.10.0, installed: 6.10.0]
│   │   └── shiboken6 [required: ==6.10.0, installed: 6.10.0]
│   └── PySide6_Addons [required: ==6.10.0, installed: 6.10.0]
│       ├── shiboken6 [required: ==6.10.0, installed: 6.10.0]
│       └── PySide6_Essentials [required: ==6.10.0, installed: 6.10.0]
│           └── shiboken6 [required: ==6.10.0, installed: 6.10.0]
├── shiboken6 [required: >=6.10.0,<7.0.0, installed: 6.10.0]
├── PyOpenGL [required: >=3.1.0, installed: 3.1.10]
├── PyOpenGL-accelerate [required: >=3.1.0, installed: 3.1.10]
├── matplotlib [required: >=3.5.0, installed: 3.10.7]
│   ├── contourpy [required: >=1.0.1, installed: 1.3.3]
│   │   └── numpy [required: >=1.25, installed: 2.3.4]
│   ├── cycler [required: >=0.10, installed: 0.12.1]
│   ├── fonttools [required: >=4.22.0, installed: 4.60.1]
│   ├── kiwisolver [required: >=1.3.1, installed: 1.4.9]
│   ├── numpy [required: >=1.23, installed: 2.3.4]
│   ├── packaging [required: >=20.0, installed: 25.0]
│   ├── pillow [required: >=8, installed: 12.0.0]
│   ├── pyparsing [required: >=3, installed: 3.2.5]
│   └── python-dateutil [required: >=2.7, installed: 2.9.0.post0]
│       └── six [required: >=1.5, installed: 1.17.0]
├── pillow [required: >=8.0.0, installed: 12.0.0]
├── psutil [required: >=5.8.0, installed: 7.1.1]
├── python-dotenv [required: >=1.0.0, installed: 1.1.1]
└── PyYAML [required: >=6.0, installed: 6.0.3]
pyright==1.1.404
├── nodeenv [required: >=1.6.0, installed: 1.9.1]
└── typing_extensions [required: >=4.1, installed: 4.15.0]
pytest==8.4.1
├── iniconfig [required: >=1, installed: 2.1.0]
├── packaging [required: >=20, installed: 25.0]
├── pluggy [required: >=1.5,<2, installed: 1.6.0]
└── Pygments [required: >=2.7.2, installed: 2.19.2]
ruff==0.12.11
```
