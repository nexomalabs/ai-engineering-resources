# Applied AI Engineering, Volume II, Chapter 17
# Section 17.7, The Pipeline Pattern
# Copied from the book by scripts/export_listings.py. Report errors as errata.

from typing import Callable
from dataclasses import dataclass, field

@dataclass
class PipelineStage:
    stage_id: str
    description: str
    prompt_template: str
    input_schema: dict
    output_schema: dict
    llm_fn: Callable[[str], str]  # Injected LLM call function

    def execute(self, context: dict) -> dict:
        """Render the stage prompt and execute the LLM call."""
        env = Environment(loader=BaseLoader())
        tmpl = env.from_string(self.prompt_template)
        rendered_prompt = tmpl.render(**context)
        raw_output = self.llm_fn(rendered_prompt)
        valid, result = self._validate(raw_output)
        if not valid:
            raise ValueError(f"Stage '{self.stage_id}' output failed validation: {result}")
        return result

    def _validate(self, raw: str) -> tuple[bool, Any]:
        try:
            return True, json.loads(raw.strip())
        except json.JSONDecodeError as e:
            return False, str(e)


@dataclass
class PromptPipeline:
    pipeline_id: str
    version: str
    stages: list[PipelineStage] = field(default_factory=list)

    def add_stage(self, stage: PipelineStage) -> "PromptPipeline":
        self.stages.append(stage)
        return self

    def run(self, initial_input: dict) -> dict:
        """Execute all pipeline stages sequentially, accumulating state."""
        state = initial_input.copy()
        for stage in self.stages:
            stage_output = stage.execute(state)
            # Merge stage output into accumulated state
            state.update(stage_output)
            state[f"_{stage.stage_id}_output"] = stage_output
        return state
