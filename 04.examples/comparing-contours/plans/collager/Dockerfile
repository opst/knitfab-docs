FROM python:3.12-bookworm

WORKDIR "/work"
COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "./main.py" ]
CMD ["--input", "/in", "--output", "/out"]
