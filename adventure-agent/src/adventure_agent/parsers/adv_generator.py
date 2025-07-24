"""
ADV file generator for converting AdventureGame models to .adv format.

This module handles generation of .adv files that are compatible with the
JavaScript game engine's fileParser.js requirements.
"""

from pathlib import Path

from ..models import AdventureGame, Choice, EndingType


def generate_adv_file(adventure: AdventureGame, output_path: str) -> None:
    """
    Generate a .adv file from an AdventureGame model.
    
    Args:
        adventure: AdventureGame model to convert
        output_path: Path where the .adv file should be saved
        
    Raises:
        ValueError: If adventure data is invalid
        IOError: If file cannot be written
    """
    adv_content = generate_adv_content(adventure)
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        path.write_text(adv_content, encoding="utf-8")
    except Exception as e:
        raise OSError(f"Failed to write .adv file: {e}") from e


def generate_adv_content(adventure: AdventureGame) -> str:
    """
    Generate .adv file content from an AdventureGame model.
    
    Args:
        adventure: AdventureGame model to convert
        
    Returns:
        String content in .adv format
        
    Raises:
        ValueError: If adventure data is invalid
    """
    # Validate required fields
    if not adventure.game_name:
        raise ValueError("Adventure must have a game name")
    if not adventure.steps:
        raise ValueError("Adventure must have at least one step")
    if not adventure.main_menu:
        raise ValueError("Adventure must have main menu items")
    
    sections = []
    
    # Game name section
    sections.append("[GAME_NAME]")
    sections.append(adventure.game_name)
    sections.append("")
    
    # Name section (whether to ask for player name)
    sections.append("[NAME]")
    sections.append("true" if adventure.ask_for_name else "false")
    sections.append("")
    
    # Main menu section
    sections.append("[MAIN_MENU]")
    for item in adventure.main_menu:
        sections.append(item)
    sections.append("")
    
    # Inventory section (if any)
    if adventure.inventory:
        sections.append("[INVENTORY]")
        for key, value in adventure.inventory.items():
            sections.append(f"{key}: {value}")
        sections.append("")
    
    # Stats section (if any)
    if adventure.stats:
        sections.append("[STATS]")
        for key, value in adventure.stats.items():
            sections.append(f"{key}: {value}")
        sections.append("")
    
    # Variables section (if any)
    if adventure.variables:
        sections.append("[VARIABLES]")
        for key, value in adventure.variables.items():
            sections.append(f"{key}: {value}")
        sections.append("")
    
    # Story steps (sorted by step ID)
    step_ids = sorted(adventure.steps.keys(), key=lambda x: int(x))
    
    for step_id in step_ids:
        step = adventure.steps[step_id]
        
        sections.append(f"[STEP_{step_id}]")
        
        # Narrative section
        sections.append("[NARRATIVE]")
        sections.append(step.narrative)
        sections.append("[/NARRATIVE]")
        
        # Choices section
        sections.append("[CHOICES]")
        for choice in step.choices:
            choice_line = _format_choice(choice)
            sections.append(choice_line)
        sections.append("[/CHOICES]")
        
        sections.append("")
    
    # Endings
    for ending_type, ending_text in adventure.endings.items():
        if ending_text.strip():  # Only include non-empty endings
            ending_key = _format_ending_key(ending_type)
            sections.append(f"[{ending_key}]")
            sections.append(ending_text)
            sections.append("")
    
    return "\n".join(sections)


def _format_choice(choice: Choice) -> str:
    """
    Format a choice according to .adv file requirements.
    
    The format is: "A) Description → TARGET {conditions; consequences}"
    
    Args:
        choice: Choice model to format
        
    Returns:
        Formatted choice string
    """
    # Basic choice format
    choice_str = f"{choice.label.value}) {choice.description} → {choice.target}"
    
    # Add conditions and consequences if present
    extras = []
    
    for condition in choice.conditions:
        extras.append(f"IF {condition}")
    
    for consequence in choice.consequences:
        extras.append(consequence)
    
    if extras:
        extras_str = "; ".join(extras)
        choice_str += f" {{{extras_str}}}"
    
    return choice_str


def _format_ending_key(ending_type: EndingType) -> str:
    """
    Format ending type to proper .adv section key.
    
    Args:
        ending_type: EndingType enum value
        
    Returns:
        Properly formatted section key
    """
    return f"ENDING_{ending_type.value.upper()}"


def validate_adv_structure(adventure: AdventureGame) -> tuple[bool, list[str]]:
    """
    Validate an AdventureGame for .adv file generation.
    
    Args:
        adventure: AdventureGame model to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    if not adventure.game_name:
        errors.append("Missing game name")
    
    if not adventure.main_menu:
        errors.append("Missing main menu items")
    
    if not adventure.steps:
        errors.append("Missing story steps")
    
    # Validate steps
    for step_id, step in adventure.steps.items():
        if not step.narrative:
            errors.append(f"Step {step_id} missing narrative")
        
        if not step.choices:
            errors.append(f"Step {step_id} missing choices")
        
        # Check that all choice targets are valid
        for choice in step.choices:
            target = choice.target
            
            # Check if target is a valid step
            if target.startswith("STEP_"):
                target_id = target.replace("STEP_", "")
                if target_id not in adventure.steps:
                    errors.append(f"Step {step_id} choice '{choice.label.value}' targets non-existent step: {target}")
            
            # Check if target is a valid ending
            elif target.startswith("ENDING_"):
                ending_type = target.replace("ENDING_", "").lower()
                if ending_type not in [e.value for e in EndingType]:
                    errors.append(f"Step {step_id} choice '{choice.label.value}' targets invalid ending: {target}")
            
            else:
                errors.append(f"Step {step_id} choice '{choice.label.value}' has invalid target format: {target}")
    
    # Check for unreachable steps
    reachable_steps: set[str] = set()
    _find_reachable_steps(adventure, "1", reachable_steps)
    
    for step_id in adventure.steps:
        if step_id not in reachable_steps and step_id != "1":
            errors.append(f"Step {step_id} is unreachable from the starting step")
    
    # Check that we have at least one ending
    if not adventure.endings:
        errors.append("Adventure should have at least one ending")
    
    return len(errors) == 0, errors


def _find_reachable_steps(adventure: AdventureGame, step_id: str, visited: set[str]) -> None:
    """
    Recursively find all reachable steps from a given starting step.
    
    Args:
        adventure: AdventureGame model
        step_id: Current step ID to explore
        visited: Set of already visited step IDs
    """
    if step_id in visited or step_id not in adventure.steps:
        return
    
    visited.add(step_id)
    
    # Follow all choices from this step
    step = adventure.steps[step_id]
    for choice in step.choices:
        if choice.target.startswith("STEP_"):
            target_id = choice.target.replace("STEP_", "")
            _find_reachable_steps(adventure, target_id, visited)


def preview_adv_structure(adventure: AdventureGame) -> str:
    """
    Generate a text preview of the adventure structure.
    
    Args:
        adventure: AdventureGame model to preview
        
    Returns:
        Human-readable structure preview
    """
    lines = []
    
    lines.append(f"Adventure: {adventure.game_name}")
    lines.append(f"Steps: {len(adventure.steps)}")
    lines.append(f"Endings: {len(adventure.endings)}")
    lines.append("")
    
    # Step flow
    lines.append("Step Flow:")
    step_ids = sorted(adventure.steps.keys(), key=lambda x: int(x))
    
    for step_id in step_ids:
        step = adventure.steps[step_id]
        lines.append(f"  STEP_{step_id}: {len(step.choices)} choices")
        
        for choice in step.choices:
            lines.append(f"    {choice.label.value}) → {choice.target}")
    
    lines.append("")
    
    # Endings
    if adventure.endings:
        lines.append("Endings:")
        for ending_type, ending_text in adventure.endings.items():
            preview = ending_text[:50] + "..." if len(ending_text) > 50 else ending_text
            lines.append(f"  {ending_type.value.upper()}: {preview}")
    
    return "\n".join(lines)