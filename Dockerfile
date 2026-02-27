FROM python:3.12-slim

RUN mkdir /workdir
WORKDIR /workdir

COPY document_parser/ /workdir/document_parser/
COPY llm/ /workdir/llm/
COPY integrations /workdir/integrations/

COPY *.py /workdir/

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /workdir/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENTRYPOINT uvicorn app:app --workers 1 --host 0.0.0.0 --port 8000