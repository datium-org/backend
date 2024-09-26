from enum import Enum

class PromptType(Enum):
  Parsing="parsing"
  Summarization="summarization"


import yaml
import os


class PromptLoader:
  @classmethod
  def get_prompt(cls, prompt_type: PromptType, prompt_name: str) -> str:
    with open(os.path.join(os.getcwd(), f'intelligence_api/backend/prompts/{prompt_type.value}.yaml'), 'r') as file:
      prompts = yaml.safe_load(file)

    # Access the LLM prompt
    prompt = prompts[prompt_name]["prompt"]
    system_message = prompts[prompt_name]["system_message"]

    return prompt, system_message