FROM python:3.10 AS builder

WORKDIR /work

COPY train-requirements.txt .
RUN python -m venv venv && \
    venv/bin/pip install --no-cache-dir -v -r train-requirements.txt

COPY . .

FROM python:3.10

WORKDIR /work

COPY --from=builder /work /work

ENV VIRTUAL_ENV=/work/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "python", "-u", "train.py" ]
CMD [ "--config-file", "/configs/train-config.json"]