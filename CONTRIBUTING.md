# Contributing

Discuss the scientific problem and expected behaviour in an issue before proposing a substantial change. Keep teaching explanations aligned with the code and state assumptions, units and exclusions explicitly.

## Local verification

Use Python 3.12 and install `requirements-lock.txt` in a virtual environment. Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use known-answer geometries or independent references for algorithm changes. Do not write tests that merely repeat the implementation. Report GUI/manual checks separately from numerical tests.

Do not add private microscopy data, credentials, virtual environments or generated review records. Public examples need provenance, permission to redistribute and source attribution. Code and data have separate licences.

Keep frozen protocols and previous results intact. Once a held-out image informs a method change it becomes development data for that revision. Do not retune on a holdout and continue presenting it as untouched validation.

Pull requests should describe the concrete problem, resulting behaviour, verification and remaining scientific limitations.
