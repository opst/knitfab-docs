FROM python:3.11

WORKDIR /work

RUN pip install pandas scikit-learn joblib

COPY . .

ENTRYPOINT [ "python", "-u", "validate.py" ]
CMD [ "--dataset", "/in/dataset", "--model", "/in/model", "--save-to", "/out/metrics" ]