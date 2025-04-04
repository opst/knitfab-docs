FROM python:3.11

WORKDIR /work

COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "-u", "validate.py" ]
CMD [ "--dataset", "/in/dataset", "--model", "/in/model", "--save-to", "/out/metrics" ]
