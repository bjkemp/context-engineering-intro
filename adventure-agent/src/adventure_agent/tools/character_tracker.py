"""
Character Tracker Tool for the Adventure Generation Agent.

This tool maintains character consistency across story branches, ensuring NPCs
have coherent personalities, dialogue patterns, and behavior throughout the adventure.
"""

from typing import Dict, List, Set

from pydantic_ai import Agent, RunContext

from ..models import AdventureGame, AuthorPersona, StoryRequirements, ToolResult


class CharacterProfile:
    """Profile for tracking character consistency."""
    
    def __init__(
        self, 
        name: str, 
        description: str,
        personality_traits: List[str],
        dialogue_style: str,
        role: str,
        relationships: Dict[str, str]
    ):
        self.name = name
        self.description = description
        self.personality_traits = personality_traits
        self.dialogue_style = dialogue_style
        self.role = role
        self.relationships = relationships
        self.appearances: Set[str] = set()  # Track which steps character appears in
        self.dialogue_examples: List[str] = []
        self.consistency_score = 10.0  # Start with perfect score


class CharacterTrackingDependencies:
    """Dependencies for character tracking."""
    
    def __init__(self, author: AuthorPersona, story: StoryRequirements):
        self.author = author
        self.story = story
        self.character_profiles: Dict[str, CharacterProfile] = {}


def create_character_agent() -> Agent[CharacterTrackingDependencies, Dict[str, CharacterProfile]]:
    """Create character tracking agent."""
    return Agent[CharacterTrackingDependencies, Dict[str, CharacterProfile]](
        'gemini-1.5-flash',
        deps_type=CharacterTrackingDependencies,
        output_type=Dict[str, CharacterProfile],
        system_prompt=(
            "You are a character consistency expert. Maintain coherent character "
            "personalities, dialogue patterns, and relationships across all story branches. "
            "Ensure characters behave consistently with their established traits."
        ),
    )


async def analyze_character_consistency(
    ctx: RunContext[CharacterTrackingDependencies],
    adventure: AdventureGame
) -> Dict[str, float]:
    """
    Analyze character consistency across the adventure.
    
    Args:
        ctx: Agent context with character tracking data
        adventure: Adventure to analyze
        
    Returns:
        Dict mapping character names to consistency scores (0-10)
    """
    scores = {}
    
    for character_name, profile in ctx.deps.character_profiles.items():
        score = await _calculate_character_consistency(profile, adventure)
        scores[character_name] = score
        profile.consistency_score = score
    
    return scores


async def generate_character_dialogue(
    ctx: RunContext[CharacterTrackingDependencies],
    character_name: str,
    context: str,
    mood: str = "neutral"
) -> str:
    """
    Generate consistent dialogue for a character.
    
    Args:
        ctx: Agent context
        character_name: Name of the character
        context: Situation context for dialogue
        mood: Character's current mood
        
    Returns:
        Generated dialogue consistent with character
    """
    if character_name not in ctx.deps.character_profiles:
        return f'"{context}" - {character_name}'
    
    profile = ctx.deps.character_profiles[character_name]
    
    # Generate dialogue based on character's established style
    dialogue_style = profile.dialogue_style
    personality = ", ".join(profile.personality_traits)
    
    # Create dialogue prompt based on character profile
    dialogue_prompt = (
        f"Generate dialogue for {character_name} who has {dialogue_style} speech style "
        f"and {personality} personality traits. Context: {context}. Mood: {mood}."
    )
    
    # For now, create template-based dialogue
    # In a full implementation, this would use the agent to generate
    if "formal" in dialogue_style.lower():
        dialogue = f"I must inform you that {context.lower()}."
    elif "witty" in dialogue_style.lower():
        dialogue = f"Well, well... it seems {context.lower()}. How delightfully unexpected!"
    elif "gruff" in dialogue_style.lower():
        dialogue = f"Bah! {context}. What did you expect?"
    else:
        dialogue = f"{context}."
    
    # Store dialogue example
    profile.dialogue_examples.append(dialogue)
    
    return f'"{dialogue}" - {character_name}'


async def track_characters(
    author: AuthorPersona,
    story: StoryRequirements,
    adventure: AdventureGame
) -> ToolResult:
    """
    Main character tracking function.
    
    Args:
        author: Author persona for style consistency
        story: Story requirements with NPC information
        adventure: Adventure to track characters in
        
    Returns:
        ToolResult with character tracking analysis
    """
    try:
        # Initialize character profiles from story requirements
        profiles = await _initialize_character_profiles(author, story)
        
        # Set up dependencies
        deps = CharacterTrackingDependencies(author, story)
        deps.character_profiles = profiles
        
        # Analyze character appearances in adventure
        character_appearances = _analyze_character_appearances(adventure, profiles)
        
        # Check consistency
        consistency_scores = {}
        for name, profile in profiles.items():
            consistency_scores[name] = await _calculate_character_consistency(profile, adventure)
        
        # Generate character report
        report = _generate_character_report(profiles, character_appearances, consistency_scores)
        
        return ToolResult(
            success=True,
            data={
                "profiles": profiles,
                "appearances": character_appearances,
                "consistency_scores": consistency_scores,
                "report": report
            },
            message=f"Tracked {len(profiles)} characters with average consistency: {sum(consistency_scores.values()) / len(consistency_scores) if consistency_scores else 0:.1f}/10",
            metadata={
                "characters_tracked": len(profiles),
                "total_appearances": sum(len(appearances) for appearances in character_appearances.values()),
                "avg_consistency": sum(consistency_scores.values()) / len(consistency_scores) if consistency_scores else 0
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Character tracking failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


async def _initialize_character_profiles(
    author: AuthorPersona, 
    story: StoryRequirements
) -> Dict[str, CharacterProfile]:
    """Initialize character profiles from story requirements."""
    
    profiles = {}
    
    # Process NPCs from story requirements
    for npc_data in story.npcs:
        name = npc_data.get("name", "Unknown")
        description = npc_data.get("description", "")
        role = npc_data.get("role", "supporting character")
        
        # Derive personality traits from description and author style
        personality_traits = _extract_personality_traits(description, author)
        
        # Determine dialogue style based on author and character
        dialogue_style = _determine_dialogue_style(description, author)
        
        profile = CharacterProfile(
            name=name,
            description=description,
            personality_traits=personality_traits,
            dialogue_style=dialogue_style,
            role=role,
            relationships={}
        )
        
        profiles[name] = profile
    
    # Add main character profile
    main_char_data = story.main_character
    main_name = main_char_data.get("name", "Player")
    main_description = main_char_data.get("background", "")
    
    main_profile = CharacterProfile(
        name=main_name,
        description=main_description,
        personality_traits=["determined", "curious"],
        dialogue_style="adaptable",
        role="protagonist",
        relationships={}
    )
    profiles[main_name] = main_profile
    
    return profiles


def _extract_personality_traits(description: str, author: AuthorPersona) -> List[str]:
    """Extract personality traits from character description."""
    
    traits = []
    
    # Extract traits from description
    description_lower = description.lower()
    
    trait_keywords = {
        "wise": ["wise", "knowledgeable", "experienced"],
        "humorous": ["funny", "witty", "comic", "humorous"],
        "serious": ["serious", "stern", "grave", "solemn"],
        "friendly": ["friendly", "kind", "warm", "welcoming"],
        "suspicious": ["suspicious", "wary", "cautious", "distrustful"],
        "brave": ["brave", "courageous", "bold", "fearless"],
        "clever": ["clever", "smart", "intelligent", "cunning"]
    }
    
    for trait, keywords in trait_keywords.items():
        if any(keyword in description_lower for keyword in keywords):
            traits.append(trait)
    
    # Add traits based on author style
    if "witty" in " ".join(author.voice_and_tone).lower():
        traits.append("quick-witted")
    
    if "philosophical" in " ".join(author.themes).lower():
        traits.append("thoughtful")
    
    # Ensure we have at least 2 traits
    if len(traits) < 2:
        traits.extend(["distinctive", "memorable"])
    
    return traits[:4]  # Limit to 4 traits for focus


def _determine_dialogue_style(description: str, author: AuthorPersona) -> str:
    """Determine dialogue style for character."""
    
    description_lower = description.lower()
    
    # Map description keywords to dialogue styles
    if any(word in description_lower for word in ["formal", "official", "authority"]):
        return "formal and authoritative"
    elif any(word in description_lower for word in ["witty", "clever", "humorous"]):
        return "witty and clever"
    elif any(word in description_lower for word in ["gruff", "rough", "tough"]):
        return "gruff and direct"
    elif any(word in description_lower for word in ["wise", "old", "experienced"]):
        return "wise and measured"
    else:
        # Default based on author style
        if "witty" in " ".join(author.voice_and_tone).lower():
            return "conversational with wit"
        else:
            return "clear and engaging"


def _analyze_character_appearances(
    adventure: AdventureGame,
    profiles: Dict[str, CharacterProfile]
) -> Dict[str, Set[str]]:
    """Analyze which steps each character appears in."""
    
    appearances = {name: set() for name in profiles.keys()}
    
    for step_id, step in adventure.steps.items():
        # Check narrative for character mentions
        narrative_lower = step.narrative.lower()
        
        for char_name in profiles.keys():
            if char_name.lower() in narrative_lower:
                appearances[char_name].add(step_id)
                profiles[char_name].appearances.add(step_id)
        
        # Check choices for character mentions
        for choice in step.choices:
            choice_text_lower = choice.description.lower()
            for char_name in profiles.keys():
                if char_name.lower() in choice_text_lower:
                    appearances[char_name].add(step_id)
                    profiles[char_name].appearances.add(step_id)
    
    return appearances


async def _calculate_character_consistency(
    profile: CharacterProfile,
    adventure: AdventureGame
) -> float:
    """Calculate consistency score for a character."""
    
    base_score = 10.0
    
    # Check for character appearances
    if not profile.appearances:
        return 5.0  # Neutral score for characters that don't appear
    
    # Analyze dialogue consistency (simplified)
    if len(profile.dialogue_examples) > 1:
        # Check for style consistency across dialogue examples
        styles = [_analyze_dialogue_style(dialogue) for dialogue in profile.dialogue_examples]
        if len(set(styles)) > 1:
            base_score -= 1.0  # Deduct for inconsistent dialogue styles
    
    # Check appearance frequency (characters should appear meaningfully)
    appearance_ratio = len(profile.appearances) / len(adventure.steps)
    if profile.role == "major" and appearance_ratio < 0.3:
        base_score -= 2.0  # Major characters should appear frequently
    elif profile.role == "supporting" and appearance_ratio > 0.8:
        base_score -= 1.0  # Supporting characters shouldn't dominate
    
    return max(0.0, min(10.0, base_score))


def _analyze_dialogue_style(dialogue: str) -> str:
    """Analyze the style of a dialogue sample."""
    
    dialogue_lower = dialogue.lower()
    
    if "!" in dialogue and ("well" in dialogue_lower or "ah" in dialogue_lower):
        return "exclamatory"
    elif dialogue.endswith("..."):
        return "hesitant"
    elif len(dialogue) > 100:
        return "verbose"
    elif "?" in dialogue:
        return "questioning"
    else:
        return "standard"


def _generate_character_report(
    profiles: Dict[str, CharacterProfile],
    appearances: Dict[str, Set[str]],
    consistency_scores: Dict[str, float]
) -> str:
    """Generate a character tracking report."""
    
    lines = ["=== Character Tracking Report ===", ""]
    
    for name, profile in profiles.items():
        lines.append(f"Character: {name}")
        lines.append(f"  Role: {profile.role}")
        lines.append(f"  Personality: {', '.join(profile.personality_traits)}")
        lines.append(f"  Dialogue Style: {profile.dialogue_style}")
        lines.append(f"  Appearances: {len(appearances.get(name, set()))} steps")
        lines.append(f"  Consistency Score: {consistency_scores.get(name, 0):.1f}/10")
        lines.append("")
    
    # Summary
    avg_consistency = sum(consistency_scores.values()) / len(consistency_scores) if consistency_scores else 0
    lines.append(f"Average Consistency: {avg_consistency:.1f}/10")
    
    return "\n".join(lines)


async def enhance_character_consistency(
    adventure: AdventureGame,
    profiles: Dict[str, CharacterProfile]
) -> AdventureGame:
    """
    Enhance character consistency in an existing adventure.
    
    Args:
        adventure: Adventure to enhance
        profiles: Character profiles to maintain consistency
        
    Returns:
        Enhanced adventure with improved character consistency
    """
    enhanced_steps = {}
    
    for step_id, step in adventure.steps.items():
        enhanced_narrative = step.narrative
        
        # Check for character mentions and enhance consistency
        for char_name, profile in profiles.items():
            if char_name.lower() in step.narrative.lower():
                # Ensure character traits are reflected in narrative
                if profile.personality_traits:
                    trait_hint = profile.personality_traits[0]
                    # Add subtle trait reinforcement if not already present
                    if trait_hint.lower() not in enhanced_narrative.lower():
                        enhanced_narrative += f" {char_name}'s {trait_hint} nature is evident."
        
        enhanced_steps[step_id] = step.model_copy(update={"narrative": enhanced_narrative})
    
    return adventure.model_copy(update={"steps": enhanced_steps})