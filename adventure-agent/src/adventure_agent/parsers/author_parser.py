"""
Author file parser for converting .author files to AuthorPersona models.

This module handles parsing of markdown-formatted .author files that contain
author persona information including voice, tone, narrative style, and themes.
"""

import re
from pathlib import Path

from ..models import AuthorPersona


def parse_author_file(file_path: str) -> AuthorPersona:
    """
    Parse a .author file and return an AuthorPersona model.
    
    Args:
        file_path: Path to the .author file
        
    Returns:
        AuthorPersona model with parsed data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Author file not found: {file_path}")
    
    if not path.suffix == ".author":
        raise ValueError(f"File must have .author extension: {file_path}")
    
    content = path.read_text(encoding="utf-8")
    return parse_author_content(content)


def parse_author_content(content: str) -> AuthorPersona:
    """
    Parse author content from string and return AuthorPersona model.
    
    Args:
        content: Raw content of .author file
        
    Returns:
        AuthorPersona model with parsed data
        
    Raises:
        ValueError: If required sections are missing
    """
    # Extract sections using regex patterns
    sections = _extract_sections(content)
    
    # Parse each section into lists
    voice_and_tone = _parse_list_section(sections.get("voice and tone", ""))
    narrative_style = _parse_list_section(sections.get("narrative style", ""))
    world_elements = _parse_list_section(
        sections.get("discworld elements to include", "") or 
        sections.get("world elements", "")
    )
    character_development = _parse_list_section(sections.get("character development", ""))
    themes = _parse_list_section(
        sections.get("themes to explore", "") or 
        sections.get("themes", "")
    )
    
    # Validate required sections
    if not voice_and_tone:
        raise ValueError("Missing or empty 'Voice and Tone' section")
    if not narrative_style:
        raise ValueError("Missing or empty 'Narrative Style' section")
    if not character_development:
        raise ValueError("Missing or empty 'Character Development' section")
    if not themes:
        raise ValueError("Missing or empty 'Themes' section")
    
    # World elements is optional but defaults to generic if missing
    if not world_elements:
        world_elements = ["fantasy setting", "rich world-building"]
    
    return AuthorPersona(
        voice_and_tone=voice_and_tone,
        narrative_style=narrative_style,
        world_elements=world_elements,
        character_development=character_development,
        themes=themes,
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


def _parse_list_section(section_content: str) -> list[str]:
    """
    Parse a section containing bullet points into a list.
    
    Args:
        section_content: Raw section content with bullet points
        
    Returns:
        List of cleaned bullet point items
    """
    if not section_content.strip():
        return []
    
    items = []
    lines = section_content.split("\n")
    
    for line in lines:
        line = line.strip()
        # Match bullet points (-, *, +)
        bullet_match = re.match(r"^[-*+]\s+(.+)$", line)
        if bullet_match:
            item = bullet_match.group(1).strip()
            # Clean up formatting
            item = re.sub(r"\*\*(.*?)\*\*", r"\1", item)  # Remove bold
            item = re.sub(r"\*(.*?)\*", r"\1", item)  # Remove italics
            item = re.sub(r"`(.*?)`", r"\1", item)  # Remove code formatting
            items.append(item)
    
    return items


def validate_author_file(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate an .author file and return validation results.
    
    Args:
        file_path: Path to the .author file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        author = parse_author_file(file_path)
        
        # Additional validation
        if len(author.voice_and_tone) < 2:
            errors.append("Voice and tone should have at least 2 characteristics")
        
        if len(author.narrative_style) < 2:
            errors.append("Narrative style should have at least 2 elements")
            
        if len(author.themes) < 2:
            errors.append("Themes should have at least 2 elements")
            
    except Exception as e:
        errors.append(str(e))
    
    return len(errors) == 0, errors