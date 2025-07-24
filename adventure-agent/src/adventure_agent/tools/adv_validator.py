"""
ADV Validator Tool for the Adventure Generation Agent.

This tool validates generated .adv files against the JavaScript parser requirements,
ensuring syntactic correctness and structural integrity for the game engine.
"""

import re
from typing import Dict, List, Set, Tuple

from pydantic_ai import Agent, RunContext

from ..models import AdventureGame, Choice, ChoiceLabel, ToolResult


class ValidationError:
    """Represents a validation error with details."""
    
    def __init__(self, error_type: str, message: str, location: str = "", severity: str = "error"):
        self.error_type = error_type
        self.message = message
        self.location = location
        self.severity = severity  # error, warning, info
    
    def __str__(self):
        loc_str = f" at {self.location}" if self.location else ""
        return f"[{self.severity.upper()}] {self.error_type}: {self.message}{loc_str}"


class ValidationDependencies:
    """Dependencies for ADV validation."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.strict_mode = True


def create_validator_agent() -> Agent[ValidationDependencies, Dict[str, bool]]:
    """Create ADV validation agent."""
    return Agent[ValidationDependencies, Dict[str, bool]](
        'gemini-1.5-flash',
        deps_type=ValidationDependencies,
        output_type=Dict[str, bool],
        system_prompt=(
            "You are an expert .adv file format validator. Ensure complete "
            "compliance with JavaScript parser requirements, identifying all "
            "structural, syntactic, and logical errors in adventure files."
        ),
    )


async def validate_adv_format(adventure: AdventureGame) -> ToolResult:
    """
    Main validation function for .adv format compliance.
    
    Args:
        adventure: Adventure game to validate
        
    Returns:
        ToolResult with validation results and error details
    """
    try:
        deps = ValidationDependencies()
        
        # Validate required sections
        await _validate_required_sections(adventure, deps)
        
        # Validate game structure
        await _validate_game_structure(adventure, deps)
        
        # Validate steps and narrative flow
        await _validate_steps(adventure, deps)
        
        # Validate choices format
        await _validate_choices(adventure, deps)
        
        # Validate endings
        await _validate_endings(adventure, deps)
        
        # Validate inventory/stats format
        await _validate_key_value_sections(adventure, deps)
        
        # Validate story flow integrity
        await _validate_story_flow(adventure, deps)
        
        # Compile results
        has_errors = len(deps.errors) > 0
        has_warnings = len(deps.warnings) > 0
        
        all_issues = deps.errors + deps.warnings
        issues_summary = "\n".join(str(issue) for issue in all_issues)
        
        return ToolResult(
            success=not has_errors,
            data={
                "valid": not has_errors,
                "errors": [str(e) for e in deps.errors],
                "warnings": [str(w) for w in deps.warnings],
                "error_count": len(deps.errors),
                "warning_count": len(deps.warnings),
                "validation_summary": issues_summary
            },
            message=f"Validation {'passed' if not has_errors else 'failed'}: {len(deps.errors)} errors, {len(deps.warnings)} warnings",
            metadata={
                "total_issues": len(all_issues),
                "critical_errors": len([e for e in deps.errors if e.severity == "error"]),
                "sections_validated": ["structure", "choices", "flow", "format"]
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"ADV validation failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


async def _validate_required_sections(adventure: AdventureGame, deps: ValidationDependencies):
    """Validate all required sections are present."""
    
    # GAME_NAME is required
    if not adventure.game_name or not adventure.game_name.strip():
        deps.errors.append(ValidationError(
            "MISSING_SECTION",
            "Missing or empty [GAME_NAME] section",
            "GAME_NAME"
        ))
    
    # MAIN_MENU is required and must have items
    if not adventure.main_menu or len(adventure.main_menu) == 0:
        deps.errors.append(ValidationError(
            "MISSING_SECTION",
            "Missing or empty [MAIN_MENU] section",
            "MAIN_MENU"
        ))
    
    # At least one STEP is required
    if not adventure.steps or len(adventure.steps) == 0:
        deps.errors.append(ValidationError(
            "MISSING_SECTION",
            "No [STEP_X] sections found - at least one step is required",
            "STEPS"
        ))
    
    # At least one ending should be present
    if not adventure.endings or len(adventure.endings) == 0:
        deps.warnings.append(ValidationError(
            "MISSING_SECTION",
            "No endings defined - consider adding at least ENDING_SUCCESS and ENDING_FAILURE",
            "ENDINGS",
            "warning"
        ))


async def _validate_game_structure(adventure: AdventureGame, deps: ValidationDependencies):
    """Validate overall game structure."""
    
    # Validate step numbering
    step_numbers = []
    for step_id in adventure.steps.keys():
        try:
            step_num = int(step_id)
            step_numbers.append(step_num)
        except ValueError:
            deps.errors.append(ValidationError(
                "INVALID_STEP_ID",
                f"Step ID '{step_id}' is not a valid number",
                f"STEP_{step_id}"
            ))
    
    # Check for sequential numbering (warning only)
    if step_numbers:
        step_numbers.sort()
        if step_numbers[0] != 1:
            deps.warnings.append(ValidationError(
                "NUMBERING_WARNING",
                f"Steps should start from 1, but start from {step_numbers[0]}",
                "STEP_NUMBERING",
                "warning"
            ))
        
        for i in range(1, len(step_numbers)):
            if step_numbers[i] != step_numbers[i-1] + 1:
                deps.warnings.append(ValidationError(
                    "NUMBERING_WARNING",
                    f"Non-sequential step numbering: gap between {step_numbers[i-1]} and {step_numbers[i]}",
                    "STEP_NUMBERING",
                    "warning"
                ))


async def _validate_steps(adventure: AdventureGame, deps: ValidationDependencies):
    """Validate step structure and content."""
    
    for step_id, step in adventure.steps.items():
        step_location = f"STEP_{step_id}"
        
        # Validate narrative exists and has content
        if not step.narrative or not step.narrative.strip():
            deps.errors.append(ValidationError(
                "MISSING_NARRATIVE",
                "Step has empty or missing narrative",
                step_location
            ))
        elif len(step.narrative.strip()) < 10:
            deps.warnings.append(ValidationError(
                "SHORT_NARRATIVE",
                f"Step narrative is very short ({len(step.narrative.strip())} chars)",
                step_location,
                "warning"
            ))
        
        # Validate choices exist
        if not step.choices or len(step.choices) == 0:
            deps.errors.append(ValidationError(
                "MISSING_CHOICES",
                "Step has no choices defined",
                step_location
            ))
        elif len(step.choices) > 4:
            deps.warnings.append(ValidationError(
                "TOO_MANY_CHOICES",
                f"Step has {len(step.choices)} choices (more than typical A-D limit)",
                step_location,
                "warning"
            ))


async def _validate_choices(adventure: AdventureGame, deps: ValidationDependencies):
    """Validate choice format and targets."""
    
    valid_targets = set()
    # Add all step targets
    for step_id in adventure.steps.keys():
        valid_targets.add(f"STEP_{step_id}")
    
    # Add ending targets
    valid_targets.update(["ENDING_SUCCESS", "ENDING_FAILURE", "ENDING_NEUTRAL"])
    
    # Add custom endings
    for ending_key in adventure.endings.keys():
        if ending_key not in ["success", "failure", "neutral"]:
            valid_targets.add(f"ENDING_{ending_key.upper()}")
    
    for step_id, step in adventure.steps.items():
        step_location = f"STEP_{step_id}"
        
        choice_labels_used = set()
        
        for i, choice in enumerate(step.choices):
            choice_location = f"{step_location}.CHOICE_{i+1}"
            
            # Validate choice label
            if not choice.label:
                deps.errors.append(ValidationError(
                    "MISSING_CHOICE_LABEL",
                    "Choice has missing label",
                    choice_location
                ))
            else:
                # Check label format (should be A, B, C, or D)
                if choice.label not in [ChoiceLabel.A, ChoiceLabel.B, ChoiceLabel.C, ChoiceLabel.D]:
                    deps.errors.append(ValidationError(
                        "INVALID_CHOICE_LABEL",
                        f"Choice label '{choice.label}' is not valid (must be A, B, C, or D)",
                        choice_location
                    ))
                
                # Check for duplicate labels
                if choice.label in choice_labels_used:
                    deps.errors.append(ValidationError(
                        "DUPLICATE_CHOICE_LABEL",
                        f"Duplicate choice label '{choice.label}' in step",
                        choice_location
                    ))
                choice_labels_used.add(choice.label)
            
            # Validate choice description
            if not choice.description or not choice.description.strip():
                deps.errors.append(ValidationError(
                    "MISSING_CHOICE_DESCRIPTION",
                    "Choice has empty or missing description",
                    choice_location
                ))
            elif len(choice.description.strip()) < 5:
                deps.warnings.append(ValidationError(
                    "SHORT_CHOICE_DESCRIPTION",
                    f"Choice description is very short ({len(choice.description.strip())} chars)",
                    choice_location,
                    "warning"
                ))
            
            # Validate choice target
            if not choice.target:
                deps.errors.append(ValidationError(
                    "MISSING_CHOICE_TARGET",
                    "Choice has missing target",
                    choice_location
                ))
            elif choice.target not in valid_targets:
                deps.errors.append(ValidationError(
                    "INVALID_CHOICE_TARGET",
                    f"Choice target '{choice.target}' is not valid (available: {sorted(valid_targets)})",
                    choice_location
                ))
            
            # Validate conditions format
            await _validate_conditions(choice.conditions, choice_location, deps)
            
            # Validate consequences format
            await _validate_consequences(choice.consequences, choice_location, deps)


async def _validate_conditions(conditions: List[str], location: str, deps: ValidationDependencies):
    """Validate condition format."""
    
    for i, condition in enumerate(conditions):
        condition_location = f"{location}.CONDITION_{i+1}"
        
        if not condition.strip():
            deps.warnings.append(ValidationError(
                "EMPTY_CONDITION",
                "Empty condition found",
                condition_location,
                "warning"
            ))
            continue
        
        # Check basic condition format patterns
        condition_lower = condition.lower().strip()
        
        # Should start with common condition keywords
        valid_starts = ["if ", "inventory.", "stats.", "variables.", "health", "reputation"]
        
        if not any(condition_lower.startswith(start) for start in valid_starts):
            deps.warnings.append(ValidationError(
                "UNUSUAL_CONDITION",
                f"Condition '{condition}' doesn't follow typical patterns",
                condition_location,
                "warning"
            ))


async def _validate_consequences(consequences: List[str], location: str, deps: ValidationDependencies):
    """Validate consequence format."""
    
    for i, consequence in enumerate(consequences):
        consequence_location = f"{location}.CONSEQUENCE_{i+1}"
        
        if not consequence.strip():
            deps.warnings.append(ValidationError(
                "EMPTY_CONSEQUENCE",
                "Empty consequence found",
                consequence_location,
                "warning"
            ))
            continue
        
        # Check basic consequence format patterns
        consequence_upper = consequence.upper().strip()
        
        # Should start with action keywords
        valid_starts = ["SET ", "USE ", "ADD ", "REMOVE ", "INCREASE ", "DECREASE "]
        
        if not any(consequence_upper.startswith(start) for start in valid_starts):
            deps.warnings.append(ValidationError(
                "UNUSUAL_CONSEQUENCE",
                f"Consequence '{consequence}' doesn't follow typical action patterns",
                consequence_location,
                "warning"
            ))


async def _validate_endings(adventure: AdventureGame, deps: ValidationDependencies):
    """Validate ending structure and content."""
    
    # Check for standard endings
    standard_endings = ["success", "failure", "neutral"]
    missing_standard = []
    
    for ending_type in standard_endings:
        if ending_type not in adventure.endings or not adventure.endings[ending_type]:
            missing_standard.append(ending_type)
    
    if missing_standard:
        deps.warnings.append(ValidationError(
            "MISSING_STANDARD_ENDING",
            f"Missing standard endings: {', '.join(missing_standard)}",
            "ENDINGS",
            "warning"
        ))
    
    # Validate ending content
    for ending_type, ending_text in adventure.endings.items():
        ending_location = f"ENDING_{ending_type.upper()}"
        
        if not ending_text or not ending_text.strip():
            deps.errors.append(ValidationError(
                "EMPTY_ENDING",
                f"Ending '{ending_type}' has empty content",
                ending_location
            ))
        elif len(ending_text.strip()) < 20:
            deps.warnings.append(ValidationError(
                "SHORT_ENDING",
                f"Ending '{ending_type}' is very short ({len(ending_text.strip())} chars)",
                ending_location,
                "warning"
            ))


async def _validate_key_value_sections(adventure: AdventureGame, deps: ValidationDependencies):
    """Validate inventory, stats, and variables format."""
    
    # Validate inventory
    if adventure.inventory:
        await _validate_key_value_dict("INVENTORY", adventure.inventory, deps)
    
    # Validate stats
    if adventure.stats:
        await _validate_key_value_dict("STATS", adventure.stats, deps)
    
    # Validate variables
    if adventure.variables:
        await _validate_key_value_dict("VARIABLES", adventure.variables, deps)


async def _validate_key_value_dict(section_name: str, data: Dict, deps: ValidationDependencies):
    """Validate key-value dictionary format."""
    
    for key, value in data.items():
        location = f"{section_name}.{key}"
        
        # Validate key format
        if not key or not isinstance(key, str):
            deps.errors.append(ValidationError(
                "INVALID_KEY",
                f"Invalid key '{key}' in {section_name}",
                location
            ))
        elif not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            deps.warnings.append(ValidationError(
                "KEY_FORMAT_WARNING",
                f"Key '{key}' contains unusual characters",
                location,
                "warning"
            ))
        
        # Validate value type
        if value is None:
            deps.warnings.append(ValidationError(
                "NULL_VALUE",
                f"Null value for key '{key}' in {section_name}",
                location,
                "warning"
            ))
        elif not isinstance(value, (str, int, float, bool)):
            deps.warnings.append(ValidationError(
                "COMPLEX_VALUE",
                f"Complex value type for key '{key}' in {section_name}",
                location,
                "warning"
            ))


async def _validate_story_flow(adventure: AdventureGame, deps: ValidationDependencies):
    """Validate story flow and reachability."""
    
    # Find all reachable steps
    reachable_steps = set()
    steps_to_check = {"1"}  # Start from step 1
    
    while steps_to_check:
        current_step = steps_to_check.pop()
        if current_step in reachable_steps:
            continue
        
        reachable_steps.add(current_step)
        
        if current_step in adventure.steps:
            step = adventure.steps[current_step]
            for choice in step.choices:
                if choice.target.startswith("STEP_"):
                    target_step = choice.target.replace("STEP_", "")
                    if target_step not in reachable_steps:
                        steps_to_check.add(target_step)
    
    # Check for unreachable steps
    all_steps = set(adventure.steps.keys())
    unreachable_steps = all_steps - reachable_steps
    
    if unreachable_steps:
        deps.warnings.append(ValidationError(
            "UNREACHABLE_STEPS",
            f"Steps are unreachable from step 1: {sorted(unreachable_steps)}",
            "FLOW_ANALYSIS",
            "warning"
        ))
    
    # Check if step 1 exists
    if "1" not in adventure.steps:
        deps.errors.append(ValidationError(
            "MISSING_START_STEP",
            "No STEP_1 found - game must start with step 1",
            "STEP_1"
        ))


async def validate_choice_syntax(choice_text: str) -> bool:
    """
    Validate individual choice syntax against parser requirements.
    
    Args:
        choice_text: Raw choice text to validate
        
    Returns:
        True if syntax is valid
    """
    # Regex pattern matching the JavaScript parser
    pattern = r'^([A-D])\)\s*(.+?)\s*(?:->|→)\s*(STEP_\d+|ENDING_SUCCESS|ENDING_FAILURE|ENDING_NEUTRAL)(?:\s*\{\s*(.+?)\s*\})?$'
    
    return bool(re.match(pattern, choice_text.strip()))


async def generate_validation_report(adventure: AdventureGame) -> str:
    """
    Generate a comprehensive validation report.
    
    Args:
        adventure: Adventure to validate
        
    Returns:
        Formatted validation report
    """
    result = await validate_adv_format(adventure)
    
    lines = ["=== ADV Validation Report ===", ""]
    
    if result.success:
        lines.append("✅ VALIDATION PASSED")
    else:
        lines.append("❌ VALIDATION FAILED")
    
    lines.append("")
    lines.append(f"Summary: {result.data.get('error_count', 0)} errors, {result.data.get('warning_count', 0)} warnings")
    lines.append("")
    
    if result.data.get('errors'):
        lines.append("ERRORS:")
        for error in result.data['errors']:
            lines.append(f"  • {error}")
        lines.append("")
    
    if result.data.get('warnings'):
        lines.append("WARNINGS:")
        for warning in result.data['warnings']:
            lines.append(f"  • {warning}")
        lines.append("")
    
    # Add recommendations
    lines.append("RECOMMENDATIONS:")
    if result.data.get('error_count', 0) > 0:
        lines.append("  • Fix all errors before using the .adv file")
    if result.data.get('warning_count', 0) > 0:
        lines.append("  • Consider addressing warnings for better quality")
    if result.success:
        lines.append("  • File should load successfully in the game engine")
    
    return "\n".join(lines)


async def fix_common_validation_issues(adventure: AdventureGame) -> AdventureGame:
    """
    Automatically fix common validation issues.
    
    Args:
        adventure: Adventure to fix
        
    Returns:
        Adventure with fixes applied
    """
    fixed_adventure = adventure.model_copy()
    
    # Fix missing game name
    if not fixed_adventure.game_name or not fixed_adventure.game_name.strip():
        fixed_adventure.game_name = "Generated Adventure"
    
    # Fix missing main menu
    if not fixed_adventure.main_menu:
        fixed_adventure.main_menu = ["Start New Game", "Load Game", "Exit"]
    
    # Fix missing endings
    if not fixed_adventure.endings:
        fixed_adventure.endings = {}
    
    if "success" not in fixed_adventure.endings:
        fixed_adventure.endings["success"] = "Congratulations! You have successfully completed the adventure."
    
    if "failure" not in fixed_adventure.endings:
        fixed_adventure.endings["failure"] = "Your adventure has ended. Better luck next time!"
    
    # Fix empty choice descriptions
    for step_id, step in fixed_adventure.steps.items():
        for choice in step.choices:
            if not choice.description or not choice.description.strip():
                choice.description = f"Continue with option {choice.label.value}"
    
    return fixed_adventure