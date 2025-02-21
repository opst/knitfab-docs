FROM python:3.10 AS builder

WORKDIR /work

COPY evaluate-requirements.txt . 
RUN python -m venv venv && \
    venv/bin/pip install --no-cache-dir -r evaluate-requirements.txt

COPY . .

FROM python:3.10

WORKDIR /work

COPY --from=builder /work /work

ENV VIRTUAL_ENV=/work/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONUNBUFFERED=1

RUN deepeval set-local-model --model-name=llama3.2 \
    --base-url="http://ollama:11434/v1/" \
    --api-key="ollama"

ENTRYPOINT [ "python", "-u", "evaluate.py" ]
CMD [ "--config-file", "/configs/evaluate-config.json", "--model-path", "/in/model"]