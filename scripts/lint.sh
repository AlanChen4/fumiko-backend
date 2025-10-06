echo "Checking with Ruff..."
uv run ruff check . --fix

echo "Checking with Mypy..."
uv run mypy .