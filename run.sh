
#!/bin/sh

pip install poetry==1.7.1 &> /dev/null
poetry run pip install --upgrade pip &> /dev/null
poetry install --only main --no-root &> /dev/null
poetry run poetry run python run.py