"""
Integration tests for the main Adventure Generation Agent.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from adventure_agent.agent import (
    generate_adventure,
    generate_adventure_from_files,
    _calculate_overall_quality,
    _generate_pipeline_summary
)
from adventure_agent.models import AuthorPersona, StoryRequirements, ToolResult


class TestAdventureGeneration:
    """Test the main adventure generation functionality."""
    
    @pytest.fixture
    def sample_author(self):
        """Sample author persona for testing."""
        return AuthorPersona(
            voice_and_tone=["witty", "satirical", "humorous"],
            narrative_style=["descriptive", "character-driven"],
            world_elements=["magic", "fantasy", "comedy"],
            character_development=["growth through adversity", "humor in tragedy"],
            themes=["good vs evil", "friendship", "adventure"]
        )
    
    @pytest.fixture
    def sample_story(self):
        """Sample story requirements for testing."""
        return StoryRequirements(
            setting={"location": "Ankh-Morpork", "time_period": "fantasy"},
            main_character={
                "name": "Rincewind",
                "background": "incompetent wizard",
                "motivation": "survival"
            },
            plot="A bumbling wizard must deliver an important message across the city",
            npcs=[
                {"name": "The Librarian", "role": "helper", "description": "wise orangutan"},
                {"name": "Patrician", "role": "authority", "description": "city ruler"}
            ],
            branches=[
                {"type": "choice", "description": "diplomatic vs sneaky approach"},
                {"type": "outcome", "description": "success vs failure paths"}
            ],
            technical_requirements={
                "length": 8,
                "branches": 3,
                "endings": 2,
                "complexity": "medium"
            }
        )
    
    def test_calculate_overall_quality_success(self):
        """Test quality calculation with successful tool results."""
        tool_results = {
            "storyline_generator": ToolResult(
                success=True,
                message="Generated storyline",
                metadata={"overall_score": 8.5}
            ),
            "adv_validator": ToolResult(
                success=True,
                message="Validation passed",
                metadata={"overall_score": 9.0}
            ),
            "coherence_analyzer": ToolResult(
                success=True,
                message="Coherence analyzed",
                metadata={"overall_score": 7.5}
            )
        }
        
        quality = _calculate_overall_quality(tool_results)
        assert quality > 7.0
        assert quality <= 10.0
    
    def test_calculate_overall_quality_mixed(self):
        """Test quality calculation with mixed results."""
        tool_results = {
            "storyline_generator": ToolResult(
                success=True,
                message="Generated storyline",
                metadata={"overall_score": 8.0}
            ),
            "adv_validator": ToolResult(
                success=False,
                message="Validation failed"
            ),
            "coherence_analyzer": ToolResult(
                success=True,
                message="Coherence analyzed",
                metadata={"overall_score": 6.0}
            )
        }
        
        quality = _calculate_overall_quality(tool_results)
        assert quality < 8.0
        assert quality > 3.0
    
    def test_generate_pipeline_summary(self):
        """Test pipeline summary generation."""
        from adventure_agent.agent import AdventureGenerationDependencies
        
        # Create mock dependencies
        deps = AdventureGenerationDependencies(
            author=AuthorPersona(
                voice_and_tone=["test"],
                narrative_style=["test"],
                world_elements=["test"],
                character_development=["test"],
                themes=["test"]
            ),
            story=StoryRequirements(
                setting={},
                main_character={},
                plot="test plot",
                npcs=[],
                branches=[],
                technical_requirements={}
            )
        )
        
        deps.generation_stages = ["stage1", "stage2", "stage3"]
        deps.tool_results = {
            "tool1": ToolResult(success=True, message="success"),
            "tool2": ToolResult(success=False, message="failed"),
            "tool3": ToolResult(success=True, message="success")
        }
        
        summary = _generate_pipeline_summary(deps)
        
        assert summary["stages_completed"] == 3
        assert summary["stages"] == ["stage1", "stage2", "stage3"]
        assert summary["tools_used"] == ["tool1", "tool2", "tool3"]
        assert summary["success_rate"] == 2/3  # 2 out of 3 succeeded
        assert "tool_summaries" in summary
    
    @pytest.mark.asyncio
    async def test_generate_adventure_basic(self, sample_author, sample_story):
        """Test basic adventure generation."""
        
        # Mock all the tool functions to avoid actual generation
        with patch('adventure_agent.agent.generate_storyline') as mock_storyline, \
             patch('adventure_agent.agent.track_characters') as mock_characters, \
             patch('adventure_agent.agent.integrate_inventory') as mock_inventory, \
             patch('adventure_agent.agent.validate_adv_format') as mock_validate, \
             patch('adventure_agent.agent.prune_branches') as mock_branches, \
             patch('adventure_agent.agent.analyze_coherence') as mock_coherence, \
             patch('adventure_agent.agent.optimize_endings') as mock_endings, \
             patch('adventure_agent.agent.analyze_choices') as mock_choices, \
             patch('adventure_agent.agent.score_replayability') as mock_replay, \
             patch('adventure_agent.agent.generate_flow_visualization') as mock_flow:
            
            # Set up mock returns
            mock_adventure = {
                "game_name": "Test Adventure",
                "steps": {"1": {"narrative": "Test narrative", "choices": []}},
                "endings": {"success": "You win!"},
                "inventory": {},
                "stats": {},
                "variables": {}
            }
            
            mock_storyline.return_value = ToolResult(
                success=True,
                data=mock_adventure,
                message="Storyline generated"
            )
            
            mock_characters.return_value = ToolResult(
                success=True,
                data={"profiles": {}},
                message="Characters tracked"
            )
            
            mock_inventory.return_value = ToolResult(
                success=True,
                data=mock_adventure,
                message="Inventory integrated"
            )
            
            mock_validate.return_value = ToolResult(
                success=True,
                data={"valid": True},
                message="Validation passed"
            )
            
            mock_branches.return_value = ToolResult(
                success=True,
                data={"optimized_adventure": mock_adventure},
                message="Branches optimized"
            )
            
            mock_coherence.return_value = ToolResult(
                success=True,
                data={"analysis": {"overall_coherence_score": 8.0}},
                message="Coherence analyzed"
            )
            
            mock_endings.return_value = ToolResult(
                success=True,
                data={"optimized_adventure": mock_adventure},
                message="Endings optimized"
            )
            
            mock_choices.return_value = ToolResult(
                success=True,
                data={"analysis": {"overall_choice_score": 7.5}},
                message="Choices analyzed"
            )
            
            mock_replay.return_value = ToolResult(
                success=True,
                data={"analysis": {"overall_replayability": 7.0}},
                message="Replayability scored"
            )
            
            mock_flow.return_value = ToolResult(
                success=True,
                data={"visualization": {}},
                message="Flow visualized"
            )
            
            # Run the generation
            result = await generate_adventure(
                sample_author,
                sample_story,
                enable_streaming=False,
                quality_threshold=6.0
            )
            
            # Verify result
            assert result.success
            assert "final_adventure" in result.data
            assert "generation_stages" in result.data
            assert "tool_results" in result.data
            assert result.metadata["overall_quality"] >= 6.0
    
    @pytest.mark.asyncio
    async def test_generate_adventure_quality_threshold_not_met(self, sample_author, sample_story):
        """Test adventure generation when quality threshold is not met."""
        
        with patch('adventure_agent.agent.generate_storyline') as mock_storyline:
            # Set up low-quality result
            mock_storyline.return_value = ToolResult(
                success=False,
                message="Generation failed"
            )
            
            # This should raise an exception due to failed storyline generation
            with pytest.raises(Exception, match="Storyline generation failed"):
                await generate_adventure(
                    sample_author,
                    sample_story,
                    enable_streaming=False,
                    quality_threshold=8.0
                )
    
    @pytest.mark.asyncio 
    async def test_generate_adventure_from_files_success(self, tmp_path):
        """Test adventure generation from files."""
        
        # Create temporary test files
        author_file = tmp_path / "test.author"
        story_file = tmp_path / "test.story"
        output_file = tmp_path / "output.adv"
        
        author_content = """
# Voice and Tone
- Witty and satirical
- Humorous undertones

# Narrative Style  
- Descriptive prose
- Character-driven

# World Elements
- Fantasy setting
- Magical elements

# Character Development
- Growth through adversity

# Themes
- Good vs evil
"""
        
        story_content = """
# Setting
Location: Test City
Time Period: Fantasy

# Main Character
Name: Hero
Background: Adventurer

# Plot
A simple test adventure for validation.

# NPCs
- Shopkeeper: Helpful merchant
- Guard: City protector

# Branches
- Choice 1: Go left or right
- Choice 2: Fight or flee

# Technical Requirements
Length: 5 story steps
Branches: 2 major branching points
Endings: 2 (success, failure)
"""
        
        author_file.write_text(author_content)
        story_file.write_text(story_content)
        
        # Mock the actual generation
        with patch('adventure_agent.agent.generate_adventure') as mock_generate:
            mock_adventure = {
                "game_name": "Test Adventure",
                "steps": {"1": {"narrative": "Test", "choices": []}},
                "endings": {"success": "Win"},
                "inventory": {},
                "stats": {},
                "variables": {}
            }
            
            mock_generate.return_value = ToolResult(
                success=True,
                data={
                    "final_adventure": mock_adventure,
                    "generation_stages": ["test"],
                    "tool_results": {},
                    "pipeline_summary": {}
                },
                message="Adventure generated",
                metadata={"overall_quality": 8.0}
            )
            
            # Mock the ADV file generation
            with patch('adventure_agent.agent.generate_adv_file') as mock_adv:
                mock_adv.return_value = "[GAME_NAME]\nTest Adventure\n[/GAME_NAME]"
                
                result = await generate_adventure_from_files(
                    str(author_file),
                    str(story_file),
                    str(output_file),
                    enable_streaming=False
                )
                
                assert result.success
                assert output_file.exists()
                assert result.metadata["output_file"] == str(output_file)
    
    @pytest.mark.asyncio
    async def test_generate_adventure_from_files_missing_file(self):
        """Test adventure generation with missing input file."""
        
        result = await generate_adventure_from_files(
            "nonexistent_author.author",
            "nonexistent_story.story",
            enable_streaming=False
        )
        
        assert not result.success
        assert "failed" in result.message.lower()
    
    def test_adventure_generation_dependencies_initialization(self, sample_author, sample_story):
        """Test the dependencies class initialization."""
        from adventure_agent.agent import AdventureGenerationDependencies
        
        deps = AdventureGenerationDependencies(sample_author, sample_story)
        
        assert deps.author == sample_author
        assert deps.story == sample_story
        assert deps.generation_stages == []
        assert deps.current_adventure is None
        assert deps.tool_results == {}
        assert deps.streaming_enabled is True
        assert deps.quality_threshold == 7.0


class TestAdventureAgent:
    """Test the adventure agent creation and configuration."""
    
    def test_create_adventure_agent(self):
        """Test adventure agent creation."""
        from adventure_agent.agent import create_adventure_agent
        
        agent = create_adventure_agent()
        assert agent is not None
        # Additional agent-specific tests would go here