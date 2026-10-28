# Engineering Failures, Bottlenecks & Fixes Log

##  1. Silent Type-Check Pass on `sqlalchemy.Enum` vs `enum.Enum` in Pydantic v2
* **Symptom:** `uv run pytest` failed during test collection with `PydanticSchemaGenerationError: Unable to generate pydantic-core schema for <class 'src.core.schemas.RiskSeverity'>`, even though `uv run mypy --strict` passed with 0 errors.
* **Root Cause:** IDE auto-import resolved `from sqlalchemy import Enum` instead of Python's standard library `from enum import Enum`. Because `sqlalchemy.Enum` is a valid class type, static type checking (`mypy`) succeeded, but `pydantic-core` schema compilation failed at runtime when inspecting `RiskSeverity(str, Enum)`.
* **Fix & Prevention:** Replaced import with standard library `enum.Enum`, enabled `ruff` import sorting (`I001`), and verified both `pytest` and `mypy --strict` run sequentially before every commit.