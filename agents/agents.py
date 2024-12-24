from json import tool
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Union, Optional

load_dotenv()

@dataclass
class FlagDependencies:
    flag: str
    file_path: Union[str,Path]

    def __post_init__(self):
        try:
            self.file_path = Path(self.file_path)
            if not self.file_path.exists():
                cwd = os.getcwd()

        except OSError as e:




class ZapperResult(BaseModel):
    path: str = Field("The path to the file where the error occurs")
    file: str = Field("The name of the file with the error")
    line: int = Field("Which line the error occured in", ge=0)
    what: str = Field("Explanation in natural language of what the error is")
    todo: str = Field("Describe steps to take in natural language in order to fix the error")


bug_zapper = Agent(
    model_name=os.getenv('MODEL'),
    apy_key=os.getenv('API_KEY'),
    deps_type=FlagDependencies,
    ersult_type=ZapperResult,
    system_prompt=(
    'You are an expert software debugging assistant specializing in programming error analysis. '
    'Your task is to analyze error tracebacks and provide structured, actionable advice. '
    )
)

@bug_zapper.tool
