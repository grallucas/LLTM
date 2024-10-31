from llama_cpp import Llama, LogitsProcessorList

class LLM:
    ... # TODO. Light wrapper for llama_cpp that additionally does: token/price tracking, easier logit processing, optional restricted JSON output (will be useful for structured tasks), LLM instance management