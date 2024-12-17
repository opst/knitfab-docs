import string

from lighteval.tasks.lighteval_task import LightevalTaskConfig
from lighteval.tasks.requests import Doc
from lighteval.metrics.metrics import Metrics


def prompter(line, task_name: str = None):
    def _remove_prefixes(aliases):
        # Optimization: Remove any alias that has a strict prefix elsewhere in the list
        # we can do this because if the prefix is acceptable by isgreedy, we can stop looking
        aliases.sort()
        ret = [aliases[0]]
        for alias in aliases[1:]:
            if not alias.startswith(ret[-1]):
                ret.append(alias)
        return ret

    # Exact match of any of the several options possible.
    list_of_candidates = [
        alias.lower().translate(str.maketrans("", "", string.punctuation))
        for alias in _remove_prefixes(line["answer"]["aliases"])
    ]

    return Doc(
        task_name=task_name,
        query=f"You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: {line['question']}\nAnswer:",
        gold_index=0,
        choices=[
            list_of_candidates
        ],  # could be interesting to add normalized aliases to the mix
    )


TASKS_TABLE = [
    LightevalTaskConfig(
        name="trivia_qa",
        prompt_function=prompter,
        suite=["custom"],
        hf_repo="mandarjoshi/trivia_qa",
        hf_subset="rc.nocontext",
        hf_revision="0f7faf33a3908546c6fd5b73a660e0f8ff173c2f",
        hf_avail_splits=["train", "validation"],
        evaluation_splits=["validation"],
        metric=[Metrics.quasi_exact_match_triviaqa],
        generation_size=20,
        trust_dataset=True,
        stop_sequence=["Question:", "Question"],
        few_shots_select="random_sampling_from_train",
    ),
]
