"""Instructional Mission — screenshots + final target result.

Key rule from the plan: the student must always be able to see the target
end result while doing the steps. The schema enforces `final_result_image_id`.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from game_content_system.core.base import ContentBase
from game_content_system.core.enums import GameType, ProofType, ReviewMode
from game_content_system.core.validation import ValidationResult


@dataclass
class InstructionalStep:
    order: int
    screenshot_asset_id: str
    instruction: str
    tip: Optional[str] = None
    warning: Optional[str] = None


@dataclass
class InstructionalMission(ContentBase):
    game_type: GameType = GameType.INSTRUCTIONAL_MISSION
    goal: str = ""
    final_result_image_asset_id: str = ""
    steps: List[InstructionalStep] = field(default_factory=list)
    required_proof_type: ProofType = ProofType.SCREENSHOT
    submission_instructions: str = ""
    pass_rule: str = ""

    def validate(self) -> ValidationResult:
        result = self.validate_base()

        if self.game_type != GameType.INSTRUCTIONAL_MISSION:
            result.add_error("game_type must be instructional_mission")
        if not self.goal.strip():
            result.add_error("goal is required")
        if not self.final_result_image_asset_id:
            result.add_error("final_result_image_asset_id is required (students must see the target)")
        if not self.steps:
            result.add_error("must have at least 1 step")
        if not self.submission_instructions.strip():
            result.add_error("submission_instructions is required")
        if not self.pass_rule.strip():
            result.add_error("pass_rule is required")

        seen_orders = set()
        for i, step in enumerate(self.steps):
            prefix = f"step[{i}]"
            if not step.screenshot_asset_id:
                result.add_error(f"{prefix}: screenshot_asset_id is required")
            if not step.instruction.strip():
                result.add_error(f"{prefix}: instruction is required")
            if step.order in seen_orders:
                result.add_error(f"{prefix}: duplicate order {step.order}")
            seen_orders.add(step.order)

        if self.required_proof_type == ProofType.TEXT and \
                self.moderation.review_mode == ReviewMode.AUTO_PASS:
            result.add_warning(
                "text proof with auto_pass — consider manual review so students "
                "cannot pass with empty text"
            )
        return result
