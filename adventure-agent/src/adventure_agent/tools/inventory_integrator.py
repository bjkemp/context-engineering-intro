"""
Inventory Integrator Tool for the Adventure Generation Agent.

This tool generates appropriate items, stats, and game mechanics that integrate
seamlessly with the narrative and enhance gameplay experience.
"""

from typing import Dict, List, Union

from pydantic_ai import Agent, RunContext

from ..models import (
    AdventureGame,
    AuthorPersona,
    StoryRequirements,
    ToolResult,
)


class InventoryDependencies:
    """Dependencies for inventory integration."""
    
    def __init__(self, author: AuthorPersona, story: StoryRequirements):
        self.author = author
        self.story = story


def create_inventory_agent() -> Agent[InventoryDependencies, Dict[str, Union[str, int]]]:
    """Create inventory integration agent."""
    return Agent[InventoryDependencies, Dict[str, Union[str, int]]](
        'gemini-1.5-flash',
        deps_type=InventoryDependencies,
        output_type=Dict[str, Union[str, int]],
        system_prompt=(
            "You are a game mechanics expert. Generate appropriate inventory items, "
            "character stats, and game variables that enhance the narrative experience "
            "while maintaining balance and thematic consistency."
        ),
    )


async def generate_starting_inventory(
    ctx: RunContext[InventoryDependencies],
    character_background: str
) -> Dict[str, Union[str, int]]:
    """
    Generate starting inventory based on character background.
    
    Args:
        ctx: Agent context with author and story dependencies
        character_background: Background of the main character
        
    Returns:
        Dict of inventory items and quantities
    """
    author = ctx.deps.author
    story = ctx.deps.story
    
    inventory = {}
    
    # Base items for most adventures
    inventory["coins"] = 50
    
    # Items based on character background
    background_lower = character_background.lower()
    
    if "scholar" in background_lower or "student" in background_lower:
        inventory["notebook"] = 1
        inventory["quill"] = 1
        inventory["research_notes"] = "incomplete"
    elif "merchant" in background_lower or "trader" in background_lower:
        inventory["coins"] = 100
        inventory["trade_goods"] = 3
        inventory["ledger"] = 1
    elif "guard" in background_lower or "soldier" in background_lower:
        inventory["sword"] = 1
        inventory["armor"] = "leather"
        inventory["badge"] = 1
    elif "thief" in background_lower or "rogue" in background_lower:
        inventory["lockpicks"] = 1
        inventory["rope"] = 1
        inventory["coins"] = 25  # Less money but more tools
    else:
        # Default adventurer kit
        inventory["backpack"] = 1
        inventory["rations"] = 3
        inventory["water"] = 2
    
    # Items based on story setting
    setting_location = story.setting.get("location", "").lower()
    
    if "city" in setting_location:
        inventory["city_map"] = 1
    elif "forest" in setting_location or "wilderness" in setting_location:
        inventory["compass"] = 1
        inventory["rope"] = 1
    elif "dungeon" in setting_location or "underground" in setting_location:
        inventory["torch"] = 3
        inventory["flint"] = 1
    
    # Theme-based items from author
    if author.world_elements:
        for element in author.world_elements[:2]:  # Limit to 2 elements
            element_lower = element.lower()
            if "magic" in element_lower:
                inventory["magic_charm"] = 1
            elif "steampunk" in element_lower:
                inventory["gear_toolkit"] = 1
            elif "postal" in element_lower or "mail" in element_lower:
                inventory["official_letter"] = 1
    
    return inventory


async def generate_character_stats(
    ctx: RunContext[InventoryDependencies],
    character_background: str
) -> Dict[str, Union[str, int]]:
    """
    Generate character stats appropriate for the adventure.
    
    Args:
        ctx: Agent context
        character_background: Character's background
        
    Returns:
        Dict of character stats
    """
    author = ctx.deps.author
    story = ctx.deps.story
    
    stats = {}
    
    # Base stats
    stats["health"] = 100
    stats["reputation"] = 50
    
    # Background-based stat adjustments
    background_lower = character_background.lower()
    
    if "scholar" in background_lower:
        stats["intelligence"] = 80
        stats["knowledge"] = 75
        stats["physical"] = 40
    elif "guard" in background_lower or "soldier" in background_lower:
        stats["physical"] = 80
        stats["combat"] = 75
        stats["intelligence"] = 50
    elif "merchant" in background_lower:
        stats["charisma"] = 75
        stats["negotiation"] = 80
        stats["wealth"] = 70
    elif "thief" in background_lower:
        stats["stealth"] = 80
        stats["agility"] = 75
        stats["reputation"] = 30  # Lower starting reputation
    else:
        # Balanced stats for general adventurer
        stats["intelligence"] = 60
        stats["physical"] = 60
        stats["charisma"] = 60
    
    # Story-specific stats
    if "postal" in story.plot.lower():
        stats["mail_delivery_skill"] = 50
    if "watch" in story.plot.lower() or "police" in story.plot.lower():
        stats["investigation_skill"] = 50
    if "magic" in story.plot.lower():
        stats["magical_awareness"] = 40
    
    return stats


async def generate_game_variables(
    ctx: RunContext[InventoryDependencies],
    adventure_plot: str
) -> Dict[str, Union[str, int]]:
    """
    Generate game variables that track adventure progress.
    
    Args:
        ctx: Agent context
        adventure_plot: Main plot of the adventure
        
    Returns:
        Dict of game variables
    """
    variables = {}
    
    # Standard progress tracking
    variables["story_progress"] = 0
    variables["chapters_completed"] = 0
    
    # Plot-specific variables
    plot_lower = adventure_plot.lower()
    
    if "mystery" in plot_lower or "investigation" in plot_lower:
        variables["clues_found"] = 0
        variables["suspects_questioned"] = 0
        variables["evidence_collected"] = 0
    
    if "postal" in plot_lower or "mail" in plot_lower:
        variables["letters_delivered"] = 0
        variables["postal_reputation"] = 50
        variables["mail_service_efficiency"] = 100
    
    if "clacks" in plot_lower or "communication" in plot_lower:
        variables["clacks_messages_sent"] = 0
        variables["communication_network_health"] = 100
    
    if "watch" in plot_lower or "guard" in plot_lower:
        variables["crimes_solved"] = 0
        variables["watch_standing"] = 50
        variables["public_safety"] = 100
    
    # Faction reputation tracking
    factions = _extract_factions_from_plot(adventure_plot)
    for faction in factions:
        variables[f"{faction.lower()}_reputation"] = 50
    
    # Time tracking
    variables["day"] = 1
    variables["time_limit"] = 7  # Default week-long adventure
    
    return variables


async def integrate_inventory(
    author: AuthorPersona,
    story: StoryRequirements,
    adventure: AdventureGame
) -> ToolResult:
    """
    Main inventory integration function.
    
    Args:
        author: Author persona for thematic consistency
        story: Story requirements
        adventure: Adventure to enhance with inventory
        
    Returns:
        ToolResult with enhanced adventure including inventory
    """
    try:
        # Set up dependencies
        deps = InventoryDependencies(author, story)
        
        # Generate starting inventory
        character_background = story.main_character.get("background", "adventurer")
        inventory = await _generate_inventory_items(deps, character_background)
        
        # Generate character stats
        stats = await _generate_character_attributes(deps, character_background)
        
        # Generate game variables
        variables = await _generate_progress_variables(deps, story.plot)
        
        # Integrate inventory into story choices
        enhanced_adventure = await _integrate_inventory_into_choices(
            adventure, inventory, stats, variables
        )
        
        # Update adventure with inventory data
        enhanced_adventure.inventory = inventory
        enhanced_adventure.stats = stats
        enhanced_adventure.variables = variables
        
        return ToolResult(
            success=True,
            data=enhanced_adventure,
            message=f"Integrated {len(inventory)} inventory items, {len(stats)} stats, and {len(variables)} variables",
            metadata={
                "inventory_items": len(inventory),
                "character_stats": len(stats),
                "game_variables": len(variables),
                "integration_type": "comprehensive"
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Inventory integration failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


async def _generate_inventory_items(
    deps: InventoryDependencies,
    character_background: str
) -> Dict[str, Union[str, int]]:
    """Generate comprehensive inventory."""
    
    inventory = {}
    
    # Basic survival items
    inventory["coins"] = 50
    inventory["health_potion"] = 2
    
    # Background-specific items
    if "scholar" in character_background.lower():
        inventory.update({
            "research_journal": 1,
            "magnifying_glass": 1,
            "ink_bottle": 1,
            "reference_book": "basic"
        })
    elif "postal" in deps.story.plot.lower():
        inventory.update({
            "official_postal_badge": 1,
            "mail_pouch": 1,
            "delivery_log": "empty",
            "postal_uniform": "standard"
        })
    elif "guard" in character_background.lower():
        inventory.update({
            "watch_badge": 1,
            "handcuffs": 1,
            "whistle": 1,
            "patrol_notes": "blank"
        })
    
    # Setting-specific items
    setting = deps.story.setting.get("location", "").lower()
    if "ankh-morpork" in setting:
        inventory["city_guide"] = 1
        inventory["street_map"] = "partial"
    
    # Author style items
    if "witty" in " ".join(deps.author.voice_and_tone).lower():
        inventory["joke_book"] = 1
    
    return inventory


async def _generate_character_attributes(
    deps: InventoryDependencies,
    character_background: str
) -> Dict[str, Union[str, int]]:
    """Generate character attributes and stats."""
    
    stats = {}
    
    # Core attributes
    stats["health"] = 100
    stats["stamina"] = 100
    stats["morale"] = 80
    
    # Skill-based stats
    background_lower = character_background.lower()
    
    if "scholar" in background_lower:
        stats.update({
            "research_skill": 75,
            "knowledge_base": 80,
            "observation": 70,
            "physical_fitness": 40
        })
    elif "postal" in deps.story.plot.lower():
        stats.update({
            "delivery_efficiency": 70,
            "route_knowledge": 60,
            "customer_service": 65,
            "package_handling": 75
        })
    elif "guard" in background_lower:
        stats.update({
            "law_enforcement": 75,
            "physical_fitness": 80,
            "investigation": 65,
            "authority": 70
        })
    else:
        # Balanced adventurer
        stats.update({
            "adaptability": 70,
            "problem_solving": 65,
            "social_skills": 60,
            "resourcefulness": 75
        })
    
    # Reputation tracking
    stats["public_reputation"] = 50
    stats["professional_standing"] = 60
    
    return stats


async def _generate_progress_variables(
    deps: InventoryDependencies,
    plot: str
) -> Dict[str, Union[str, int]]:
    """Generate variables for tracking story progress."""
    
    variables = {}
    
    # Universal progress tracking
    variables["story_stage"] = 1
    variables["major_decisions_made"] = 0
    variables["completion_percentage"] = 0
    
    # Plot-specific tracking
    plot_lower = plot.lower()
    
    if "clacks" in plot_lower or "communication" in plot_lower:
        variables.update({
            "messages_investigated": 0,
            "clacks_towers_visited": 0,
            "communication_disruptions_found": 0,
            "signal_quality": 100
        })
    
    if "mystery" in plot_lower:
        variables.update({
            "evidence_pieces": 0,
            "witnesses_interviewed": 0,
            "false_leads_eliminated": 0,
            "investigation_depth": 0
        })
    
    if "postal" in plot_lower:
        variables.update({
            "mail_route_efficiency": 100,
            "customer_satisfaction": 80,
            "delivery_success_rate": 100,
            "postal_network_health": 90
        })
    
    # Time and deadline tracking
    variables["current_day"] = 1
    variables["time_pressure"] = 50
    variables["deadline_approaching"] = False
    
    # Relationship tracking
    for npc in deps.story.npcs:
        npc_name = npc.get("name", "").replace(" ", "_").lower()
        if npc_name:
            variables[f"relationship_{npc_name}"] = 50
    
    return variables


async def _integrate_inventory_into_choices(
    adventure: AdventureGame,
    inventory: Dict[str, Union[str, int]],
    stats: Dict[str, Union[str, int]],
    variables: Dict[str, Union[str, int]]
) -> AdventureGame:
    """Integrate inventory mechanics into story choices."""
    
    enhanced_steps = {}
    
    for step_id, step in adventure.steps.items():
        enhanced_choices = []
        
        for choice in step.choices:
            enhanced_choice = choice.model_copy()
            
            # Add inventory-based conditions and consequences
            description_lower = choice.description.lower()
            
            # Add conditions based on available items
            if "investigate" in description_lower and "magnifying_glass" in inventory:
                enhanced_choice.conditions.append("IF inventory.magnifying_glass >= 1")
                enhanced_choice.consequences.append("SET investigation_bonus +5")
            
            if "deliver" in description_lower and "mail_pouch" in inventory:
                enhanced_choice.conditions.append("IF inventory.mail_pouch >= 1")
                enhanced_choice.consequences.append("SET delivery_success_rate +10")
            
            if "fight" in description_lower or "combat" in description_lower:
                if "sword" in inventory:
                    enhanced_choice.consequences.append("SET combat_bonus +10")
                enhanced_choice.consequences.append("USE health -10")
            
            # Add stat-based conditions
            if "negotiate" in description_lower:
                enhanced_choice.conditions.append("IF stats.charisma >= 60")
                enhanced_choice.consequences.append("SET public_reputation +5")
            
            if "research" in description_lower:
                enhanced_choice.conditions.append("IF stats.research_skill >= 50")
                enhanced_choice.consequences.append("SET knowledge_base +5")
            
            enhanced_choices.append(enhanced_choice)
        
        enhanced_steps[step_id] = step.model_copy(update={"choices": enhanced_choices})
    
    return adventure.model_copy(update={"steps": enhanced_steps})


def _extract_factions_from_plot(plot: str) -> List[str]:
    """Extract faction names from plot description."""
    
    factions = []
    plot_lower = plot.lower()
    
    # Common faction keywords
    faction_keywords = {
        "watch": ["watch", "city watch", "police"],
        "postal": ["postal", "post office", "mail"],
        "university": ["university", "wizards", "magic"],
        "thieves": ["thieves", "criminals", "underground"],
        "merchants": ["merchants", "traders", "guild"],
        "government": ["government", "patrician", "officials"]
    }
    
    for faction, keywords in faction_keywords.items():
        if any(keyword in plot_lower for keyword in keywords):
            factions.append(faction)
    
    return factions


async def balance_inventory_progression(
    adventure: AdventureGame,
    difficulty_curve: str = "gradual"
) -> AdventureGame:
    """
    Balance inventory acquisition and usage throughout the adventure.
    
    Args:
        adventure: Adventure to balance
        difficulty_curve: Type of difficulty progression
        
    Returns:
        Adventure with balanced inventory progression
    """
    total_steps = len(adventure.steps)
    
    for i, (step_id, step) in enumerate(adventure.steps.items()):
        step_progress = (i + 1) / total_steps
        
        # Adjust inventory rewards based on progress
        enhanced_choices = []
        
        for choice in step.choices:
            enhanced_choice = choice.model_copy()
            
            # Early game: basic items
            if step_progress < 0.3:
                if "explore" in choice.description.lower():
                    enhanced_choice.consequences.append("USE stamina -5")
                    enhanced_choice.consequences.append("SET coins +10")
            
            # Mid game: useful items
            elif step_progress < 0.7:
                if "complete" in choice.description.lower():
                    enhanced_choice.consequences.append("SET reputation +10")
                    if "special_item" not in adventure.inventory:
                        enhanced_choice.consequences.append("ADD inventory.special_item 1")
            
            # Late game: powerful items or consequences
            else:
                if "confront" in choice.description.lower():
                    enhanced_choice.consequences.append("USE special_item -1")
                    enhanced_choice.consequences.append("SET story_progress +20")
            
            enhanced_choices.append(enhanced_choice)
        
        adventure.steps[step_id] = step.model_copy(update={"choices": enhanced_choices})
    
    return adventure