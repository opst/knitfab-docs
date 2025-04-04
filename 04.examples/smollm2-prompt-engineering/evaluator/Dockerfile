FROM python:3.12.7-bookworm

WORKDIR "/work"
RUN git clone https://github.com/huggingface/smollm.git .
RUN pip install -r text/evaluation/requirements.txt
ENTRYPOINT ["lighteval", "accelerate", "--model_args", "pretrained=HuggingFaceTB/SmolLM2-135M,revision=main,dtype=bfloat16", "--save_details"]
CMD ["--custom_tasks", "/in/tasks.py", "--tasks", "custom|trivia_qa|0|1", "--output_dir", "/out"]
