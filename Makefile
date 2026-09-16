.PHONY: run test lint format clean

run:
	uv run python -m src.generate_data
	uv run python pipeline.py

test:
	uv run pytest tests/ -v

lint: 
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

clean:
	rm -rf data/*.duckdb data/*.csv .pytest_cache
