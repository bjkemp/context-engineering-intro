"""
Core Pydantic models for the Adventure Generation Agent.

This module defines the data structures used throughout the adventure generation
system, ensuring type safety and validation.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuthorPersona(BaseModel):
    """
    Represents an author's persona and writing style.
    
    This model captures the key characteristics that define how an author
    writes, including their voice, narrative style, and thematic elements.
    """
    
    voice_and_tone: list[str] = Field(
        ..., 
        min_length=1,
        description="List of voice and tone characteristics (e.g., 'witty', 'dramatic')"
    )
    narrative_style: list[str] = Field(
        ..., 
        min_length=1,
        description="List of narrative style elements (e.g., 'first-person', 'descriptive')"
    )
    world_elements: list[str] = Field(
        ..., 
        min_length=1,
        description="List of world-building elements (e.g., 'fantasy', 'steampunk')"
    )
    character_development: list[str] = Field(
        ..., 
        min_length=1,
        description="List of character development approaches"
    )
    themes: list[str] = Field(
        ..., 
        min_length=1,
        description="List of thematic elements the author explores"
    )


class StoryRequirements(BaseModel):
    """
    Defines the requirements and constraints for a story to be generated.
    
    This model captures all the necessary information to generate a coherent
    adventure story that meets specific requirements.
    """
    
    setting: dict[str, str] = Field(
        ...,
        description="Setting details including time, place, environment"
    )
    main_character: dict[str, str] = Field(
        ...,
        description="Main character details including background, motivation"
    )
    plot: str = Field(
        ...,
        min_length=10,
        description="Core plot description"
    )
    npcs: list[dict[str, str]] = Field(
        default_factory=list,
        description="Non-player characters with their details"
    )
    branches: list[dict[str, str]] = Field(
        default_factory=list,
        description="Story branching points and their consequences"
    )
    technical_requirements: dict[str, str | int | list[str]] = Field(
        default_factory=dict,
        description="Technical constraints like length, number of endings"
    )


class ChoiceLabel(str, Enum):
    """Valid choice labels for adventure game choices."""
    A = "A"
    B = "B" 
    C = "C"
    D = "D"


class Choice(BaseModel):
    """
    Represents a single choice in an adventure game step.
    
    Each choice has a label, description, target destination, and optional
    conditions/consequences that affect gameplay.
    """
    
    label: ChoiceLabel = Field(
        ...,
        description="Choice label (A, B, C, or D)"
    )
    description: str = Field(
        ...,
        min_length=5,
        description="User-facing description of the choice"
    )
    target: str = Field(
        ...,
        pattern=r"^(STEP_\d+|ENDING_(SUCCESS|FAILURE|NEUTRAL))$",
        description="Target step or ending (e.g., 'STEP_5', 'ENDING_SUCCESS')"
    )
    conditions: list[str] = Field(
        default_factory=list,
        description="Conditions that must be met for this choice to be available"
    )
    consequences: list[str] = Field(
        default_factory=list,
        description="Effects of choosing this option"
    )


class StoryStep(BaseModel):
    """
    Represents a single step in an adventure story.
    
    Each step contains narrative text and a list of choices that determine
    where the story goes next.
    """
    
    step_id: str = Field(
        ...,
        pattern=r"^\d+$",
        description="Numeric step identifier (e.g., '1', '2')"
    )
    narrative: str = Field(
        ...,
        min_length=50,
        description="The narrative text for this step"
    )
    choices: list[Choice] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Available choices for the player"
    )


class EndingType(str, Enum):
    """Types of story endings."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"


class AdventureGame(BaseModel):
    """
    Complete adventure game data structure.
    
    This model represents a fully generated adventure game that can be
    exported to .adv format and played in the JavaScript game engine.
    """
    
    game_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Name of the adventure game"
    )
    ask_for_name: bool = Field(
        default=False,
        description="Whether to ask for player's name at start"
    )
    main_menu: list[str] = Field(
        default=["Start New Game", "Load Game", "Exit"],
        min_length=1,
        description="Main menu items"
    )
    steps: dict[str, StoryStep] = Field(
        ...,
        min_length=1,
        description="Story steps indexed by step ID"
    )
    endings: dict[EndingType, str] = Field(
        default_factory=dict,
        description="Story endings by type"
    )
    inventory: dict[str, str | int] = Field(
        default_factory=dict,
        description="Initial inventory items and values"
    )
    stats: dict[str, str | int] = Field(
        default_factory=dict,
        description="Character stats and values"
    )
    variables: dict[str, str | int] = Field(
        default_factory=dict,
        description="Game variables and flags"
    )


class ValidationResult(BaseModel):
    """
    Result of validating an adventure game.
    
    Contains validation status and any errors found during validation.
    """
    
    valid: bool = Field(
        ...,
        description="Whether the adventure game is valid"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of validation warnings"
    )


class GenerationProgress(BaseModel):
    """
    Tracks progress during adventure generation.
    
    Used for streaming progress updates to the CLI.
    """
    
    current_step: str = Field(
        ...,
        description="Current generation step being executed"
    )
    total_steps: int = Field(
        ...,
        ge=1,
        description="Total number of steps in generation process"
    )
    completed_steps: int = Field(
        ...,
        ge=0,
        description="Number of completed steps"
    )
    message: str = Field(
        default="",
        description="Status message for current step"
    )
    
    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100.0


class ToolResult(BaseModel):
    """
    Generic result from agent tool execution.
    
    Standardizes the response format from all agent tools.
    """
    
    success: bool = Field(
        ...,
        description="Whether the tool execution was successful"
    )
    data: Any = Field(
        default=None,
        description="Tool execution result data"
    )
    message: str = Field(
        default="",
        description="Human-readable status message"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the execution"
    )


class FlowNode(BaseModel):
    """
    Represents a node in the story flow visualization.
    
    Used by the flow visualizer tool to create story maps.
    """
    
    node_id: str = Field(
        ...,
        description="Unique identifier for this node"
    )
    node_type: str = Field(
        ...,
        description="Type of node (step, ending, choice)"
    )
    label: str = Field(
        ...,
        description="Display label for the node"
    )
    connections: list[str] = Field(
        default_factory=list,
        description="List of connected node IDs"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional node metadata"
    )


class ReplayabilityMetrics(BaseModel):
    """
    Metrics for analyzing story replayability.
    
    Used by the replayability scorer tool.
    """
    
    total_paths: int = Field(
        ...,
        ge=1,
        description="Total number of unique story paths"
    )
    unique_outcomes: int = Field(
        ...,
        ge=1,
        description="Number of unique endings"
    )
    branch_complexity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Complexity score of branching (0-1)"
    )
    content_variation: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Variation in content across paths (0-1)"
    )
    replayability_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Overall replayability score (0-10)"
    )