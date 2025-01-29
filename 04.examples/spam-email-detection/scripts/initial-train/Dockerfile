FROM python:3.11

WORKDIR /work

RUN pip install pandas scikit-learn 
COPY . .

ENTRYPOINT [ "python", "-u", "initial-train.py" ]
CMD [ "--dataset", "/in/dataset", "--save-to", "/out/model" ]