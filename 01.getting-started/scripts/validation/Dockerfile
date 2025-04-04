FROM python:3.11

WORKDIR /work

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "-u", "validation.py", "--dataset", "/in/dataset", "--model", "/in/model/model.pth" ]
