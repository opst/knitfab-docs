FROM python:3.12.7-bookworm

WORKDIR "/work"
COPY . .
RUN pip install -r requirements.txt
ENTRYPOINT ["lighteval", "accelerate", "--save-details"]
CMD ["--custom-tasks", "/in/tasks.py", "--output-dir", "/out", "model_name=HuggingFaceTB/SmolLM2-135M,revision=main,dtype=bfloat16", "custom|trivia_qa|0|1"]
