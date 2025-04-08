FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

COPY pyproject.toml /app

# Install dependencies
RUN uv sync && echo "UV sync completed"
RUN uv pip install -e .

COPY . /app


RUN cd src/rag_doc_manager

# Run the app
CMD ["uv", "run", "fastapi", "run", "src/rag_doc_manager/main.py", "--port", "80", "--host", "0.0.0.0"]