# make check — 2025-02-13

```bash
$ make check
python3 -m tools.ci_tasks lint
226 files already formatted
All checks passed!
[ci_tasks] $ /root/.pyenv/versions/3.13.3/bin/python3 -m ruff format --check app.py src tests tools
[ci_tasks] $ /root/.pyenv/versions/3.13.3/bin/python3 -m ruff check app.py src tests tools
python3 -m tools.ci_tasks typecheck
Success: no issues found in 3 source files
[ci_tasks] $ /root/.pyenv/versions/3.13.3/bin/python3 -m mypy --config-file /workspace/PneumoStabSim-Professional/mypy.ini src/pneumostabsim_typing src/common/signal_trace.py tools/audit_config.py
Running QML lint (qmllint)
---
---
python3 -m tools.ci_tasks test
===================================================== test session starts ======================================================
platform linux -- Python 3.13.3, pytest-8.4.1, pluggy-1.6.0
rootdir: /workspace/PneumoStabSim-Professional
configfile: pytest.ini
collected 28 items

tests/quality/test_sample_vector.py ..                                                                                   [  7%]
tests/unit/physics/test_forces.py ..............                                                                         [ 57%]
tests/unit/physics/test_physics_loop.py .                                                                                [ 60%]
tests/unit/physics/test_gas_network.py .........                                                                         [ 92%]
tests/unit/pneumo/test_diagonal_linking.py ..                                                                            [100%]

====================================================== 28 passed in 1.31s ======================================================
[ci_tasks] $ /root/.pyenv/versions/3.13.3/bin/python3 -m pytest tests/quality/test_sample_vector.py tests/unit/physics/test_forces.py tests/unit/physics/test_physics_loop.py tests/unit/physics/test_gas_network.py tests/unit/pneumo/test_diagonal_linking.py
```
