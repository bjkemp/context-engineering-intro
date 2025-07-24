"""
Adventure Generation Agent - AI-powered .adv file creator.

This package provides a Pydantic AI agent system that generates complete,
balanced .adv adventure files from author style templates and story content files.
"""

from .models import (
    AdventureGame,
    AuthorPersona,
    Choice,
    ChoiceLabel,
    EndingType,
    FlowNode,
    GenerationProgress,
    ReplayabilityMetrics,
    StoryRequirements,
    StoryStep,
    ToolResult,
    ValidationResult,
)

__version__ = "0.1.0"
__all__ = [
    "AdventureGame",
    "AuthorPersona", 
    "Choice",
    "ChoiceLabel",
    "EndingType",
    "FlowNode",
    "GenerationProgress",
    "ReplayabilityMetrics",
    "StoryRequirements",
    "StoryStep",
    "ToolResult",
    "ValidationResult",
]
