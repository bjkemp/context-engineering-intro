"""Adventure Format Validator MCP Tool.

This tool validates .adv file format and structure for game engine compatibility.
It uses the existing validation logic from the adventure-agent codebase.
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of adventure format validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    structure_info: Dict[str, Any]


async def validate_adventure_format(adventure_content: str, strict_mode: bool = True) -> Dict[str, Any]:
    """
    Validate .adv file format and structure.
    
    Args:
        adventure_content: Content of the .adv file to validate
        strict_mode: Enable strict validation mode
        
    Returns:
        Dict containing validation results
    """
    try:
        result = _validate_adv_content(adventure_content, strict_mode)
        
        return {
            "success": True,
            "valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
            "structure_info": result.structure_info,
            "summary": f"Validation {'passed' if result.is_valid else 'failed'}: {len(result.errors)} errors, {len(result.warnings)} warnings"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}",
            "valid": False,
            "errors": [str(e)],
            "warnings": [],
            "suggestions": ["Check file format and content structure"]
        }


def _validate_adv_content(content: str, strict_mode: bool) -> ValidationResult:
    """Validate adventure content structure."""
    
    errors = []
    warnings = []
    suggestions = []
    structure_info = {}
    
    # Parse sections
    sections = _parse_adv_sections(content)
    structure_info["sections_found"] = list(sections.keys())
    
    # Required sections
    required_sections = ["GAME_NAME", "MAIN_MENU"]
    for section in required_sections:
        if section not in sections:
            errors.append(f"Missing required section: [{section}]")
    
    # Check for steps
    step_sections = [key for key in sections.keys() if key.startswith("STEP_")]
    if not step_sections:
        errors.append("No [STEP_X] sections found - at least one step is required")
    else:
        structure_info["total_steps"] = len(step_sections)
        
        # Validate step numbering
        step_numbers = []
        for step_key in step_sections:
            try:
                step_num = int(step_key.replace("STEP_", ""))
                step_numbers.append(step_num)
            except ValueError:
                errors.append(f"Invalid step number in section: [{step_key}]")
        
        if step_numbers:
            step_numbers.sort()
            structure_info["step_range"] = f"{min(step_numbers)}-{max(step_numbers)}"
            
            # Check sequential numbering
            if step_numbers[0] != 1:
                warnings.append(f"Steps should start from 1, but start from {step_numbers[0]}")
            
            for i in range(1, len(step_numbers)):
                if step_numbers[i] != step_numbers[i-1] + 1:
                    warnings.append(f"Non-sequential step numbering: gap between {step_numbers[i-1]} and {step_numbers[i]}")
    
    # Check endings
    ending_sections = [key for key in sections.keys() if key.startswith("ENDING_")]
    if not ending_sections:
        warnings.append("No endings defined - consider adding at least ENDING_SUCCESS and ENDING_FAILURE")
    else:
        structure_info["total_endings"] = len(ending_sections)
        
        # Check for standard endings
        standard_endings = ["ENDING_SUCCESS", "ENDING_FAILURE", "ENDING_NEUTRAL"]
        missing_standard = [ending for ending in standard_endings if ending not in sections]
        if missing_standard:
            warnings.append(f"Missing standard endings: {', '.join(missing_standard)}")
    
    # Validate step content
    total_choices = 0
    for step_key in step_sections:
        step_content = sections[step_key]
        
        # Check for narrative
        if not step_content.strip():
            errors.append(f"Step [{step_key}] has empty content")
            continue
        
        # Look for choices
        choices = _extract_choices_from_step(step_content)
        total_choices += len(choices)
        
        if not choices:
            errors.append(f"Step [{step_key}] has no choices defined")
        else:
            # Validate choice format
            for i, choice in enumerate(choices):
                choice_errors = _validate_choice_format(choice, f"{step_key}.CHOICE_{i+1}")
                errors.extend(choice_errors)
    
    structure_info["total_choices"] = total_choices
    
    # Validate choice targets
    if step_sections:
        choice_target_errors = _validate_choice_targets(sections, step_sections, ending_sections)
        errors.extend(choice_target_errors)
    
    # Generate suggestions
    if errors:
        suggestions.append("Fix all errors before using the .adv file")
    if warnings:
        suggestions.append("Consider addressing warnings for better quality")
    if not errors and not warnings:
        suggestions.append("File structure is valid and should work with the game engine")
    
    # Add improvement suggestions
    if total_choices > 0:
        avg_choices = total_choices / len(step_sections) if step_sections else 0
        if avg_choices < 2:
            suggestions.append("Consider adding more choices per step for better player engagement")
        elif avg_choices > 4:
            suggestions.append("Consider reducing choices per step to avoid overwhelming players")
    
    is_valid = len(errors) == 0
    if strict_mode and warnings:
        is_valid = False
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
        structure_info=structure_info
    )


def _parse_adv_sections(content: str) -> Dict[str, str]:
    """Parse .adv file into sections."""
    
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Check for section headers
        if line.startswith('[') and line.endswith(']'):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            # Start new section
            current_section = line[1:-1]  # Remove brackets
            current_content = []
        else:
            if current_section:
                current_content.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections


def _extract_choices_from_step(step_content: str) -> List[str]:
    """Extract choices from step content."""
    
    choices = []
    
    # Look for choice patterns like "A) Something -> TARGET"
    choice_pattern = r'^([A-D])\)\s*(.+?)\s*(?:->|→)\s*(.+?)(?:\s*\{(.+?)\})?$'
    
    for line in step_content.split('\n'):
        line = line.strip()
        if re.match(choice_pattern, line):
            choices.append(line)
    
    return choices


def _validate_choice_format(choice: str, location: str) -> List[str]:
    """Validate individual choice format."""
    
    errors = []
    
    # Regex pattern matching the JavaScript parser
    pattern = r'^([A-D])\)\s*(.+?)\s*(?:->|→)\s*(STEP_\d+|ENDING_SUCCESS|ENDING_FAILURE|ENDING_NEUTRAL|ENDING_\w+)(?:\s*\{(.+?)\})?$'
    
    match = re.match(pattern, choice.strip())
    if not match:
        errors.append(f"Invalid choice format at {location}: '{choice}'")
        return errors
    
    label, description, target, conditions = match.groups()
    
    # Validate label
    if label not in ['A', 'B', 'C', 'D']:
        errors.append(f"Invalid choice label '{label}' at {location}")
    
    # Validate description
    if not description.strip():
        errors.append(f"Empty choice description at {location}")
    elif len(description.strip()) < 5:
        errors.append(f"Choice description too short at {location}: '{description}'")
    
    # Validate target
    if not target.strip():
        errors.append(f"Empty choice target at {location}")
    elif not (target.startswith('STEP_') or target.startswith('ENDING_')):
        errors.append(f"Invalid choice target format at {location}: '{target}'")
    
    return errors


def _validate_choice_targets(sections: Dict[str, str], step_sections: List[str], ending_sections: List[str]) -> List[str]:
    """Validate that choice targets exist."""
    
    errors = []
    
    # Build valid targets
    valid_targets = set()
    for step_key in step_sections:
        valid_targets.add(step_key)
    for ending_key in ending_sections:
        valid_targets.add(ending_key)
    
    # Add standard endings even if not defined
    valid_targets.update(["ENDING_SUCCESS", "ENDING_FAILURE", "ENDING_NEUTRAL"])
    
    # Check all choice targets
    for step_key in step_sections:
        step_content = sections[step_key]
        choices = _extract_choices_from_step(step_content)
        
        for choice in choices:
            pattern = r'^([A-D])\)\s*(.+?)\s*(?:->|→)\s*(.+?)(?:\s*\{(.+?)\})?$'
            match = re.match(pattern, choice.strip())
            
            if match:
                target = match.group(3).strip()
                if target not in valid_targets:
                    errors.append(f"Choice target '{target}' not found in [{step_key}]")
    
    return errors