"""MCP Server for Adventure Storyteller Tools.

This server provides specialized tools for adventure generation that can be
used by Gemini CLI to enhance story creation, validation, and analysis.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    EmbeddedResource,
    ImageContent,
)

from .tools import (
    adventure_format_validator,
    character_consistency_tracker,
    plot_branch_generator,
    choice_quality_analyzer,
    ending_balance_checker,
    story_flow_visualizer,
    author_style_matcher,
    technical_requirements_parser,
)


class AdventureStorytellerServer:
    """Adventure Storyteller MCP Server."""
    
    def __init__(self):
        self.server = Server("adventure-storyteller")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up MCP handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available storyteller tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="validate_adventure_format",
                        description="Validate .adv file format and structure for game engine compatibility",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "adventure_content": {
                                    "type": "string",
                                    "description": "Content of the .adv file to validate"
                                },
                                "strict_mode": {
                                    "type": "boolean",
                                    "description": "Enable strict validation mode",
                                    "default": True
                                }
                            },
                            "required": ["adventure_content"]
                        }
                    ),
                    Tool(
                        name="track_character_consistency",
                        description="Analyze character consistency across story branches",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "adventure_content": {
                                    "type": "string",
                                    "description": "Content of the .adv file to analyze"
                                },
                                "character_profiles": {
                                    "type": "object",
                                    "description": "Character profiles to track",
                                    "additionalProperties": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "personality": {"type": "array", "items": {"type": "string"}},
                                            "dialogue_style": {"type": "string"}
                                        }
                                    }
                                }
                            },
                            "required": ["adventure_content"]
                        }
                    ),
                    Tool(
                        name="generate_plot_branches",
                        description="Generate meaningful story branching points",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "current_narrative": {
                                    "type": "string",
                                    "description": "Current story narrative"
                                },
                                "branch_count": {
                                    "type": "integer",
                                    "description": "Number of branches to generate",
                                    "minimum": 2,
                                    "maximum": 4,
                                    "default": 3
                                },
                                "theme": {
                                    "type": "string",
                                    "description": "Story theme or genre"
                                }
                            },
                            "required": ["current_narrative"]
                        }
                    ),
                    Tool(
                        name="analyze_choice_quality",
                        description="Analyze player choice quality and meaningfulness",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "adventure_content": {
                                    "type": "string",
                                    "description": "Content of the .adv file to analyze"
                                },
                                "min_impact_threshold": {
                                    "type": "number",
                                    "description": "Minimum impact score for meaningful choices",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                    "default": 0.3
                                }
                            },
                            "required": ["adventure_content"]
                        }
                    ),
                    Tool(
                        name="check_ending_balance",
                        description="Verify good distribution of success/failure/neutral endings",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "adventure_content": {
                                    "type": "string",
                                    "description": "Content of the .adv file to analyze"
                                },
                                "target_ratios": {
                                    "type": "object",
                                    "description": "Target distribution ratios",
                                    "properties": {
                                        "success": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                        "failure": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                        "neutral": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                                    }
                                }
                            },
                            "required": ["adventure_content"]
                        }
                    ),
                    Tool(
                        name="visualize_story_flow",
                        description="Generate ASCII map of adventure structure",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "adventure_content": {
                                    "type": "string",
                                    "description": "Content of the .adv file to visualize"
                                },
                                "format": {
                                    "type": "string",
                                    "description": "Output format",
                                    "enum": ["ascii", "mermaid", "dot"],
                                    "default": "ascii"
                                }
                            },
                            "required": ["adventure_content"]
                        }
                    ),
                    Tool(
                        name="match_author_style",
                        description="Apply specific author voice/tone to content",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "Content to style"
                                },
                                "author_profile": {
                                    "type": "string",
                                    "description": "Author profile content (.author file)"
                                },
                                "target_section": {
                                    "type": "string",
                                    "description": "Type of content being styled",
                                    "enum": ["narrative", "dialogue", "description", "choice"],
                                    "default": "narrative"
                                }
                            },
                            "required": ["content", "author_profile"]
                        }
                    ),
                    Tool(
                        name="parse_technical_requirements",
                        description="Extract length, complexity, and branch requirements",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "requirements_text": {
                                    "type": "string",
                                    "description": "Technical requirements specification"
                                },
                                "story_content": {
                                    "type": "string",
                                    "description": "Story content to analyze"
                                }
                            },
                            "required": ["requirements_text"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute a storyteller tool."""
            try:
                if name == "validate_adventure_format":
                    result = await adventure_format_validator.validate_adventure_format(
                        arguments["adventure_content"],
                        arguments.get("strict_mode", True)
                    )
                
                elif name == "track_character_consistency":
                    result = await character_consistency_tracker.track_character_consistency(
                        arguments["adventure_content"],
                        arguments.get("character_profiles", {})
                    )
                
                elif name == "generate_plot_branches":
                    result = await plot_branch_generator.generate_plot_branches(
                        arguments["current_narrative"],
                        arguments.get("branch_count", 3),
                        arguments.get("theme", "adventure")
                    )
                
                elif name == "analyze_choice_quality":
                    result = await choice_quality_analyzer.analyze_choice_quality(
                        arguments["adventure_content"],
                        arguments.get("min_impact_threshold", 0.3)
                    )
                
                elif name == "check_ending_balance":
                    result = await ending_balance_checker.check_ending_balance(
                        arguments["adventure_content"],
                        arguments.get("target_ratios", {})
                    )
                
                elif name == "visualize_story_flow":
                    result = await story_flow_visualizer.visualize_story_flow(
                        arguments["adventure_content"],
                        arguments.get("format", "ascii")
                    )
                
                elif name == "match_author_style":
                    result = await author_style_matcher.match_author_style(
                        arguments["content"],
                        arguments["author_profile"],
                        arguments.get("target_section", "narrative")
                    )
                
                elif name == "parse_technical_requirements":
                    result = await technical_requirements_parser.parse_technical_requirements(
                        arguments["requirements_text"],
                        arguments.get("story_content", "")
                    )
                
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                        isError=True
                    )
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))],
                    isError=False
                )
                
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error executing {name}: {str(e)}")],
                    isError=True
                )
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as streams:
            await self.server.run(
                streams[0], 
                streams[1], 
                InitializationOptions(
                    server_name="adventure-storyteller",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities()
                )
            )


async def main():
    """Main entry point for the MCP server."""
    server = AdventureStorytellerServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())