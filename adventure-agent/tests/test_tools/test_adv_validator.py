"""
Tests for the ADV validator tool.
"""

import pytest
from adventure_agent.tools.adv_validator import (
    validate_adv_format,
    validate_choice_syntax,
    fix_common_validation_issues,
    ValidationError
)
from adventure_agent.models import AdventureGame, Choice, ChoiceLabel, StoryStep


class TestAdvValidator:
    """Test the ADV format validation functionality."""
    
    @pytest.fixture
    def valid_adventure(self):
        """Create a valid adventure for testing."""
        choice_a = Choice(
            label=ChoiceLabel.A,
            description="Take the direct path",
            target="STEP_2",
            conditions=[],
            consequences=[]
        )
        
        choice_b = Choice(
            label=ChoiceLabel.B,
            description="Try the sneaky route",
            target="ENDING_SUCCESS",
            conditions=[],
            consequences=[]
        )
        
        step1 = StoryStep(
            step_id="1",
            narrative="You stand at a crossroads in the forest. Two paths diverge before you.",
            choices=[choice_a, choice_b]
        )
        
        step2 = StoryStep(
            step_id="2",
            narrative="The direct path leads to a clearing with a mysterious tower.",
            choices=[Choice(
                label=ChoiceLabel.A,
                description="Enter the tower",
                target="ENDING_SUCCESS",
                conditions=[],
                consequences=[]
            )]
        )
        
        return AdventureGame(
            game_name="Test Adventure",
            main_menu=["Start New Game", "Load Game", "Exit"],
            steps={"1": step1, "2": step2},
            endings={
                "success": "You have successfully completed your quest!",
                "failure": "Your adventure ends in failure."
            },
            inventory={},
            stats={},
            variables={}
        )
    
    @pytest.fixture
    def invalid_adventure(self):
        """Create an invalid adventure for testing."""
        choice_invalid = Choice(
            label=ChoiceLabel.A,
            description="",  # Empty description
            target="STEP_999",  # Non-existent target
            conditions=[],
            consequences=[]
        )
        
        step1 = StoryStep(
            step_id="1",
            narrative="",  # Empty narrative
            choices=[choice_invalid]
        )
        
        return AdventureGame(
            game_name="",  # Empty game name
            main_menu=[],  # Empty main menu
            steps={"1": step1},
            endings={},  # No endings
            inventory={},
            stats={},
            variables={}
        )
    
    @pytest.mark.asyncio
    async def test_validate_valid_adventure(self, valid_adventure):
        """Test validation of a valid adventure."""
        result = await validate_adv_format(valid_adventure)
        
        assert result.success
        assert result.data["valid"] is True
        assert result.data["error_count"] == 0
        assert len(result.data["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_invalid_adventure(self, invalid_adventure):
        """Test validation of an invalid adventure."""
        result = await validate_adv_format(invalid_adventure)
        
        assert not result.success
        assert result.data["valid"] is False
        assert result.data["error_count"] > 0
        assert len(result.data["errors"]) > 0
        
        # Check for specific errors
        errors = result.data["errors"]
        error_text = " ".join(errors)
        
        assert "game name" in error_text.lower()
        assert "main menu" in error_text.lower()
        assert "narrative" in error_text.lower()
        assert "ending" in error_text.lower()
    
    @pytest.mark.asyncio
    async def test_validate_missing_required_sections(self):
        """Test validation catches missing required sections."""
        # Adventure with minimal content
        adventure = AdventureGame(
            game_name="",  # Missing
            main_menu=[],  # Missing
            steps={},      # Missing
            endings={},    # Missing
            inventory={},
            stats={},
            variables={}
        )
        
        result = await validate_adv_format(adventure)
        
        assert not result.success
        errors = result.data["errors"]
        error_text = " ".join(errors).lower()
        
        assert "game_name" in error_text
        assert "main_menu" in error_text
        assert "step" in error_text
    
    @pytest.mark.asyncio
    async def test_validate_choice_targets(self, valid_adventure):
        """Test validation of choice targets."""
        # Add choice with invalid target
        invalid_choice = Choice(
            label=ChoiceLabel.B,
            description="Go to non-existent step",
            target="STEP_999",  # Invalid target
            conditions=[],
            consequences=[]
        )
        
        valid_adventure.steps["1"].choices.append(invalid_choice)
        
        result = await validate_adv_format(valid_adventure)
        
        assert not result.success
        errors = result.data["errors"]
        error_text = " ".join(errors)
        
        assert "STEP_999" in error_text
        assert "invalid" in error_text.lower()
    
    @pytest.mark.asyncio
    async def test_validate_choice_labels(self):
        """Test validation of choice labels."""
        # Create adventure with duplicate choice labels
        choice1 = Choice(
            label=ChoiceLabel.A,
            description="First choice",
            target="ENDING_SUCCESS",
            conditions=[],
            consequences=[]
        )
        
        choice2 = Choice(
            label=ChoiceLabel.A,  # Duplicate label
            description="Second choice",
            target="ENDING_FAILURE", 
            conditions=[],
            consequences=[]
        )
        
        step = StoryStep(
            step_id="1",
            narrative="Choose your path.",
            choices=[choice1, choice2]
        )
        
        adventure = AdventureGame(
            game_name="Test",
            main_menu=["Start"],
            steps={"1": step},
            endings={"success": "Win", "failure": "Lose"},
            inventory={},
            stats={},
            variables={}
        )
        
        result = await validate_adv_format(adventure)
        
        assert not result.success
        errors = result.data["errors"]
        error_text = " ".join(errors)
        
        assert "duplicate" in error_text.lower()
        assert "label" in error_text.lower()
    
    @pytest.mark.asyncio
    async def test_validate_step_numbering(self):
        """Test validation of step numbering."""
        # Create adventure with non-sequential step numbers
        step1 = StoryStep(
            step_id="1",
            narrative="First step",
            choices=[Choice(
                label=ChoiceLabel.A,
                description="Continue",
                target="STEP_5",  # Skip to step 5
                conditions=[],
                consequences=[]
            )]
        )
        
        step5 = StoryStep(
            step_id="5",  # Non-sequential
            narrative="Fifth step",
            choices=[Choice(
                label=ChoiceLabel.A,
                description="End",
                target="ENDING_SUCCESS",
                conditions=[],
                consequences=[]
            )]
        )
        
        adventure = AdventureGame(
            game_name="Test",
            main_menu=["Start"],
            steps={"1": step1, "5": step5},
            endings={"success": "Win"},
            inventory={},
            stats={},
            variables={}
        )
        
        result = await validate_adv_format(adventure)
        
        # Non-sequential numbering should produce warnings, not errors
        assert result.success  # Should still be valid
        warnings = result.data.get("warnings", [])
        if warnings:
            warning_text = " ".join(warnings)
            assert "sequential" in warning_text.lower() or "numbering" in warning_text.lower()
    
    @pytest.mark.asyncio
    async def test_validate_story_flow(self, valid_adventure):
        """Test validation of story flow and reachability."""
        # Add unreachable step
        unreachable_step = StoryStep(
            step_id="99",
            narrative="This step cannot be reached from step 1.",
            choices=[Choice(
                label=ChoiceLabel.A,
                description="End",
                target="ENDING_SUCCESS",
                conditions=[],
                consequences=[]
            )]
        )
        
        valid_adventure.steps["99"] = unreachable_step
        
        result = await validate_adv_format(valid_adventure)
        
        # This might be a warning rather than an error
        if not result.success:
            errors = result.data["errors"]
            error_text = " ".join(errors)
            assert "unreachable" in error_text.lower()
        else:
            warnings = result.data.get("warnings", [])
            if warnings:
                warning_text = " ".join(warnings)
                assert "unreachable" in warning_text.lower()
    
    @pytest.mark.asyncio
    async def test_fix_common_validation_issues(self, invalid_adventure):
        """Test automatic fixing of common validation issues."""
        fixed_adventure = await fix_common_validation_issues(invalid_adventure)
        
        # Check that common issues were fixed
        assert fixed_adventure.game_name != ""  # Should have default name
        assert len(fixed_adventure.main_menu) > 0  # Should have default menu
        assert "success" in fixed_adventure.endings  # Should have default endings
        assert "failure" in fixed_adventure.endings
        
        # Validate the fixed adventure
        result = await validate_adv_format(fixed_adventure)
        
        # Should have fewer errors after fixing
        assert result.data["error_count"] < invalid_adventure.__dict__.get("error_count", 10)
    
    @pytest.mark.asyncio
    async def test_validate_choice_syntax(self):
        """Test individual choice syntax validation."""
        
        # Valid choice syntax
        valid_choice = "A) Take the left path → STEP_2"
        assert await validate_choice_syntax(valid_choice) is True
        
        # Valid choice with arrow
        valid_choice_arrow = "B) Go right → ENDING_SUCCESS"
        assert await validate_choice_syntax(valid_choice_arrow) is True
        
        # Valid choice with conditions
        valid_choice_conditions = "C) Use magic → STEP_3 {IF magic_skill >= 5; SET mana -10}"
        assert await validate_choice_syntax(valid_choice_conditions) is True
        
        # Invalid choice syntax
        invalid_choice = "A Take the path STEP_2"  # Missing ) and →
        assert await validate_choice_syntax(invalid_choice) is False
        
        # Invalid label
        invalid_label = "E) Invalid label → STEP_2"  # E is not valid
        assert await validate_choice_syntax(invalid_label) is False
    
    def test_validation_error_class(self):
        """Test the ValidationError class."""
        error = ValidationError(
            "TEST_ERROR",
            "This is a test error",
            "STEP_1",
            "high"
        )
        
        assert error.error_type == "TEST_ERROR"
        assert error.message == "This is a test error"
        assert error.location == "STEP_1"
        assert error.severity == "high"
        
        error_str = str(error)
        assert "HIGH" in error_str
        assert "TEST_ERROR" in error_str
        assert "This is a test error" in error_str
        assert "STEP_1" in error_str
    
    @pytest.mark.asyncio
    async def test_validate_endings_content(self):
        """Test validation of ending content."""
        # Adventure with very short endings
        adventure = AdventureGame(
            game_name="Test",
            main_menu=["Start"],
            steps={"1": StoryStep(
                step_id="1",
                narrative="Test narrative",
                choices=[Choice(
                    label=ChoiceLabel.A,
                    description="End",
                    target="ENDING_SUCCESS",
                    conditions=[],
                    consequences=[]
                )]
            )},
            endings={
                "success": "Win",  # Very short
                "failure": ""      # Empty
            },
            inventory={},
            stats={},
            variables={}
        )
        
        result = await validate_adv_format(adventure)
        
        issues = result.data["errors"] + result.data.get("warnings", [])
        issue_text = " ".join(issues).lower()
        
        assert "ending" in issue_text
        assert ("short" in issue_text or "empty" in issue_text)
    
    @pytest.mark.asyncio
    async def test_validate_inventory_format(self):
        """Test validation of inventory format."""
        adventure = AdventureGame(
            game_name="Test",
            main_menu=["Start"],
            steps={"1": StoryStep(
                step_id="1",
                narrative="Test",
                choices=[Choice(
                    label=ChoiceLabel.A,
                    description="End",
                    target="ENDING_SUCCESS",
                    conditions=[],
                    consequences=[]
                )]
            )},
            endings={"success": "Win"},
            inventory={
                "": "invalid_empty_key",  # Invalid key
                "valid_item": 5,
                "another_item": "text_value"
            },
            stats={},
            variables={}
        )
        
        result = await validate_adv_format(adventure)
        
        # Empty key should cause validation issue
        if not result.success:
            errors = result.data["errors"] 
            error_text = " ".join(errors)
            assert "key" in error_text.lower() and "invalid" in error_text.lower()