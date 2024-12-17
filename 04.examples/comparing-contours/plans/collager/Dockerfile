FROM python:3.12-bookworm

RUN pip install beautifulsoup4

WORKDIR "/work"
COPY ./main.py .
ENTRYPOINT [ "python", "./main.py" ]
CMD ["--input", "/in", "--output", "/out"]
