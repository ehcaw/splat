# [START utils.py]
"""
This file creates a dependency graph that depicts the relationships between files.
If the user does not provide a flag, the graph will only create itself from the error stack.
If the user does provide "-g", the graph will contain all files from the repo, with respect to the .gitignore.
If the user does provide "-r", the graph will contain all files from the error stack, alongside all files that are imported/included in the source file, and recursively call itself until all relationships are exhausted.

@Usage: "splat <?-g> <?-r>"
"""
import os
from typing import List, Set
import ast
from networkx import DiGraph

'''
This function is a shorthand redirecting based on if a flag is raised during command call or not.
@Usage: call graph_related_files(pure error string, if flag is raised)
@Returns: None
'''
def graph_related_files(error_info: str, global_flag_raised: bool = False) -> None:
  if global_flag_raised:
    return
  else:
    return

'''
This function runs through the entire repository, and dodges all files that do not start with .py.
@Usage: call get_repo_details() or with a specific path (most preferably from the stack error trace)
@Returns: all traced files of type List[str]
'''
def get_repo_details(repo_path: str = ".") -> List[str]:
  traced_files = []
  gitignore = set()

  # Read the .gitignore, if it exists
  if os.path.exists('.gitignore'):
    with open('.gitgnore', 'r') as f:
      gitignore = set(line.strip() for line in f if line.strip() and not line.startswith("#"))

  for root, _, files in os.walk(repo_path):
    for file in files:
      if (file.endswith('py')):
        full_path = os.path.join(root, file)
        relative_path = os.path.relpath(full_path, repo_path)
        if not any(relative_path.startswith(ignore) for ignore in gitignore):
          traced_files.append(full_path)

  return traced_files

'''
This function runs through a source file, and grabs all files linked by any Nth degree connection.
@Usage: call get_related_details with required parameter: src file path
@Returns: all files related to parameter file to any Nth degree in type Set[str]
'''
def get_related_details(file_path: str) -> Set[str]:
  with open(file_path, 'r') as file:
    tree = ast.parse(file.read(), filename=file_path)

  imports = set()
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      for alias in node.names:
        imports.add(alias.name)
    elif isinstance(node, ast.ImportFrom):
      if node.module:
        imports.add(node.module)

  return imports

'''
This helper function resolves an import name to an absolute file path.
@Usage: call resolve_import(import_name: str, file_path: str)
@Returns: absolute path as type str or None if the import cannot be found
'''
def resolve_import(import_name: str, file_path: str) -> str | None:
  dir_path = os.path.dirname(file_path)
  possible_paths = [
    os.path.join(dir_path, f"{import_name.replace('.', '/')}.py"),
    os.path.join(dir_path, import_name, "__init__.py"),
  ]

  for path in possible_paths:
    if os.path.exists(path):
      return os.path.abspath(path)

  return None
# [END utils.py]
