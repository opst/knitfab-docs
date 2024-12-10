FROM python:3.12.7-bookworm

WORKDIR "/work"
RUN git clone https://github.com/huggingface/smollm.git .
# RUN pip install jinja2
# RUN pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r evaluation/requirements.txt
ENTRYPOINT ["lighteval", "accelerate", "--model_args", "pretrained=HuggingFaceTB/SmolLM2-135M,revision=main,dtype=bfloat16", "--save_details"]
CMD ["--custom_tasks", "/evaluation/tasks.py", "--tasks", "custom|trivia_qa|0|1", "--output_dir", "/evals"]
