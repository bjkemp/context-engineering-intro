"""
Command Line Interface for the Adventure Generation Agent.

Modern Typer-based CLI with streaming output, batch processing, and validation modes.
"""

import asyncio
import os
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .agent import (
    generate_adventure_from_files,
    generate_adventure_batch,
    quick_validate_adventure,
    generate_quality_report,
)
from .parsers.author_parser import parse_author_content
from .parsers.story_parser import parse_story_content
from .tools.flow_visualizer import export_to_format
from .tools.branch_pruner import generate_branch_report
from .tools.ending_optimizer import generate_ending_report


app = typer.Typer(
    name="adventure-agent",
    help="AI-powered .adv file generator with 10 specialized tools for creating balanced adventures.",
    add_completion=False,
)

console = Console()


@app.command()
def generate(
    author: str = typer.Argument(..., help="Path to .author file"),
    story: str = typer.Argument(..., help="Path to .story file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .adv file path"),
    quality_threshold: float = typer.Option(7.0, "--quality", "-q", help="Minimum quality threshold (0-10)"),
    no_streaming: bool = typer.Option(False, "--no-streaming", help="Disable streaming output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Generate a single adventure from author and story files."""
    
    # Validate input files
    if not os.path.exists(author):
        console.print(f"❌ Author file not found: {author}", style="red")
        raise typer.Exit(1)
    
    if not os.path.exists(story):
        console.print(f"❌ Story file not found: {story}", style="red")
        raise typer.Exit(1)
    
    # Set default output path
    if not output:
        author_name = Path(author).stem
        story_name = Path(story).stem
        output = f"{author_name}_{story_name}.adv"
    
    console.print(Panel.fit(
        f"🎮 Adventure Generation\n"
        f"📖 Author: {author}\n"
        f"📚 Story: {story}\n"
        f"🎯 Output: {output}\n"
        f"⚡ Quality Threshold: {quality_threshold}/10",
        title="Configuration"
    ))
    
    # Run generation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating adventure...", total=None)
        
        try:
            result = asyncio.run(generate_adventure_from_files(
                author,
                story,
                output,
                enable_streaming=not no_streaming,
                quality_threshold=quality_threshold
            ))
            
            progress.update(task, completed=True)
            
            if result.success:
                console.print(f"✅ {result.message}", style="green")
                console.print(f"📁 Adventure saved to: {output}")
                
                if verbose and result.data:
                    _display_generation_summary(result.data)
                    
            else:
                console.print(f"❌ {result.message}", style="red")
                raise typer.Exit(1)
                
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"❌ Generation failed: {str(e)}", style="red")
            raise typer.Exit(1)


@app.command()
def batch(
    author_dir: str = typer.Argument(..., help="Directory containing .author files"),
    story_dir: str = typer.Argument(..., help="Directory containing .story files"),
    output_dir: str = typer.Option("output", "--output-dir", "-o", help="Output directory for .adv files"),
    quality_threshold: float = typer.Option(7.0, "--quality", "-q", help="Minimum quality threshold"),
    max_combinations: int = typer.Option(10, "--max", "-m", help="Maximum combinations to generate"),
):
    """Generate adventures from all author/story combinations."""
    
    # Validate directories
    if not os.path.isdir(author_dir):
        console.print(f"❌ Author directory not found: {author_dir}", style="red")
        raise typer.Exit(1)
    
    if not os.path.isdir(story_dir):
        console.print(f"❌ Story directory not found: {story_dir}", style="red")
        raise typer.Exit(1)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all combinations
    author_files = [f for f in os.listdir(author_dir) if f.endswith('.author')]
    story_files = [f for f in os.listdir(story_dir) if f.endswith('.story')]
    
    combinations = [
        (os.path.join(author_dir, a), os.path.join(story_dir, s))
        for a in author_files
        for s in story_files
    ][:max_combinations]
    
    console.print(Panel.fit(
        f"🎮 Batch Adventure Generation\n"
        f"📖 Authors: {len(author_files)} files\n"
        f"📚 Stories: {len(story_files)} files\n"
        f"🔢 Combinations: {len(combinations)}\n"
        f"📁 Output: {output_dir}",
        title="Batch Configuration"
    ))
    
    if not combinations:
        console.print("❌ No valid author/story combinations found", style="red")
        raise typer.Exit(1)
    
    # Run batch generation
    try:
        results = asyncio.run(generate_adventure_batch(
            combinations,
            output_dir,
            enable_streaming=False,  # Disable for batch
            quality_threshold=quality_threshold
        ))
        
        # Display results summary
        _display_batch_results(results, combinations)
        
    except Exception as e:
        console.print(f"❌ Batch generation failed: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def validate(
    adventure_file: str = typer.Argument(..., help="Path to .adv file to validate"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed validation report"),
):
    """Validate an existing .adv adventure file."""
    
    if not os.path.exists(adventure_file):
        console.print(f"❌ Adventure file not found: {adventure_file}", style="red")
        raise typer.Exit(1)
    
    console.print(f"🔍 Validating: {adventure_file}")
    
    try:
        result = asyncio.run(quick_validate_adventure(adventure_file))
        
        if result.success:
            console.print("✅ Validation passed", style="green")
        else:
            console.print(f"❌ Validation failed: {result.message}", style="red")
            
        if verbose:
            console.print("\n📊 Detailed validation report:")
            # This would show detailed validation results
            console.print("(Detailed validation not yet implemented)")
            
    except Exception as e:
        console.print(f"❌ Validation error: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def visualize(
    adventure_file: str = typer.Argument(..., help="Path to .adv file to visualize"),
    format: str = typer.Option("ascii", "--format", "-f", help="Output format: ascii, dot, mermaid, json"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate flow visualization for an adventure."""
    
    if not os.path.exists(adventure_file):
        console.print(f"❌ Adventure file not found: {adventure_file}", style="red")
        raise typer.Exit(1)
    
    console.print(f"📊 Generating {format} visualization for: {adventure_file}")
    
    try:
        # This would require parsing the .adv file first
        # For now, show a placeholder
        console.print("🚧 Visualization feature coming soon!", style="yellow")
        console.print(f"Will generate {format} format visualization")
        
        if output:
            console.print(f"Will save to: {output}")
            
    except Exception as e:
        console.print(f"❌ Visualization failed: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def analyze(
    adventure_file: str = typer.Argument(..., help="Path to .adv file to analyze"),
    author_file: Optional[str] = typer.Option(None, "--author", help="Author file for context"),
    story_file: Optional[str] = typer.Option(None, "--story", help="Story file for context"),
    report_type: str = typer.Option("quality", "--type", "-t", help="Report type: quality, branch, ending, choice"),
):
    """Analyze an adventure file and generate reports."""
    
    if not os.path.exists(adventure_file):
        console.print(f"❌ Adventure file not found: {adventure_file}", style="red")
        raise typer.Exit(1)
    
    console.print(f"📈 Analyzing adventure: {adventure_file}")
    console.print(f"📊 Report type: {report_type}")
    
    try:
        # This would require parsing the .adv file and running analysis tools
        console.print("🚧 Analysis feature coming soon!", style="yellow")
        console.print(f"Will generate {report_type} report")
        
        if author_file and not os.path.exists(author_file):
            console.print(f"⚠️ Author file not found: {author_file}", style="yellow")
            
        if story_file and not os.path.exists(story_file):
            console.print(f"⚠️ Story file not found: {story_file}", style="yellow")
            
    except Exception as e:
        console.print(f"❌ Analysis failed: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def info(
    file: str = typer.Argument(..., help="Path to .author, .story, or .adv file"),
):
    """Display information about an adventure-related file."""
    
    if not os.path.exists(file):
        console.print(f"❌ File not found: {file}", style="red")
        raise typer.Exit(1)
    
    file_ext = Path(file).suffix.lower()
    
    try:
        if file_ext == '.author':
            _display_author_info(file)
        elif file_ext == '.story':
            _display_story_info(file)
        elif file_ext == '.adv':
            _display_adventure_info(file)
        else:
            console.print(f"❌ Unsupported file type: {file_ext}", style="red")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ Error reading file: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def examples(
    list_only: bool = typer.Option(False, "--list", "-l", help="List available examples only"),
    copy_to: Optional[str] = typer.Option(None, "--copy-to", help="Copy examples to directory"),
):
    """Show or copy example files."""
    
    examples_info = [
        ("Terry_Pratchett.author", "Discworld-style author with witty, satirical voice"),
        ("George_Lucas.author", "Epic space opera author style"),
        ("The_Color_Of_Magic_CYOA.story", "Discworld adventure story requirements"),
        ("BlackHawks_TroublesInHyperspace_CYOA.story", "Space adventure story"),
        ("demo.adv", "Example generated adventure file"),
    ]
    
    if list_only:
        table = Table(title="Available Examples")
        table.add_column("File", style="cyan")
        table.add_column("Description", style="green")
        
        for filename, description in examples_info:
            table.add_row(filename, description)
        
        console.print(table)
        return
    
    if copy_to:
        os.makedirs(copy_to, exist_ok=True)
        console.print(f"📁 Copying examples to: {copy_to}")
        
        # This would copy example files
        console.print("🚧 Example copying coming soon!", style="yellow")
        return
    
    # Show examples information
    console.print(Panel.fit(
        "📚 Adventure Generation Examples\n\n"
        "Use --list to see available examples\n"
        "Use --copy-to <dir> to copy examples to a directory\n\n"
        "Example usage:\n"
        "  adventure-agent generate Terry_Pratchett.author The_Color_Of_Magic_CYOA.story\n"
        "  adventure-agent batch examples/authors examples/stories",
        title="Examples Help"
    ))


def _display_generation_summary(data: dict):
    """Display generation pipeline summary."""
    
    if "pipeline_summary" in data:
        summary = data["pipeline_summary"]
        
        table = Table(title="Generation Pipeline Summary")
        table.add_column("Stage", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Tool", style="yellow")
        
        stages = summary.get("stages", [])
        tool_summaries = summary.get("tool_summaries", {})
        
        stage_tool_map = {
            "storyline_generation": "storyline_generator",
            "character_tracking": "character_tracker",
            "inventory_integration": "inventory_integrator",
            "structure_validation": "adv_validator",
            "branch_optimization": "branch_pruner",
            "coherence_analysis": "coherence_analyzer",
            "ending_optimization": "ending_optimizer",
            "choice_analysis": "choice_analyzer",
            "replayability_scoring": "replayability_scorer",
            "flow_visualization": "flow_visualizer"
        }
        
        for stage in stages:
            tool = stage_tool_map.get(stage, "unknown")
            tool_summary = tool_summaries.get(tool, {})
            status = "✅ Success" if tool_summary.get("success", False) else "❌ Failed"
            
            table.add_row(stage.replace("_", " ").title(), status, tool)
        
        console.print(table)
        
        # Overall quality
        overall_quality = summary.get("overall_quality", 0)
        success_rate = summary.get("success_rate", 0) * 100
        
        console.print(f"\n📊 Overall Quality: {overall_quality:.1f}/10")
        console.print(f"✅ Success Rate: {success_rate:.1f}%")


def _display_batch_results(results: List, combinations: List):
    """Display batch generation results."""
    
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    table = Table(title="Batch Generation Results")
    table.add_column("Author", style="cyan")
    table.add_column("Story", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Quality", style="magenta")
    
    for i, (result, (author_file, story_file)) in enumerate(zip(results, combinations)):
        author_name = Path(author_file).stem
        story_name = Path(story_file).stem
        status = "✅ Success" if result.success else "❌ Failed"
        
        quality = "N/A"
        if result.success and result.metadata:
            overall_quality = result.metadata.get("overall_quality", 0)
            quality = f"{overall_quality:.1f}/10"
        
        table.add_row(author_name, story_name, status, quality)
    
    console.print(table)
    console.print(f"\n📊 Batch Summary: {successful} successful, {failed} failed")


def _display_author_info(file_path: str):
    """Display author file information."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        author = parse_author_content(content)
        
        console.print(Panel.fit(
            f"📖 Author Information\n"
            f"Voice & Tone: {', '.join(author.voice_and_tone[:3])}...\n"
            f"Narrative Style: {', '.join(author.narrative_style[:3])}...\n"
            f"Themes: {', '.join(author.themes[:3])}...\n"
            f"World Elements: {len(author.world_elements)} elements\n"
            f"Character Development: {len(author.character_development)} aspects",
            title=f"Author: {Path(file_path).stem}"
        ))
        
    except Exception as e:
        console.print(f"❌ Error parsing author file: {str(e)}", style="red")


def _display_story_info(file_path: str):
    """Display story file information."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        story = parse_story_content(content)
        
        console.print(Panel.fit(
            f"📚 Story Information\n"
            f"Setting: {story.setting.get('location', 'Unknown')}\n"
            f"Main Character: {story.main_character.get('name', 'Unknown')}\n"
            f"Plot: {story.plot[:100]}...\n"
            f"NPCs: {len(story.npcs)} characters\n"
            f"Branches: {len(story.branches)} planned paths\n"
            f"Target Length: {story.technical_requirements.get('length', 'Not specified')}",
            title=f"Story: {Path(file_path).stem}"
        ))
        
    except Exception as e:
        console.print(f"❌ Error parsing story file: {str(e)}", style="red")


def _display_adventure_info(file_path: str):
    """Display adventure file information."""
    
    # This would require parsing the .adv file
    console.print(f"🎮 Adventure file: {file_path}")
    console.print("🚧 Adventure file parsing coming soon!", style="yellow")


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()