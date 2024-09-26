from abc import ABC, abstractmethod
import os
import pandas as pd
import uuid
import csv
import json
import math

from typing import Tuple

from prompts.prompts import PromptLoader, PromptType




class FileProcessor(ABC):
  def __init__(self, file_path: str, temp_dir: str = "tmp", llm_model: Tuple[str, str] = ("openai", "gpt-4o-mini")):
    self.file_path = file_path
    self.temp_dir = temp_dir

    self.file_name, self.file_extension = os.path.splitext(self.file_path)
    self.file_name = self.file_name.split("/")[-1]

    self.llm_client = LLM(llm_model)
    
  @classmethod
  def get_processor(cls, file_path: str):
    file_name, file_extension = os.path.splitext(file_path)
    if file_extension in [".xlsx", ".csv"]:
      return SheetProcessor(file_path)
    
  @classmethod
  def remove_numbers_dict(cls, d: dict):
    """
    Recursively remove keys with NaN values or numeric values from nested dictionaries.
    """
    if isinstance(d, dict):
      return {k: FileProcessor.remove_numbers_dict(v) for k, v in d.items()
        if not (isinstance(v, (int, float)) or pd.isna(v) or (isinstance(v, float) and math.isnan(v)))}
    return d

  @abstractmethod
  def process(self):
    pass

class SheetProcessor(FileProcessor):
  def __init__(self, file_path: str, temp_dir: str = "tmp"):
    super().__init__(file_path, temp_dir)


  def load_df_from_string(self, table_string: str, col_delim: str = ","):
    tmp_file = uuid.uuid4()
    tmp_file_path = os.path.join(os.getcwd(), f"{self.temp_dir}/processing/{tmp_file}.csv")

    with open(tmp_file_path, "w+") as f:
      f.write(table_string)
    with open(tmp_file_path, "r+") as f:
      n = len(f.readline().split(col_delim))

    table_df = pd.read_csv(os.path.join(os.getcwd(), tmp_file_path), usecols=range(n),quoting=csv.QUOTE_ALL, quotechar="'")
    
    os.remove(tmp_file_path)

    print(table_df)

    return table_df
  
  def generate_summary_and_tags(self):
    if self.file_extension == ".xlsx":
      unprocessed_df = pd.read_excel(self.file_path)
    elif self.file_extension == ".csv":
      unprocessed_df = pd.read_csv(self.file_path)

    processed_dict = FileProcessor.remove_numbers_dict(unprocessed_df.to_dict())

    prompt, system_message = PromptLoader.get_prompt(PromptType.Summarization, "dict_sheet")

    filled_prompt = prompt.format(title=self.filename, dict_sheet=str(processed_dict))

    result: str = self.llm_client.query(filled_prompt, system_message)

    # strip json markdown
    result = result.removeprefix("```json").removesuffix("```")

    result_json: dict[str, str] = json.loads(result)
    
    try:
      summary, tags = result_json["summary"], result_json["tags"] 
    except Exception as e:
      print(f"{e}: Returning title as summary and blank tags")
      summary = self.filename
      tags = []

    return summary, tags

  def process(self):
    if self.file_extension == ".xlsx":
      unprocessed_df = pd.read_excel(self.file_path)
    elif self.file_extension == ".csv":
      unprocessed_df = pd.read_csv(self.file_path)

    tmp_file = uuid.uuid4()
    tmp_file_path = os.path.join(os.getcwd(), f"{self.temp_dir}/processing/{tmp_file}.csv")

    unprocessed_df.dropna(axis=1, how='all') \
                  .to_csv(tmp_file_path,quoting=csv.QUOTE_ALL, quotechar="'")
    
    with open(tmp_file_path, "r+") as f:
      csv_as_text = f.read()

    os.remove(tmp_file_path)

    prompt, system_message = PromptLoader.get_prompt(PromptType.Parsing, "csv")

    filled_prompt = prompt.format(text=csv_as_text)

    result: str = self.llm_client.query(filled_prompt, system_message)

    # strip json markdown
    result = result.removeprefix("```json").removesuffix("```")

    tables_json: dict[str, str] = json.loads(result)

    tables_df: dict[str, pd.DataFrame] = {}

    for key, value in tables_json.items():
      tables_df[key] = self.load_df_from_string(value)

    return tables_df