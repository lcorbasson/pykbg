#! /bin/bash -ex
[ ! -f pyproject.toml ] && exit 0

COV_ARGS=""

if [ -n "$HTMLCOV" ]; then
  COV_ARGS="$COV_ARGS --cov-report=html"
fi
if [ -n "$BRANCHCOV" ]; then
  COV_ARGS="$COV_ARGS --cov-branch"
fi

uv run ruff check kbg
#uv run mypy --strict --check-untyped-defs ./*.py kbg/*.py examples/*.py
uv run mypy --check-untyped-defs ./*.py kbg/*.py examples/*.py
uv run pytest --cov=. $COV_ARGS tests/
