"""
Tests for the story file parser.
"""

import pytest
from adventure_agent.parsers.story_parser import parse_story_file
from adventure_agent.models import StoryRequirements


class TestStoryParser:
    """Test the story file parsing functionality."""
    
    def test_parse_complete_story_file(self):
        """Test parsing a complete story file."""
        content = """
# Setting
Location: Ankh-Morpork
Time Period: Fantasy/Medieval
Atmosphere: Bustling city

# Main Character
Name: Rincewind
Background: Incompetent wizard
Motivation: Survival and avoiding responsibility
Personality: Cowardly but resourceful

# Plot
Rincewind must deliver an important message from the Unseen University to the Patrician's Palace, but various magical and mundane obstacles keep getting in his way. The message contains vital information about a brewing magical crisis.

# NPCs
- The Librarian: The orangutan librarian of Unseen University who provides cryptic assistance
- Lord Vetinari: The Patrician of Ankh-Morpork, expecting the message
- Luggage: Rincewind's magical travel chest with hundreds of little legs
- Death: May appear if things go very wrong

# Branches
- Diplomatic Approach: Try to use official channels and proper procedures
- Sneaky Route: Attempt to avoid attention and sneak through back alleys
- Magical Solution: Use unreliable magic to solve problems
- Direct Confrontation: Face obstacles head-on despite being terrible at fighting

# Technical Requirements
Length: 8-12 story steps
Branches: 3 major branching points
Endings: 3 (success, failure, neutral)
Complexity: Medium
Target Audience: Fantasy fans
Estimated Playtime: 15-20 minutes
"""
        
        story = parse_story_file(content)
        
        assert isinstance(story, StoryRequirements)
        
        # Test setting
        assert story.setting["location"] == "Ankh-Morpork"
        assert story.setting["time_period"] == "Fantasy/Medieval"
        assert story.setting["atmosphere"] == "Bustling city"
        
        # Test main character
        assert story.main_character["name"] == "Rincewind"
        assert story.main_character["background"] == "Incompetent wizard"
        assert story.main_character["motivation"] == "Survival and avoiding responsibility"
        assert story.main_character["personality"] == "Cowardly but resourceful"
        
        # Test plot
        assert "Rincewind must deliver" in story.plot
        assert "magical crisis" in story.plot
        
        # Test NPCs
        assert len(story.npcs) == 4
        librarian = next(npc for npc in story.npcs if npc["name"] == "The Librarian")
        assert librarian["description"] == "The orangutan librarian of Unseen University who provides cryptic assistance"
        
        # Test branches
        assert len(story.branches) == 4
        diplomatic = next(branch for branch in story.branches if branch["type"] == "Diplomatic Approach")
        assert "official channels" in diplomatic["description"]
        
        # Test technical requirements
        assert story.technical_requirements["length"] == "8-12 story steps"
        assert story.technical_requirements["branches"] == "3 major branching points"
        assert story.technical_requirements["endings"] == "3 (success, failure, neutral)"
        assert story.technical_requirements["complexity"] == "Medium"
    
    def test_parse_minimal_story_file(self):
        """Test parsing a minimal story file."""
        content = """
# Setting
Location: Test City

# Main Character
Name: Hero

# Plot
A simple test adventure.

# NPCs
- Merchant: Sells items

# Branches
- Choice 1: Go left or right

# Technical Requirements
Length: 5
"""
        
        story = parse_story_file(content)
        
        assert isinstance(story, StoryRequirements)
        assert story.setting["location"] == "Test City"
        assert story.main_character["name"] == "Hero"
        assert story.plot == "A simple test adventure."
        assert len(story.npcs) == 1
        assert len(story.branches) == 1
        assert story.technical_requirements["length"] == "5"
    
    def test_parse_story_file_with_multiline_plot(self):
        """Test parsing story file with multiline plot."""
        content = """
# Setting
Location: Fantasy World

# Main Character
Name: Adventurer

# Plot
This is a long plot description that spans multiple lines.
It continues on the second line with more details about the story.
And even a third line with additional plot elements.

# NPCs
- Guide: Helpful character

# Branches
- Path 1: First choice

# Technical Requirements
Length: 6
"""
        
        story = parse_story_file(content)
        
        assert isinstance(story, StoryRequirements)
        assert "multiple lines" in story.plot
        assert "second line" in story.plot
        assert "third line" in story.plot
    
    def test_parse_story_file_with_complex_npcs(self):
        """Test parsing story file with complex NPC descriptions."""
        content = """
# Setting
Location: Test

# Main Character
Name: Hero

# Plot
Simple plot.

# NPCs
- Wizard: A powerful spellcaster with a long white beard and mysterious past
- Guard Captain: Stern military leader, role: authority figure
- Merchant Bob: Friendly trader who sells potions, role: helper, background: former adventurer
- The Shadow: Mysterious antagonist, description: cloaked figure, role: villain

# Branches
- Choice: Test choice

# Technical Requirements
Length: 5
"""
        
        story = parse_story_file(content)
        
        assert len(story.npcs) == 4
        
        wizard = next(npc for npc in story.npcs if npc["name"] == "Wizard")
        assert "powerful spellcaster" in wizard["description"]
        
        guard = next(npc for npc in story.npcs if npc["name"] == "Guard Captain")
        assert "Stern military leader" in guard["description"]
        assert guard.get("role") == "authority figure"
        
        merchant = next(npc for npc in story.npcs if npc["name"] == "Merchant Bob")
        assert merchant.get("role") == "helper"
        assert merchant.get("background") == "former adventurer"
    
    def test_parse_story_file_with_complex_branches(self):
        """Test parsing story file with complex branch descriptions."""
        content = """
# Setting
Location: Test

# Main Character
Name: Hero

# Plot
Test plot.

# NPCs
- Helper: Test helper

# Branches
- Combat Approach: Use force to solve problems, type: aggressive, difficulty: hard
- Diplomatic Route: Try to negotiate and find peaceful solutions
- Stealth Path: Avoid detection and sneak past obstacles, type: sneaky
- Magic Solution: Use magical abilities, requirements: magic skill

# Technical Requirements
Length: 8
"""
        
        story = parse_story_file(content)
        
        assert len(story.branches) == 4
        
        combat = next(branch for branch in story.branches if branch["type"] == "Combat Approach")
        assert "Use force" in combat["description"]
        assert combat.get("difficulty") == "hard"
        
        stealth = next(branch for branch in story.branches if branch["type"] == "Stealth Path")
        assert stealth.get("type") == "sneaky"
    
    def test_parse_story_file_missing_sections(self):
        """Test parsing story file with missing sections."""
        content = """
# Setting
Location: Test City

# Plot
Simple plot without all sections.

# Technical Requirements
Length: 5
"""
        
        story = parse_story_file(content)
        
        assert isinstance(story, StoryRequirements)
        assert story.setting["location"] == "Test City"
        assert story.plot == "Simple plot without all sections."
        assert len(story.main_character) == 0  # Missing section
        assert len(story.npcs) == 0  # Missing section
        assert len(story.branches) == 0  # Missing section
        assert story.technical_requirements["length"] == "5"
    
    def test_parse_story_file_empty_sections(self):
        """Test parsing story file with empty sections."""
        content = """
# Setting
Location: Test City

# Main Character

# Plot
Test plot.

# NPCs

# Branches

# Technical Requirements
Length: 5
"""
        
        story = parse_story_file(content)
        
        assert isinstance(story, StoryRequirements)
        assert story.setting["location"] == "Test City"
        assert len(story.main_character) == 0  # Empty section
        assert story.plot == "Test plot."
        assert len(story.npcs) == 0  # Empty section
        assert len(story.branches) == 0  # Empty section
    
    def test_parse_story_file_with_special_characters(self):
        """Test parsing story file with special characters."""
        content = """
# Setting
Location: Café del Mañana
Time Period: 21st-century

# Main Character
Name: José María
Background: Ex-soldier with PTSD

# Plot
A story about redemption & hope—featuring José's journey through his past demons.

# NPCs
- Dr. Smith: Therapist with "unconventional" methods
- María: José's ex-wife (50/50 custody)

# Branches
- Therapy Route: Professional help → healing
- Self-medication: Alcohol/drugs path

# Technical Requirements
Length: 10-15 steps
"""
        
        story = parse_story_file(content)
        
        assert story.setting["location"] == "Café del Mañana"
        assert story.main_character["name"] == "José María"
        assert "redemption & hope—featuring" in story.plot
        
        therapist = next(npc for npc in story.npcs if npc["name"] == "Dr. Smith")
        assert '"unconventional"' in therapist["description"]
    
    def test_parse_story_file_case_insensitive_headers(self):
        """Test parsing story file with mixed case headers."""
        content = """
# setting
Location: Test

# MAIN CHARACTER
Name: Hero

# plot
Simple story.

# npcs
- Helper: Test

# BRANCHES
- Choice: Test

# technical requirements
Length: 5
"""
        
        story = parse_story_file(content)
        
        assert isinstance(story, StoryRequirements)
        assert story.setting["location"] == "Test"
        assert story.main_character["name"] == "Hero"
        assert story.plot == "Simple story."
    
    def test_parse_story_file_with_numeric_values(self):
        """Test parsing story file with numeric technical requirements."""
        content = """
# Setting
Location: Test

# Main Character
Name: Hero

# Plot
Test plot.

# NPCs
- Helper: Test

# Branches
- Choice: Test

# Technical Requirements
Length: 12
Branches: 4
Endings: 3
Complexity: 7
Playtime: 20
"""
        
        story = parse_story_file(content)
        
        assert story.technical_requirements["length"] == "12"
        assert story.technical_requirements["branches"] == "4"
        assert story.technical_requirements["endings"] == "3"
        assert story.technical_requirements["complexity"] == "7"
        assert story.technical_requirements["playtime"] == "20"
    
    def test_parse_empty_story_file(self):
        """Test parsing an empty story file."""
        content = ""
        
        story = parse_story_file(content)
        
        assert isinstance(story, StoryRequirements)
        assert len(story.setting) == 0
        assert len(story.main_character) == 0
        assert story.plot == ""
        assert len(story.npcs) == 0
        assert len(story.branches) == 0
        assert len(story.technical_requirements) == 0