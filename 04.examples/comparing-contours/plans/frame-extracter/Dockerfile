FROM python:3.12-bookworm

RUN pip install opencv-python-headless

WORKDIR "/work"
COPY ./main.py .
ENTRYPOINT [ "python", "./main.py" ]
CMD ["--input", "/in", "--output", "/out"]
