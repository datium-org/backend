import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.globals import set_verbose

import argparse
import dotenv
import langchain
import logging
import numpy as np

from typing import Generator, Tuple

# For Testing Purposes...
langchain.debug = True
logging.basicConfig(level=logging.ERROR)

dotenv.load_dotenv()

class LLM():
  """
  A class that integrates with various LLM APIs for conversational AI purposes.
  """

  def __init__(self, llm_model: Tuple[str, str] = ("openai", "gpt-4o"), verbose=False):
    """
    Initializes the Chat class.
    """

    self.llm_model = llm_model

    self.__key = os.getenv(f'{llm_model[0].upper()}_API_KEY')
    self.__org = os.getenv(f'{llm_model[0].upper()}_ORG')

    if llm_model[0] == "openai":
      self.__client = ChatOpenAI(
          temperature=0, openai_api_key=self.__key, verbose=verbose, model=llm_model[1], organization=self.__org)
    
    self.__history = []
    self.__token_usage = np.zeros(shape=(4))  # ['completion_tokens', 'prompt_tokens', 'total_tokens'], Does not track streaming tokens

  def query(self, query: str, system_message: str = "You're a helpful assistant", include_history=False) -> str:
    """
    Processes a query using LLM.

    Args:
      query (str): The query string.

    Returns:
      str: The response from the language model.
    """
    query_message = HumanMessage(content=query)

    if include_history:
      messages = [
        SystemMessage(content=system_message),
        *self.__history,
        query_message
      ]
    else:
      messages = [
        SystemMessage(content=system_message),
        query_message
      ]

    response = self.__client.invoke(input=messages)

    token_usage: dict = response.response_metadata["token_usage"]
    logging.debug(token_usage)
    # Extract numerical values
    numeric_values = [
      token_usage.get('prompt_tokens', 0),
      token_usage.get('completion_tokens', 0),
      token_usage.get('total_tokens', 0),
      token_usage.get('completion_tokens_details', {}).get('reasoning_tokens', 0)
    ]

    # Convert to NumPy array
    token_stats = np.array(numeric_values, dtype=np.float64)
    self.__token_usage += token_stats

    content_response = response.content

    if include_history:
      self.__history.append(query_message)
      self.__history.append(AIMessage(content=content_response))

    return content_response

  def stream_query(self, query, system_message="You're a helpful assistant") -> Generator:
    """
    Stream a query using LLM.

    Args:
      query (str): The query string.

    Returns:
      str: The response from the language model.
    """
    query_message = HumanMessage(content=query)

    messages = [
      SystemMessage(content=system_message),
      *self.__history,
      query_message
    ]

    response = self.__client.stream(input=messages)
    out = ""
    for chunk in response:
      current_content = chunk
      out += current_content.content
      yield current_content.content
    out = AIMessage(content=out)
    self.__history.append(query_message)
    self.__history.append(out)

  def clear_history(self) -> None:
    self.__history = []

  def end_chat(self) -> None:
    """
    Cleans up resources
    """
    pass


if __name__ == "__main__":
  llm = LLM()
  print(llm.query("what is ur name"))
