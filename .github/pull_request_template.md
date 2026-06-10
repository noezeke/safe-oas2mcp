## Summary

## Safety impact

- [ ] Does not expose secrets to tool schemas, logs, or responses
- [ ] Does not weaken default DELETE/write-operation policy
- [ ] Includes tests for policy or redaction changes

## Verification

```bash
python -m pytest -q
python -m ruff check .
python -m mypy
```

