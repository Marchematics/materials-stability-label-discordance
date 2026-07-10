FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates make \
    latexmk texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/sourceaware
COPY requirements-lock.txt pyproject.toml ./
COPY sourceaware ./sourceaware
RUN pip install --no-cache-dir -r requirements-lock.txt && pip install --no-deps -e .
COPY . .
ENTRYPOINT ["bash", "run_all.sh"]
