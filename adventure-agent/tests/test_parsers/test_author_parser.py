"""
Tests for the author file parser.
"""

import pytest
from adventure_agent.parsers.author_parser import parse_author_file
from adventure_agent.models import AuthorPersona


class TestAuthorParser:
    """Test the author file parsing functionality."""
    
    def test_parse_complete_author_file(self):
        """Test parsing a complete author file."""
        content = """
# Voice and Tone
- Witty and satirical
- Humorous undertones
- Ironic observations

# Narrative Style
- Descriptive prose
- Character-driven storytelling
- Third-person omniscient

# World Elements
- Fantasy setting with modern sensibilities
- Magical bureaucracy
- Anthropomorphic Death

# Character Development
- Growth through adversity
- Humor in the face of tragedy
- Reluctant heroes

# Themes
- Good vs evil (but it's complicated)
- The power of friendship
- Bureaucracy and society
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 3
        assert "Witty and satirical" in author.voice_and_tone
        assert "Humorous undertones" in author.voice_and_tone
        assert "Ironic observations" in author.voice_and_tone
        
        assert len(author.narrative_style) == 3
        assert "Descriptive prose" in author.narrative_style
        assert "Character-driven storytelling" in author.narrative_style
        
        assert len(author.world_elements) == 3
        assert "Fantasy setting with modern sensibilities" in author.world_elements
        
        assert len(author.character_development) == 3
        assert "Growth through adversity" in author.character_development
        
        assert len(author.themes) == 3
        assert "Good vs evil (but it's complicated)" in author.themes
    
    def test_parse_minimal_author_file(self):
        """Test parsing a minimal author file."""
        content = """
# Voice and Tone
- Simple tone

# Narrative Style
- Basic style

# World Elements
- Generic fantasy

# Character Development
- Standard growth

# Themes
- Basic theme
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 1
        assert len(author.narrative_style) == 1
        assert len(author.world_elements) == 1
        assert len(author.character_development) == 1
        assert len(author.themes) == 1
    
    def test_parse_author_file_with_extra_whitespace(self):
        """Test parsing author file with extra whitespace."""
        content = """

# Voice and Tone

- Witty and satirical   

- Humorous undertones


# Narrative Style

- Descriptive prose   

# World Elements
- Fantasy setting

# Character Development
- Growth through adversity

# Themes
- Good vs evil

"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 2
        assert "Witty and satirical" in author.voice_and_tone
        assert "Humorous undertones" in author.voice_and_tone
    
    def test_parse_author_file_mixed_case_headers(self):
        """Test parsing author file with mixed case headers."""
        content = """
# voice and tone
- Witty style

# NARRATIVE STYLE
- Descriptive

# World elements
- Fantasy

# Character Development
- Growth

# themes
- Adventure
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 1
        assert len(author.narrative_style) == 1
        assert len(author.world_elements) == 1
        assert len(author.character_development) == 1
        assert len(author.themes) == 1
    
    def test_parse_author_file_with_numbered_lists(self):
        """Test parsing author file with numbered lists instead of bullets."""
        content = """
# Voice and Tone
1. Witty and satirical
2. Humorous undertones

# Narrative Style
1. Descriptive prose

# World Elements
1. Fantasy setting

# Character Development
1. Growth through adversity

# Themes
1. Good vs evil
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 2
        assert "Witty and satirical" in author.voice_and_tone
        assert "Humorous undertones" in author.voice_and_tone
    
    def test_parse_author_file_missing_sections(self):
        """Test parsing author file with missing sections."""
        content = """
# Voice and Tone
- Witty style

# Themes
- Adventure theme
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 1
        assert len(author.narrative_style) == 0  # Missing section
        assert len(author.world_elements) == 0   # Missing section
        assert len(author.character_development) == 0  # Missing section
        assert len(author.themes) == 1
    
    def test_parse_author_file_empty_sections(self):
        """Test parsing author file with empty sections."""
        content = """
# Voice and Tone
- Witty style

# Narrative Style

# World Elements
- Fantasy setting

# Character Development

# Themes
- Adventure
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 1
        assert len(author.narrative_style) == 0  # Empty section
        assert len(author.world_elements) == 1
        assert len(author.character_development) == 0  # Empty section
        assert len(author.themes) == 1
    
    def test_parse_author_file_special_characters(self):
        """Test parsing author file with special characters."""
        content = """
# Voice and Tone
- "Witty" & satirical (with quotes)
- Humorous—with dashes
- Café-style narrative

# Narrative Style
- Stream-of-consciousness
- Déjà vu themes

# World Elements
- Fantasy™ setting
- 21st-century magic

# Character Development
- Growth → transformation

# Themes
- Good vs. evil: it's complicated!
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 3
        assert ""Witty" & satirical (with quotes)" in author.voice_and_tone
        assert "Humorous—with dashes" in author.voice_and_tone
        assert "Café-style narrative" in author.voice_and_tone
    
    def test_parse_author_file_long_entries(self):
        """Test parsing author file with very long entries."""
        content = """
# Voice and Tone
- This is a very long voice and tone description that spans multiple concepts and ideas, including wit, satire, humor, irony, and various other literary devices that make the writing engaging and memorable for readers
- Short entry

# Narrative Style
- Complex multi-layered narrative structure with interconnected plotlines, character arcs, and thematic elements that weave together to create a rich tapestry of storytelling

# World Elements
- Elaborate fantasy world

# Character Development
- Detailed character growth

# Themes
- Complex themes
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 2
        assert len(author.voice_and_tone[0]) > 100  # Long entry
        assert len(author.voice_and_tone[1]) < 20   # Short entry
    
    def test_parse_empty_author_file(self):
        """Test parsing an empty author file."""
        content = ""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 0
        assert len(author.narrative_style) == 0
        assert len(author.world_elements) == 0
        assert len(author.character_development) == 0
        assert len(author.themes) == 0
    
    def test_parse_author_file_only_headers(self):
        """Test parsing author file with only headers and no content."""
        content = """
# Voice and Tone
# Narrative Style
# World Elements
# Character Development
# Themes
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        assert len(author.voice_and_tone) == 0
        assert len(author.narrative_style) == 0
        assert len(author.world_elements) == 0
        assert len(author.character_development) == 0
        assert len(author.themes) == 0
    
    def test_parse_author_file_duplicate_entries(self):
        """Test parsing author file with duplicate entries."""
        content = """
# Voice and Tone
- Witty style
- Witty style
- Different style
- Witty style

# Narrative Style
- Descriptive

# World Elements
- Fantasy

# Character Development
- Growth

# Themes
- Adventure
"""
        
        author = parse_author_file(content)
        
        assert isinstance(author, AuthorPersona)
        # Should contain duplicates as the parser doesn't deduplicate
        assert len(author.voice_and_tone) == 4
        assert author.voice_and_tone.count("Witty style") == 3