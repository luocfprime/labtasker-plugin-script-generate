import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Tuple

import typer

from labtasker.client.cli.cli import app
from labtasker.client.core.logging import stderr_console, stdout_console


class BlockType(Enum):
    """Enum representing the types of blocks in the script."""

    SUBMIT = auto()
    TASK = auto()


@dataclass
class ScriptBlock:
    """Represents a block of script content with its variables and lines."""

    variables: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)
    indentation: int = 0


class ScriptParser:
    """Handles parsing and processing of script files with special markers."""

    SHEBANG_DEFAULT = "#!/bin/bash"
    VAR_PATTERN = re.compile(r"\$([a-zA-Z_][a-zA-Z0-9_]*)")
    MARKER_SUBMIT = "#@submit"
    MARKER_TASK = "#@task"
    MARKER_END = "#@end"

    def __init__(self, input_path: Path):
        self.input_path = input_path
        self.submit_lines: List[str] = []
        self.run_lines: List[str] = []
        self.block_stack: List[BlockType] = []
        self.current_task: Optional[ScriptBlock] = None
        self.insertion_point: Optional[int] = None
        self.line_number_offset: int = 0

    @property
    def current_block_type(self) -> Optional[BlockType]:
        """Get the current block type from the top of the stack."""
        return self.block_stack[-1] if self.block_stack else None

    @property
    def in_submit_block(self) -> bool:
        """Check if we're inside a submit block."""
        return BlockType.SUBMIT in self.block_stack

    @property
    def in_task_block(self) -> bool:
        """Check if we're inside a task block."""
        return self.block_stack and self.block_stack[-1] == BlockType.TASK

    def push_block(self, block_type: BlockType) -> None:
        """Push a new block onto the stack."""
        self.block_stack.append(block_type)

    def pop_block(self) -> Optional[BlockType]:
        """Pop the current block from the stack."""
        return self.block_stack.pop() if self.block_stack else None

    def parse_shebang(self, lines: List[str]) -> Tuple[str, List[str]]:
        """Extract and remove shebang line from script content."""
        if lines and lines[0].startswith("#!"):
            return lines[0].strip(), lines[1:]
        return self.SHEBANG_DEFAULT, lines

    def extract_variables_from_content(self, content: List[str]) -> List[str]:
        """Extract all variables from a block of content."""
        block_text = "\n".join(content)
        return sorted(
            set(f"${match}" for match in self.VAR_PATTERN.findall(block_text))
        )

    def extract_variables_from_task_marker(self, marker_text: str) -> List[str]:
        """Extract variables explicitly defined in a task marker."""
        return sorted(set(marker_text[len(self.MARKER_TASK) :].strip().split()))

    def look_ahead_for_variables(self, lines: List[str], start_idx: int) -> List[str]:
        """Look ahead in the script to find variables used in a block."""
        block_content = []
        idx = start_idx

        while idx < len(lines):
            line = lines[idx].strip()
            if line == self.MARKER_END:
                break
            block_content.append(lines[idx])
            idx += 1

        return self.extract_variables_from_content(block_content)

    def build_loop_command(self, block: ScriptBlock) -> List[str]:
        """Construct labtasker loop command using heredoc syntax."""
        if not block.variables:
            return []

        clean_vars = sorted({v.lstrip("$") for v in block.variables})
        delimiter = "LABTASKER_LOOP_EOF"

        return [
            f"labtasker loop <<'{delimiter}'",
            *[f"{var}='%({var})'" for var in clean_vars],
            *block.lines,
            delimiter,
        ]

    def create_task_block(self, line: str, variables: List[str]) -> ScriptBlock:
        """Create a new task block with the given variables."""
        indentation = len(line) - len(line.lstrip())
        return ScriptBlock(variables=variables, indentation=indentation)

    def add_task_to_submit_script(self, task: ScriptBlock) -> None:
        """Add task submission command to the submit script."""
        if not task.variables:
            stderr_console.print(
                "Warning: Task with no variables will be ignored in submit script",
                style="yellow",
            )
            return

        params = " ".join(
            [f"--{var.lstrip('$')} ${var.lstrip('$')}" for var in task.variables]
        )
        indent = " " * task.indentation
        self.submit_lines.append(f"{indent}labtasker task submit -- {params}")

    def process_script(self) -> Tuple[List[str], List[str]]:
        """Process the input script and generate submit and run scripts."""
        with open(self.input_path, "r") as f:
            raw_lines = f.readlines()

        shebang, content_lines = self.parse_shebang(raw_lines)
        self.line_number_offset = len(raw_lines) - len(content_lines)

        header = [
            shebang,
            f"# This script is generated by Labtasker from {self.input_path.name}",
        ]

        self.submit_lines = header.copy()
        self.run_lines = header.copy()

        for idx, line in enumerate(content_lines):
            stripped = line.strip()
            line_number = idx + 1 + self.line_number_offset

            if stripped == self.MARKER_SUBMIT:
                if self.in_submit_block:
                    raise ValueError(
                        f"Nested #@submit blocks not allowed at line {line_number}"
                    )
                self.push_block(BlockType.SUBMIT)
                self.insertion_point = len(self.run_lines)
                continue

            if stripped.startswith(self.MARKER_TASK):
                if self.in_task_block:
                    raise ValueError(
                        f"Nested #@task blocks not allowed at line {line_number}"
                    )

                explicit_vars = self.extract_variables_from_task_marker(stripped)
                if not explicit_vars:
                    explicit_vars = self.look_ahead_for_variables(
                        content_lines, idx + 1
                    )
                    if not explicit_vars:
                        raise ValueError(
                            f"No variables found in #@task block at line {line_number}"
                        )

                self.current_task = self.create_task_block(line, explicit_vars)
                self.push_block(BlockType.TASK)

                if self.in_submit_block:
                    self.add_task_to_submit_script(self.current_task)
                continue

            if stripped == self.MARKER_END:
                block_type = self.pop_block()
                if not block_type:
                    raise ValueError(f"Unmatched #@end at line {line_number}")

                if (
                    block_type == BlockType.TASK
                    and self.current_task
                    and self.in_submit_block
                ):
                    task_commands = self.build_loop_command(self.current_task)
                    if task_commands and self.insertion_point is not None:
                        self.run_lines[self.insertion_point : self.insertion_point] = (
                            task_commands
                        )

                if block_type == BlockType.TASK:
                    self.current_task = None
                continue

            if self.in_task_block and self.current_task:
                self.current_task.lines.append(line.rstrip())
            elif self.in_submit_block:
                self.submit_lines.append(line.rstrip())
            else:
                self.submit_lines.append(line.rstrip())
                self.run_lines.append(line.rstrip())

        if self.block_stack:
            block_name = self.current_block_type.name.lower()
            raise ValueError(f"Unclosed #{block_name} block at end of file")

        return self.submit_lines, self.run_lines


@app.command()
def generate(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Input script file containing task markers",
    ),
    submit_output: str = typer.Option(
        "{basename}_submit.sh", help="Submit script filename template"
    ),
    run_output: str = typer.Option(
        "{basename}_run.sh", help="Run script filename template"
    ),
):
    """Decompose workflow script into submit/run components using special markers."""
    try:
        basename = input_path.stem
        path_separator = "/"

        submit_output_path = (
            Path(submit_output.format(basename=basename))
            if path_separator in submit_output
            else input_path.parent / submit_output.format(basename=basename)
        )

        run_output_path = (
            Path(run_output.format(basename=basename))
            if path_separator in run_output
            else input_path.parent / run_output.format(basename=basename)
        )

        parser = ScriptParser(input_path)
        submit_lines, run_lines = parser.process_script()

        submit_output_path.write_text("\n".join(submit_lines))
        run_output_path.write_text("\n".join(run_lines))

        submit_output_path.chmod(0o755)
        run_output_path.chmod(0o755)

        stdout_console.print(
            f"Generated submit script: {submit_output_path}", style="green"
        )
        stdout_console.print(f"Generated run script: {run_output_path}", style="green")

    except ValueError as e:
        stderr_console.print(f"Error: {str(e)}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        stderr_console.print(f"Unexpected error: {str(e)}", style="red")
        raise typer.Exit(1)
