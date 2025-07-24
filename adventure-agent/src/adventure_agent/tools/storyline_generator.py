"""
Storyline Generator Tool for the Adventure Generation Agent.

This tool handles the core narrative generation process, transforming author
personas and story requirements into branching adventure narratives.
"""

import asyncio
from typing import Dict, List

from pydantic_ai import Agent, RunContext

from ..models import (
    AdventureGame,
    AuthorPersona,
    Choice,
    ChoiceLabel,
    EndingType,
    StoryRequirements,
    StoryStep,
    ToolResult,
)


class StorylineDependencies:
    """Dependencies for the storyline generator."""
    
    def __init__(self, author: AuthorPersona, story: StoryRequirements):
        self.author = author
        self.story = story


def create_storyline_agent() -> Agent[StorylineDependencies, AdventureGame]:
    """Create a storyline generation agent."""
    return Agent[StorylineDependencies, AdventureGame](
        'gemini-1.5-flash',  # Using Gemini instead of OpenAI
        deps_type=StorylineDependencies,
        output_type=AdventureGame,
        system_prompt=(
            "You are an expert adventure story generator. Create complete branching "
            "narratives that match the author's style and story requirements. "
            "Generate engaging adventures with meaningful choices and consequences."
        ),
    )


# Note: Tool decorators will be applied when agent is created
async def generate_story_steps(
    ctx: RunContext[StorylineDependencies], 
    target_length: int,
    branching_factor: int = 2
) -> List[StoryStep]:
    """
    Generate the core story steps for the adventure.
    
    Args:
        ctx: Agent context with author and story dependencies
        target_length: Target number of story steps
        branching_factor: Average number of choices per step
        
    Returns:
        List of generated story steps
    """
    author = ctx.deps.author
    story = ctx.deps.story
    
    # Create story outline based on author style and story requirements
    steps = []
    
    for step_num in range(1, target_length + 1):
        # Generate narrative for this step
        narrative = await _generate_step_narrative(
            step_num, author, story, target_length
        )
        
        # Generate choices for this step
        choices = await _generate_step_choices(
            step_num, author, story, target_length, branching_factor
        )
        
        step = StoryStep(
            step_id=str(step_num),
            narrative=narrative,
            choices=choices
        )
        steps.append(step)
    
    return steps


async def generate_game_endings(
    ctx: RunContext[StorylineDependencies],
    story_steps: List[StoryStep]
) -> Dict[EndingType, str]:
    """
    Generate appropriate endings for the adventure.
    
    Args:
        ctx: Agent context with author and story dependencies
        story_steps: Generated story steps for context
        
    Returns:
        Dict mapping ending types to ending text
    """
    author = ctx.deps.author
    story = ctx.deps.story
    
    endings = {}
    
    # Generate success ending
    success_ending = await _generate_ending(
        EndingType.SUCCESS, author, story, story_steps
    )
    endings[EndingType.SUCCESS] = success_ending
    
    # Generate failure ending
    failure_ending = await _generate_ending(
        EndingType.FAILURE, author, story, story_steps
    )
    endings[EndingType.FAILURE] = failure_ending
    
    # Generate neutral ending if requested
    if story.technical_requirements.get("endings", 2) >= 3:
        neutral_ending = await _generate_ending(
            EndingType.NEUTRAL, author, story, story_steps
        )
        endings[EndingType.NEUTRAL] = neutral_ending
    
    return endings


async def generate_storyline(
    author: AuthorPersona, 
    story: StoryRequirements
) -> ToolResult:
    """
    Main storyline generation function.
    
    Args:
        author: Author persona defining writing style
        story: Story requirements and constraints
        
    Returns:
        ToolResult containing generated AdventureGame or error information
    """
    try:
        # Set up dependencies
        deps = StorylineDependencies(author, story)
        
        # Get target length from story requirements
        target_length = story.technical_requirements.get("length", 10)
        if isinstance(target_length, str):
            # Extract number from string like "8-12 story steps"
            import re
            match = re.search(r'(\d+)', str(target_length))
            target_length = int(match.group(1)) if match else 10
        
        # Generate the adventure using the agent
        agent = create_storyline_agent()
        result = await agent.run(
            f"Create a {target_length}-step adventure based on the provided "
            f"author style and story requirements. The story should be about: {story.plot}",
            deps=deps
        )
        
        adventure = result.output
        
        # Add metadata
        adventure.game_name = f"{author.themes[0]} Adventure" if author.themes else "Generated Adventure"
        
        return ToolResult(
            success=True,
            data=adventure,
            message=f"Generated {len(adventure.steps)}-step adventure successfully",
            metadata={
                "steps_generated": len(adventure.steps),
                "endings_generated": len(adventure.endings),
                "author_style": author.voice_and_tone[0] if author.voice_and_tone else "unknown"
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Storyline generation failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


async def _generate_step_narrative(
    step_num: int, 
    author: AuthorPersona, 
    story: StoryRequirements, 
    total_steps: int
) -> str:
    """Generate narrative text for a specific step."""
    
    # Determine story progression
    if step_num == 1:
        phase = "opening"
    elif step_num <= total_steps // 3:
        phase = "setup"
    elif step_num <= (total_steps * 2) // 3:
        phase = "development"
    else:
        phase = "climax"
    
    # Create narrative based on author style and story context
    style_elements = ", ".join(author.voice_and_tone[:2])
    narrative_style = ", ".join(author.narrative_style[:2])
    
    # Create a contextual narrative
    setting = story.setting.get("location", "unknown location")
    character_background = story.main_character.get("background", "adventurer")
    
    if phase == "opening":
        narrative = (
            f"You find yourself in {setting}, {character_background} seeking adventure. "
            f"The {phase} of your journey unfolds with {style_elements}. "
            f"The world around you reflects {narrative_style} as you begin to understand "
            f"the challenge ahead. {story.plot[:100]}..."
        )
    else:
        narrative = (
            f"As your adventure continues in {setting}, the {phase} brings new challenges. "
            f"Your character as {character_background} faces decisions that will shape "
            f"the outcome of {story.plot[:50]}... The atmosphere maintains {style_elements} "
            f"while the narrative unfolds with {narrative_style}."
        )
    
    # Ensure minimum length
    while len(narrative) < 50:
        narrative += f" The {phase} deepens as you proceed."
    
    return narrative


async def _generate_step_choices(
    step_num: int,
    author: AuthorPersona,
    story: StoryRequirements, 
    total_steps: int,
    branching_factor: int
) -> List[Choice]:
    """Generate choices for a specific step."""
    
    choices = []
    choice_labels = [ChoiceLabel.A, ChoiceLabel.B, ChoiceLabel.C, ChoiceLabel.D]
    
    num_choices = min(branching_factor, len(choice_labels))
    
    for i in range(num_choices):
        label = choice_labels[i]
        
        # Determine target based on step progression
        if step_num >= total_steps - 1:
            # Last steps should lead to endings
            if i == 0:
                target = "ENDING_SUCCESS"
            elif i == 1:
                target = "ENDING_FAILURE" 
            else:
                target = "ENDING_NEUTRAL"
        else:
            # Regular steps lead to next steps
            target = f"STEP_{step_num + 1}"
        
        # Generate choice description based on author style
        if "witty" in author.voice_and_tone[0].lower():
            descriptions = [
                "Take the clever approach with wit and charm",
                "Use humor to defuse the situation", 
                "Apply unconventional wisdom",
                "Trust in the absurd logic of the universe"
            ]
        else:
            descriptions = [
                "Take the direct approach",
                "Seek more information first",
                "Try a diplomatic solution",
                "Trust your instincts"
            ]
        
        description = descriptions[i] if i < len(descriptions) else f"Choose path {label.value}"
        
        choice = Choice(
            label=label,
            description=description,
            target=target,
            conditions=[],
            consequences=[]
        )
        choices.append(choice)
    
    return choices


async def _generate_ending(
    ending_type: EndingType,
    author: AuthorPersona,
    story: StoryRequirements,
    story_steps: List[StoryStep]
) -> str:
    """Generate an ending of the specified type."""
    
    style = ", ".join(author.voice_and_tone[:2])
    theme = author.themes[0] if author.themes else "adventure"
    
    if ending_type == EndingType.SUCCESS:
        ending = (
            f"Congratulations! Your journey through {story.setting.get('location', 'this world')} "
            f"has reached a triumphant conclusion. With {style}, you have successfully "
            f"resolved the challenge of {story.plot[:50]}... The theme of {theme} "
            f"resonates as you emerge victorious, having grown as {story.main_character.get('background', 'an adventurer')}."
        )
    elif ending_type == EndingType.FAILURE:
        ending = (
            f"Despite your best efforts, your adventure in {story.setting.get('location', 'this world')} "
            f"has not gone as planned. With characteristic {style}, you face the consequences "
            f"of the choices made during {story.plot[:50]}... Yet there is wisdom in this failure, "
            f"and the theme of {theme} teaches valuable lessons about perseverance."
        )
    else:  # NEUTRAL
        ending = (
            f"Your journey through {story.setting.get('location', 'this world')} concludes "
            f"with mixed results. The {style} of your adventure regarding {story.plot[:50]}... "
            f"has led to a complex resolution. The theme of {theme} suggests that not all "
            f"adventures end in clear victory or defeat, but in nuanced understanding."
        )
    
    return ending


async def chunk_storyline_generation(
    author: AuthorPersona,
    story: StoryRequirements,
    chunk_size: int = 5
) -> ToolResult:
    """
    Generate storyline in chunks to handle large adventures.
    
    Args:
        author: Author persona
        story: Story requirements  
        chunk_size: Number of steps per chunk
        
    Returns:
        ToolResult with complete adventure
    """
    try:
        target_length = story.technical_requirements.get("length", 10)
        if isinstance(target_length, str):
            import re
            match = re.search(r'(\d+)', str(target_length))
            target_length = int(match.group(1)) if match else 10
        
        # Generate in chunks if large
        if target_length > chunk_size * 2:
            all_steps = []
            for chunk_start in range(1, target_length + 1, chunk_size):
                chunk_end = min(chunk_start + chunk_size - 1, target_length)
                
                # Generate chunk
                chunk_result = await generate_storyline(author, story)
                if not chunk_result.success:
                    return chunk_result
                
                chunk_adventure = chunk_result.data
                all_steps.extend(list(chunk_adventure.steps.values()))
            
            # Combine chunks into complete adventure
            final_adventure = AdventureGame(
                game_name=f"{author.themes[0]} Adventure" if author.themes else "Generated Adventure",
                steps={str(i+1): step for i, step in enumerate(all_steps[:target_length])},
                endings={}  # Will be generated separately
            )
            
            return ToolResult(
                success=True,
                data=final_adventure,
                message=f"Generated {len(final_adventure.steps)}-step adventure in chunks",
                metadata={"chunked": True, "chunk_size": chunk_size}
            )
        else:
            # Generate normally for smaller adventures
            return await generate_storyline(author, story)
            
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Chunked storyline generation failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )