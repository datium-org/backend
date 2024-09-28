from setuptools import setup, find_packages

setup(
  name="shared_clients",
  version="0.1.0",
  packages=find_packages(),
  install_requires=[
      "boto3>=1.20.0",
      "requests>=2.25.1",
      "pyyaml",
      "psycopg2",
      "pypdf2",
      "pandas",
      "openpyxl",
      "fastapi",
      "langchain",
      "langchain-openai",
      "openai",
      "transformers",
      "langchain-huggingface",
      "numpy",
      "python-dotenv"
  ],
  description="Shared client libraries for interacting with AWS services and LLMs.",
  author="Ali A",
  author_email="ali.hamdani.biz@gmail.com",
  classifiers=[
      "Programming Language :: Python :: 3",
      "Operating System :: OS Independent",
  ],
)
