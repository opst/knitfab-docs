FROM python:3.11

WORKDIR /work

COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "-u", "initial-train.py" ]
CMD [ "--dataset", "/in/dataset", "--save-to", "/out/model" ]
