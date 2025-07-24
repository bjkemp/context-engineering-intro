"""
Story file parser for converting .story files to StoryRequirements models.

This module handles parsing of markdown-formatted .story files that contain
story requirements including setting, characters, plot, and technical constraints.
"""

import re
from pathlib import Path

from ..models import StoryRequirements


def parse_story_file(file_path: str) -> StoryRequirements:
    """
    Parse a .story file and return a StoryRequirements model.
    
    Args:
        file_path: Path to the .story file
        
    Returns:
        StoryRequirements model with parsed data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Story file not found: {file_path}")
    
    if not path.suffix == ".story":
        raise ValueError(f"File must have .story extension: {file_path}")
    
    content = path.read_text(encoding="utf-8")
    return parse_story_content(content)


def parse_story_content(content: str) -> StoryRequirements:
    """
    Parse story content from string and return StoryRequirements model.
    
    Args:
        content: Raw content of .story file
        
    Returns:
        StoryRequirements model with parsed data
        
    Raises:
        ValueError: If required sections are missing
    """
    # Extract sections using regex patterns
    sections = _extract_sections(content)
    
    # Parse setting information
    setting = _parse_setting_section(sections.get("setting and location", ""))
    
    # Parse main character
    main_character = _parse_main_character_section(sections.get("main character", ""))
    
    # Parse plot
    plot = _parse_plot_section(sections.get("core mystery/plot", "") or sections.get("plot", ""))
    
    # Parse NPCs
    npcs = _parse_npcs_section(sections.get("key npcs to include", "") or sections.get("npcs", ""))
    
    # Parse branches
    branches = _parse_branches_section(sections.get("story branches and choices", "") or sections.get("branches", ""))
    
    # Parse technical requirements
    technical_requirements = _parse_technical_requirements(sections.get("technical requirements", ""))
    
    # Validate required fields
    if not setting:
        raise ValueError("Missing or empty 'Setting and Location' section")
    if not main_character:
        raise ValueError("Missing or empty 'Main Character' section")
    if not plot:
        raise ValueError("Missing or empty plot section")
    
    return StoryRequirements(
        setting=setting,
        main_character=main_character,
        plot=plot,
        npcs=npcs,
        branches=branches,
        technical_requirements=technical_requirements,
    )


def _extract_sections(content: str) -> dict[str, str]:
    """
    Extract markdown sections from content.
    
    Args:
        content: Raw markdown content
        
    Returns:
        Dict mapping section names to their content
    """
    sections = {}
    current_section = None
    current_content: list[str] = []
    
    lines = content.split("\n")
    
    for line in lines:
        # Check if this is a section header (# Header or ## Header)
        header_match = re.match(r"^#{1,2}\s+(.+)$", line.strip())
        if header_match:
            # Save previous section if it exists
            if current_section:
                sections[current_section.lower()] = "\n".join(current_content).strip()
            
            # Start new section
            current_section = header_match.group(1)
            current_content = []
        else:
            # Add content to current section
            if current_section:
                current_content.append(line)
    
    # Save the last section
    if current_section:
        sections[current_section.lower()] = "\n".join(current_content).strip()
    
    return sections


def _parse_setting_section(section_content: str) -> dict[str, str]:
    """
    Parse setting section into structured data.
    
    Args:
        section_content: Raw setting section content
        
    Returns:
        Dict with setting details
    """
    setting = {}
    
    if not section_content.strip():
        return {"location": "unspecified", "time": "present day"}
    
    lines = section_content.split("\n")
    
    for line in lines:
        line = line.strip()
        # Match bullet points with bold labels
        bullet_match = re.match(r"^[-*+]\s+\*\*(.*?)\*\*:\s*(.+)$", line)
        if bullet_match:
            key = bullet_match.group(1).lower().replace(" ", "_")
            value = bullet_match.group(2).strip()
            setting[key] = value
    
    # Ensure we have at least location and time
    if "primary_location" in setting:
        setting["location"] = setting["primary_location"]
    if "location" not in setting:
        setting["location"] = "fantasy world"
    
    if "time_period" in setting:
        setting["time"] = setting["time_period"]
    if "time" not in setting:
        setting["time"] = "present day"
    
    return setting


def _parse_main_character_section(section_content: str) -> dict[str, str]:
    """
    Parse main character section into structured data.
    
    Args:
        section_content: Raw main character section content
        
    Returns:
        Dict with character details
    """
    character = {}
    
    if not section_content.strip():
        return {"background": "unknown", "motivation": "adventure"}
    
    lines = section_content.split("\n")
    
    for line in lines:
        line = line.strip()
        # Match bullet points with bold labels
        bullet_match = re.match(r"^[-*+]\s+\*\*(.*?)\*\*:\s*(.+)$", line)
        if bullet_match:
            key = bullet_match.group(1).lower().replace(" ", "_")
            value = bullet_match.group(2).strip()
            character[key] = value
    
    # Ensure we have basic character info
    if "protagonist" in character:
        character["background"] = character["protagonist"]
    if "starting_situation" in character:
        character["motivation"] = character["starting_situation"]
    
    if "background" not in character:
        character["background"] = "adventurer"
    if "motivation" not in character:
        character["motivation"] = "seeking adventure"
    
    return character


def _parse_plot_section(section_content: str) -> str:
    """
    Parse plot section and extract main plot description.
    
    Args:
        section_content: Raw plot section content
        
    Returns:
        Plot description string
    """
    if not section_content.strip():
        return "A mysterious adventure unfolds."
    
    # Clean up the content and return first substantial paragraph
    paragraphs = [p.strip() for p in section_content.split("\n\n") if p.strip()]
    
    if paragraphs:
        plot = paragraphs[0]
        # Remove markdown formatting
        plot = re.sub(r"\*\*(.*?)\*\*", r"\1", plot)
        plot = re.sub(r"\*(.*?)\*", r"\1", plot)
        return plot
    
    return "A mysterious adventure unfolds."


def _parse_npcs_section(section_content: str) -> list[dict[str, str]]:
    """
    Parse NPCs section into list of character dicts.
    
    Args:
        section_content: Raw NPCs section content
        
    Returns:
        List of NPC dictionaries
    """
    npcs: list[dict[str, str]] = []
    
    if not section_content.strip():
        return npcs
    
    lines = section_content.split("\n")
    
    for line in lines:
        line = line.strip()
        # Match bullet points with bold character names and descriptions
        bullet_match = re.match(r"^[-*+]\s+\*\*(.*?)\*\*:\s*(.+)$", line)
        if bullet_match:
            name = bullet_match.group(1).strip()
            description = bullet_match.group(2).strip()
            npcs.append({
                "name": name,
                "description": description,
                "role": "supporting character"
            })
    
    return npcs


def _parse_branches_section(section_content: str) -> list[dict[str, str]]:
    """
    Parse story branches section into list of branch dicts.
    
    Args:
        section_content: Raw branches section content
        
    Returns:
        List of branch dictionaries
    """
    branches: list[dict[str, str]] = []
    
    if not section_content.strip():
        return branches
    
    # Split by numbered items (1., 2., 3.)
    numbered_sections = re.split(r"\n\d+\.\s+", section_content)
    
    for i, section in enumerate(numbered_sections):
        if not section.strip():
            continue
            
        # Extract the path name (usually in bold)
        path_match = re.search(r"\*\*(.*?Path)\*\*:\s*(.+)", section)
        if path_match:
            path_name = path_match.group(1)
            description = path_match.group(2)
            
            branches.append({
                "name": path_name,
                "description": description,
                "type": "major_branch"
            })
    
    return branches


def _parse_technical_requirements(section_content: str) -> dict[str, str | int | list[str]]:
    """
    Parse technical requirements section.
    
    Args:
        section_content: Raw technical requirements section content
        
    Returns:
        Dict with technical constraints
    """
    requirements: dict[str, str | int | list[str]] = {}
    
    if not section_content.strip():
        return {"length": 10, "endings": 3}
    
    lines = section_content.split("\n")
    
    for line in lines:
        line = line.strip()
        # Match bullet points with bold labels
        bullet_match = re.match(r"^[-*+]\s+\*\*(.*?)\*\*:\s*(.+)$", line)
        if bullet_match:
            key = bullet_match.group(1).lower().replace(" ", "_")
            value_str = bullet_match.group(2).strip()
            
            # Try to parse numbers
            number_match = re.search(r"(\d+)", value_str)
            if number_match and key in ["length", "endings", "steps"]:
                requirements[key] = int(number_match.group(1))
            else:
                requirements[key] = value_str
    
    # Set defaults
    if "length" not in requirements:
        requirements["length"] = 10
    if "endings" not in requirements:
        requirements["endings"] = 3
    
    return requirements


def validate_story_file(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate a .story file and return validation results.
    
    Args:
        file_path: Path to the .story file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        story = parse_story_file(file_path)
        
        # Additional validation
        if len(story.plot) < 20:
            errors.append("Plot description should be more detailed")
        
        if not story.setting.get("location"):
            errors.append("Setting should include a location")
            
        if not story.main_character.get("background"):
            errors.append("Main character should have background information")
            
    except Exception as e:
        errors.append(str(e))
    
    return len(errors) == 0, errors