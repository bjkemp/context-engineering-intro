"""
Coherence Analyzer Tool for the Adventure Generation Agent.

This tool validates plot logic and narrative flow, ensuring story consistency,
character behavior coherence, and logical progression throughout the adventure.
"""

import re
from typing import Dict, List, Set, Tuple

from pydantic_ai import Agent, RunContext

from ..models import AdventureGame, AuthorPersona, StoryRequirements, ToolResult


class CoherenceIssue:
    """Represents a coherence issue with severity and location."""
    
    def __init__(self, issue_type: str, description: str, location: str, severity: str = "medium"):
        self.issue_type = issue_type
        self.description = description
        self.location = location
        self.severity = severity  # low, medium, high, critical
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.issue_type}: {self.description} ({self.location})"


class CoherenceAnalysis:
    """Analysis results for story coherence."""
    
    def __init__(self):
        self.plot_issues: List[CoherenceIssue] = []
        self.character_issues: List[CoherenceIssue] = []
        self.narrative_issues: List[CoherenceIssue] = []
        self.logic_issues: List[CoherenceIssue] = []
        self.consistency_score: float = 0.0
        self.readability_score: float = 0.0
        self.engagement_score: float = 0.0
        self.overall_coherence_score: float = 0.0


class CoherenceDependencies:
    """Dependencies for coherence analysis."""
    
    def __init__(self, author: AuthorPersona, story: StoryRequirements):
        self.author = author
        self.story = story
        self.analysis = CoherenceAnalysis()


def create_coherence_agent() -> Agent[CoherenceDependencies, CoherenceAnalysis]:
    """Create coherence analysis agent."""
    return Agent[CoherenceDependencies, CoherenceAnalysis](
        'gemini-1.5-flash',
        deps_type=CoherenceDependencies,
        output_type=CoherenceAnalysis,
        system_prompt=(
            "You are a narrative coherence expert. Analyze story logic, plot "
            "consistency, character behavior, and narrative flow. Identify "
            "contradictions, plot holes, and areas that break immersion."
        ),
    )


async def analyze_plot_coherence(
    ctx: RunContext[CoherenceDependencies],
    adventure: AdventureGame
) -> List[CoherenceIssue]:
    """
    Analyze plot logic and consistency.
    
    Args:
        ctx: Agent context with author and story dependencies
        adventure: Adventure to analyze
        
    Returns:
        List of plot coherence issues
    """
    issues = []
    
    # Check plot progression
    issues.extend(await _check_plot_progression(adventure, ctx.deps.story))
    
    # Check for contradictions
    issues.extend(await _check_plot_contradictions(adventure))
    
    # Check motivation consistency
    issues.extend(await _check_character_motivations(adventure, ctx.deps.story))
    
    # Check setting consistency
    issues.extend(await _check_setting_consistency(adventure, ctx.deps.story))
    
    return issues


async def analyze_narrative_flow(
    ctx: RunContext[CoherenceDependencies],
    adventure: AdventureGame
) -> List[CoherenceIssue]:
    """
    Analyze narrative flow and readability.
    
    Args:
        ctx: Agent context
        adventure: Adventure to analyze
        
    Returns:
        List of narrative flow issues
    """
    issues = []
    
    # Check pacing
    issues.extend(await _check_narrative_pacing(adventure))
    
    # Check transitions
    issues.extend(await _check_narrative_transitions(adventure))
    
    # Check tone consistency
    issues.extend(await _check_tone_consistency(adventure, ctx.deps.author))
    
    # Check information flow
    issues.extend(await _check_information_flow(adventure))
    
    return issues


async def analyze_coherence(
    author: AuthorPersona,
    story: StoryRequirements,
    adventure: AdventureGame
) -> ToolResult:
    """
    Main coherence analysis function.
    
    Args:
        author: Author persona for style consistency
        story: Story requirements for plot consistency
        adventure: Adventure to analyze
        
    Returns:
        ToolResult with coherence analysis
    """
    try:
        # Set up dependencies
        deps = CoherenceDependencies(author, story)
        
        # Analyze different aspects of coherence
        plot_issues = await _analyze_plot_coherence_impl(adventure, story)
        character_issues = await _analyze_character_coherence(adventure, story)
        narrative_issues = await _analyze_narrative_coherence(adventure, author)
        logic_issues = await _analyze_logical_consistency(adventure)
        
        # Calculate scores
        scores = _calculate_coherence_scores(plot_issues, character_issues, narrative_issues, logic_issues, adventure)
        
        # Compile analysis
        analysis = CoherenceAnalysis()
        analysis.plot_issues = plot_issues
        analysis.character_issues = character_issues
        analysis.narrative_issues = narrative_issues
        analysis.logic_issues = logic_issues
        analysis.consistency_score = scores["consistency"]
        analysis.readability_score = scores["readability"]
        analysis.engagement_score = scores["engagement"]
        analysis.overall_coherence_score = scores["overall"]
        
        # Generate recommendations
        recommendations = _generate_coherence_recommendations(analysis)
        
        # Generate detailed report
        report = _generate_coherence_report(analysis, adventure)
        
        total_issues = len(plot_issues) + len(character_issues) + len(narrative_issues) + len(logic_issues)
        critical_issues = len([i for issues in [plot_issues, character_issues, narrative_issues, logic_issues] 
                              for i in issues if i.severity == "critical"])
        
        return ToolResult(
            success=critical_issues == 0,
            data={
                "analysis": analysis,
                "scores": scores,
                "recommendations": recommendations,
                "report": report,
                "issue_summary": {
                    "total_issues": total_issues,
                    "critical_issues": critical_issues,
                    "plot_issues": len(plot_issues),
                    "character_issues": len(character_issues),
                    "narrative_issues": len(narrative_issues),
                    "logic_issues": len(logic_issues)
                }
            },
            message=f"Coherence analysis: {scores['overall']:.1f}/10 overall score, {total_issues} issues found ({critical_issues} critical)",
            metadata={
                "overall_score": scores["overall"],
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "analysis_type": "comprehensive"
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Coherence analysis failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


async def _analyze_plot_coherence_impl(adventure: AdventureGame, story: StoryRequirements) -> List[CoherenceIssue]:
    """Analyze plot coherence and consistency."""
    
    issues = []
    
    # Check if adventure follows the intended plot
    plot_summary = story.plot.lower()
    adventure_content = _extract_adventure_content(adventure).lower()
    
    # Check for key plot elements
    plot_keywords = _extract_plot_keywords(plot_summary)
    missing_elements = []
    
    for keyword in plot_keywords:
        if keyword not in adventure_content:
            missing_elements.append(keyword)
    
    if missing_elements:
        issues.append(CoherenceIssue(
            "MISSING_PLOT_ELEMENTS",
            f"Adventure doesn't include key plot elements: {', '.join(missing_elements)}",
            "OVERALL_PLOT",
            "high"
        ))
    
    # Check plot progression
    step_order = list(adventure.steps.keys())
    if len(step_order) > 1:
        # Check for logical progression
        progression_issues = _check_step_progression(adventure, step_order)
        issues.extend(progression_issues)
    
    # Check for plot contradictions
    contradictions = _find_plot_contradictions(adventure)
    issues.extend(contradictions)
    
    # Check ending consistency with plot
    ending_issues = _check_ending_plot_consistency(adventure, story)
    issues.extend(ending_issues)
    
    return issues


async def _analyze_character_coherence(adventure: AdventureGame, story: StoryRequirements) -> List[CoherenceIssue]:
    """Analyze character behavior consistency."""
    
    issues = []
    
    # Extract character information from story requirements
    main_character = story.main_character
    npcs = story.npcs
    
    # Check main character consistency
    if main_character:
        char_issues = _check_character_consistency(adventure, main_character, "main_character")
        issues.extend(char_issues)
    
    # Check NPC consistency
    for npc in npcs:
        npc_issues = _check_character_consistency(adventure, npc, f"npc_{npc.get('name', 'unknown')}")
        issues.extend(npc_issues)
    
    # Check for character development
    development_issues = _check_character_development(adventure, main_character)
    issues.extend(development_issues)
    
    return issues


async def _analyze_narrative_coherence(adventure: AdventureGame, author: AuthorPersona) -> List[CoherenceIssue]:
    """Analyze narrative style and flow."""
    
    issues = []
    
    # Check tone consistency
    tone_issues = _check_narrative_tone(adventure, author)
    issues.extend(tone_issues)
    
    # Check writing style consistency
    style_issues = _check_writing_style_consistency(adventure, author)
    issues.extend(style_issues)
    
    # Check pacing
    pacing_issues = _check_narrative_pacing_impl(adventure)
    issues.extend(pacing_issues)
    
    # Check transitions between steps
    transition_issues = _check_step_transitions(adventure)
    issues.extend(transition_issues)
    
    return issues


async def _analyze_logical_consistency(adventure: AdventureGame) -> List[CoherenceIssue]:
    """Analyze logical consistency and common sense."""
    
    issues = []
    
    # Check choice consequences
    consequence_issues = _check_choice_logic(adventure)
    issues.extend(consequence_issues)
    
    # Check for impossible situations
    impossibility_issues = _check_logical_impossibilities(adventure)
    issues.extend(impossibility_issues)
    
    # Check temporal consistency
    temporal_issues = _check_temporal_consistency(adventure)
    issues.extend(temporal_issues)
    
    return issues


def _extract_adventure_content(adventure: AdventureGame) -> str:
    """Extract all text content from the adventure."""
    
    content_parts = []
    
    # Add narratives
    for step in adventure.steps.values():
        content_parts.append(step.narrative)
        
        # Add choice descriptions
        for choice in step.choices:
            content_parts.append(choice.description)
    
    # Add endings
    for ending in adventure.endings.values():
        content_parts.append(ending)
    
    return " ".join(content_parts)


def _extract_plot_keywords(plot_text: str) -> List[str]:
    """Extract key plot elements from plot description."""
    
    # Remove common words and extract meaningful terms
    common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    
    words = re.findall(r'\b\w+\b', plot_text.lower())
    keywords = [word for word in words if len(word) > 3 and word not in common_words]
    
    # Return unique keywords
    return list(set(keywords))


def _check_step_progression(adventure: AdventureGame, step_order: List[str]) -> List[CoherenceIssue]:
    """Check logical progression between steps."""
    
    issues = []
    
    for i in range(len(step_order) - 1):
        current_id = step_order[i]
        next_id = step_order[i + 1]
        
        current_step = adventure.steps.get(current_id)
        next_step = adventure.steps.get(next_id)
        
        if current_step and next_step:
            # Check if progression makes sense
            current_narrative = current_step.narrative.lower()
            next_narrative = next_step.narrative.lower()
            
            # Look for jarring transitions
            if _has_jarring_transition(current_narrative, next_narrative):
                issues.append(CoherenceIssue(
                    "JARRING_TRANSITION",
                    f"Abrupt narrative transition from step {current_id} to {next_id}",
                    f"STEP_{current_id} -> STEP_{next_id}",
                    "medium"
                ))
    
    return issues


def _has_jarring_transition(current_text: str, next_text: str) -> bool:
    """Check if transition between narratives is jarring."""
    
    # Simplified check - look for dramatic setting or tone changes
    setting_words = ["forest", "city", "dungeon", "castle", "tavern", "library", "street", "room"]
    
    current_settings = [word for word in setting_words if word in current_text]
    next_settings = [word for word in setting_words if word in next_text]
    
    # If settings change completely without explanation, it might be jarring
    if current_settings and next_settings and not set(current_settings) & set(next_settings):
        return True
    
    return False


def _find_plot_contradictions(adventure: AdventureGame) -> List[CoherenceIssue]:
    """Find contradictions in the plot."""
    
    issues = []
    
    # Extract facts from narratives
    all_facts = []
    
    for step_id, step in adventure.steps.items():
        facts = _extract_facts_from_text(step.narrative, f"STEP_{step_id}")
        all_facts.extend(facts)
    
    # Look for contradictions
    contradictions = _find_contradictory_facts(all_facts)
    
    for contradiction in contradictions:
        issues.append(CoherenceIssue(
            "PLOT_CONTRADICTION",
            f"Contradictory statements: {contradiction['fact1']['text']} vs {contradiction['fact2']['text']}",
            f"{contradiction['fact1']['location']} / {contradiction['fact2']['location']}",
            "high"
        ))
    
    return issues


def _extract_facts_from_text(text: str, location: str) -> List[Dict]:
    """Extract factual statements from text."""
    
    facts = []
    
    # Simple fact extraction - look for definitive statements
    sentences = re.split(r'[.!?]', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:  # Ignore very short fragments
            # Look for definitive patterns
            if any(pattern in sentence.lower() for pattern in ["you are", "the", "there is", "you have"]):
                facts.append({
                    "text": sentence,
                    "location": location,
                    "type": "statement"
                })
    
    return facts


def _find_contradictory_facts(facts: List[Dict]) -> List[Dict]:
    """Find contradictory facts."""
    
    contradictions = []
    
    # Simple contradiction detection
    for i in range(len(facts)):
        for j in range(i + 1, len(facts)):
            fact1 = facts[i]
            fact2 = facts[j]
            
            # Look for direct negations or contradictory statements
            if _are_contradictory(fact1["text"], fact2["text"]):
                contradictions.append({
                    "fact1": fact1,
                    "fact2": fact2
                })
    
    return contradictions


def _are_contradictory(text1: str, text2: str) -> bool:
    """Check if two texts are contradictory."""
    
    # Simplified contradiction detection
    t1_lower = text1.lower()
    t2_lower = text2.lower()
    
    # Look for opposite statements about the same subject
    contradiction_patterns = [
        ("dead", "alive"),
        ("empty", "full"),
        ("open", "closed"),
        ("light", "dark"),
        ("safe", "dangerous")
    ]
    
    for word1, word2 in contradiction_patterns:
        if (word1 in t1_lower and word2 in t2_lower) or (word2 in t1_lower and word1 in t2_lower):
            # Check if they're talking about the same thing
            common_nouns = _find_common_nouns(t1_lower, t2_lower)
            if common_nouns:
                return True
    
    return False


def _find_common_nouns(text1: str, text2: str) -> List[str]:
    """Find common nouns between two texts."""
    
    # Extract potential nouns (simplified)
    nouns1 = re.findall(r'\b[a-z]+\b', text1)
    nouns2 = re.findall(r'\b[a-z]+\b', text2)
    
    common = set(nouns1) & set(nouns2)
    
    # Filter out common words
    common_words = {"the", "a", "an", "and", "or", "but", "you", "your", "are", "is", "was", "have", "has"}
    return [word for word in common if word not in common_words and len(word) > 3]


def _check_ending_plot_consistency(adventure: AdventureGame, story: StoryRequirements) -> List[CoherenceIssue]:
    """Check if endings are consistent with the plot."""
    
    issues = []
    
    plot_tone = _determine_plot_tone(story.plot)
    
    for ending_type, ending_text in adventure.endings.items():
        ending_tone = _determine_text_tone(ending_text)
        
        # Check if ending tone matches expected tone for ending type
        if ending_type == "success" and ending_tone in ["tragic", "dark"]:
            issues.append(CoherenceIssue(
                "INCONSISTENT_ENDING_TONE",
                f"Success ending has {ending_tone} tone, inconsistent with positive outcome",
                f"ENDING_{ending_type.upper()}",
                "medium"
            ))
        elif ending_type == "failure" and ending_tone in ["triumphant", "celebratory"]:
            issues.append(CoherenceIssue(
                "INCONSISTENT_ENDING_TONE",
                f"Failure ending has {ending_tone} tone, inconsistent with negative outcome",
                f"ENDING_{ending_type.upper()}",
                "medium"
            ))
    
    return issues


def _determine_plot_tone(plot_text: str) -> str:
    """Determine the overall tone of the plot."""
    
    plot_lower = plot_text.lower()
    
    if any(word in plot_lower for word in ["mystery", "investigation", "solve", "clues"]):
        return "mysterious"
    elif any(word in plot_lower for word in ["danger", "threat", "evil", "dark"]):
        return "threatening"
    elif any(word in plot_lower for word in ["adventure", "quest", "journey", "explore"]):
        return "adventurous"
    elif any(word in plot_lower for word in ["comedy", "humor", "funny", "witty"]):
        return "humorous"
    else:
        return "neutral"


def _determine_text_tone(text: str) -> str:
    """Determine the tone of a text passage."""
    
    text_lower = text.lower()
    
    positive_words = ["congratulations", "success", "triumph", "victory", "celebrate", "joy", "happy"]
    negative_words = ["failure", "defeat", "loss", "tragedy", "death", "disaster", "despair"]
    dark_words = ["dark", "evil", "sinister", "doom", "curse", "shadow"]
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    dark_count = sum(1 for word in dark_words if word in text_lower)
    
    if dark_count > 0:
        return "dark"
    elif positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


def _check_character_consistency(adventure: AdventureGame, character_data: Dict, character_id: str) -> List[CoherenceIssue]:
    """Check consistency of character behavior."""
    
    issues = []
    
    character_name = character_data.get("name", character_id)
    character_background = character_data.get("background", "")
    
    # Find all mentions of this character
    character_mentions = []
    
    for step_id, step in adventure.steps.items():
        if character_name.lower() in step.narrative.lower():
            character_mentions.append((step_id, step.narrative))
    
    if len(character_mentions) > 1:
        # Check for consistent characterization
        first_portrayal = character_mentions[0][1].lower()
        
        for step_id, mention in character_mentions[1:]:
            if _has_inconsistent_characterization(first_portrayal, mention.lower(), character_background):
                issues.append(CoherenceIssue(
                    "INCONSISTENT_CHARACTER",
                    f"Character {character_name} behaves inconsistently",
                    f"STEP_{step_id}",
                    "medium"
                ))
    
    return issues


def _has_inconsistent_characterization(first_text: str, second_text: str, background: str) -> bool:
    """Check if character portrayal is inconsistent."""
    
    # Simplified check - look for contradictory traits
    trait_opposites = [
        ("friendly", "hostile"),
        ("helpful", "unhelpful"),
        ("wise", "foolish"),
        ("brave", "cowardly"),
        ("honest", "deceptive")
    ]
    
    for trait1, trait2 in trait_opposites:
        if ((trait1 in first_text or trait1 in background.lower()) and trait2 in second_text) or \
           ((trait2 in first_text or trait2 in background.lower()) and trait1 in second_text):
            return True
    
    return False


def _check_character_development(adventure: AdventureGame, main_character: Dict) -> List[CoherenceIssue]:
    """Check for appropriate character development."""
    
    issues = []
    
    # For longer adventures, expect some character growth
    if len(adventure.steps) > 5:
        # Check if character changes or learns something
        first_step = list(adventure.steps.values())[0]
        last_steps = list(adventure.steps.values())[-2:]  # Last two steps
        
        first_narrative = first_step.narrative.lower()
        last_narratives = " ".join(step.narrative.lower() for step in last_steps)
        
        # Look for growth indicators
        growth_indicators = ["learned", "discovered", "realized", "understood", "changed", "grew"]
        
        if not any(indicator in last_narratives for indicator in growth_indicators):
            issues.append(CoherenceIssue(
                "LACK_OF_CHARACTER_DEVELOPMENT",
                "Main character shows no growth or development throughout the adventure",
                "CHARACTER_ARC",
                "low"
            ))
    
    return issues


def _check_narrative_tone(adventure: AdventureGame, author: AuthorPersona) -> List[CoherenceIssue]:
    """Check consistency of narrative tone."""
    
    issues = []
    
    expected_tone = _determine_author_tone(author)
    
    # Check each step's tone
    for step_id, step in adventure.steps.items():
        step_tone = _determine_text_tone(step.narrative)
        
        if _tones_are_inconsistent(expected_tone, step_tone):
            issues.append(CoherenceIssue(
                "TONE_INCONSISTENCY",
                f"Step tone ({step_tone}) inconsistent with author style ({expected_tone})",
                f"STEP_{step_id}",
                "medium"
            ))
    
    return issues


def _determine_author_tone(author: AuthorPersona) -> str:
    """Determine expected tone from author persona."""
    
    voice_tone = " ".join(author.voice_and_tone).lower()
    
    if "witty" in voice_tone or "humorous" in voice_tone:
        return "humorous"
    elif "serious" in voice_tone or "formal" in voice_tone:
        return "serious"
    elif "dark" in voice_tone or "grim" in voice_tone:
        return "dark"
    else:
        return "neutral"


def _tones_are_inconsistent(expected: str, actual: str) -> bool:
    """Check if tones are inconsistent."""
    
    inconsistent_pairs = [
        ("humorous", "dark"),
        ("serious", "comedic"),
        ("formal", "casual")
    ]
    
    return (expected, actual) in inconsistent_pairs or (actual, expected) in inconsistent_pairs


def _check_writing_style_consistency(adventure: AdventureGame, author: AuthorPersona) -> List[CoherenceIssue]:
    """Check consistency of writing style."""
    
    issues = []
    
    narrative_style = author.narrative_style
    expected_elements = set(narrative_style)
    
    # Check if narratives reflect the expected style
    for step_id, step in adventure.steps.items():
        narrative_text = step.narrative.lower()
        
        # Look for style indicators
        if "descriptive" in expected_elements and len(narrative_text) < 50:
            issues.append(CoherenceIssue(
                "STYLE_INCONSISTENCY",
                "Narrative too brief for descriptive style",
                f"STEP_{step_id}",
                "low"
            ))
        
        if "dialogue-heavy" in expected_elements and '"' not in step.narrative:
            issues.append(CoherenceIssue(
                "STYLE_INCONSISTENCY",
                "Missing dialogue in dialogue-heavy style",
                f"STEP_{step_id}",
                "low"
            ))
    
    return issues


def _check_narrative_pacing_impl(adventure: AdventureGame) -> List[CoherenceIssue]:
    """Check narrative pacing."""
    
    issues = []
    
    # Check for consistent pacing
    narrative_lengths = [(step_id, len(step.narrative)) for step_id, step in adventure.steps.items()]
    
    if len(narrative_lengths) > 1:
        avg_length = sum(length for _, length in narrative_lengths) / len(narrative_lengths)
        
        for step_id, length in narrative_lengths:
            if length < avg_length * 0.3:  # Much shorter than average
                issues.append(CoherenceIssue(
                    "PACING_ISSUE",
                    f"Step narrative much shorter than average ({length} vs {avg_length:.0f} chars)",
                    f"STEP_{step_id}",
                    "low"
                ))
            elif length > avg_length * 2.5:  # Much longer than average
                issues.append(CoherenceIssue(
                    "PACING_ISSUE",
                    f"Step narrative much longer than average ({length} vs {avg_length:.0f} chars)",
                    f"STEP_{step_id}",
                    "low"
                ))
    
    return issues


def _check_step_transitions(adventure: AdventureGame) -> List[CoherenceIssue]:
    """Check transitions between steps."""
    
    issues = []
    
    # Check choice-to-step transitions
    for step_id, step in adventure.steps.items():
        for choice in step.choices:
            if choice.target.startswith("STEP_"):
                target_step_id = choice.target.replace("STEP_", "")
                target_step = adventure.steps.get(target_step_id)
                
                if target_step:
                    if _has_poor_transition(choice.description, target_step.narrative):
                        issues.append(CoherenceIssue(
                            "POOR_TRANSITION",
                            f"Poor transition from choice '{choice.description}' to target step",
                            f"STEP_{step_id} -> STEP_{target_step_id}",
                            "medium"
                        ))
    
    return issues


def _has_poor_transition(choice_text: str, target_narrative: str) -> bool:
    """Check if transition from choice to target is poor."""
    
    # Simplified check - look for completely unrelated content
    choice_words = set(re.findall(r'\b\w+\b', choice_text.lower()))
    narrative_words = set(re.findall(r'\b\w+\b', target_narrative.lower()))
    
    # If there's very little word overlap, transition might be poor
    common_words = choice_words & narrative_words
    
    # Remove very common words
    very_common = {"the", "a", "an", "and", "or", "but", "you", "to", "in", "on", "at", "with"}
    meaningful_common = common_words - very_common
    
    # If fewer than 10% of words are in common, might be poor transition
    return len(meaningful_common) < max(1, len(choice_words) * 0.1)


def _check_choice_logic(adventure: AdventureGame) -> List[CoherenceIssue]:
    """Check logical consistency of choices and consequences."""
    
    issues = []
    
    for step_id, step in adventure.steps.items():
        for i, choice in enumerate(step.choices):
            # Check if choice makes sense in context
            if _choice_seems_illogical(choice.description, step.narrative):
                issues.append(CoherenceIssue(
                    "ILLOGICAL_CHOICE",
                    f"Choice '{choice.description}' seems illogical in context",
                    f"STEP_{step_id}.CHOICE_{i+1}",
                    "medium"
                ))
            
            # Check consequences logic
            for consequence in choice.consequences:
                if _consequence_seems_illogical(consequence, choice.description):
                    issues.append(CoherenceIssue(
                        "ILLOGICAL_CONSEQUENCE",
                        f"Consequence '{consequence}' doesn't match choice '{choice.description}'",
                        f"STEP_{step_id}.CHOICE_{i+1}",
                        "medium"
                    ))
    
    return issues


def _choice_seems_illogical(choice_text: str, context: str) -> bool:
    """Check if a choice seems illogical in its context."""
    
    # Simplified logic check
    choice_lower = choice_text.lower()
    context_lower = context.lower()
    
    # Check for obvious mismatches
    if "fight" in choice_lower and "peaceful" in context_lower:
        return True
    
    if "negotiate" in choice_lower and "dead" in context_lower:
        return True
    
    return False


def _consequence_seems_illogical(consequence: str, choice_text: str) -> bool:
    """Check if a consequence seems illogical for the choice."""
    
    # Simplified consequence logic check
    consequence_lower = consequence.lower()
    choice_lower = choice_text.lower()
    
    # Check for obvious mismatches
    if "health" in consequence_lower and "+" in consequence and "dangerous" not in choice_lower and "heal" not in choice_lower:
        return False  # Gaining health without healing action might be illogical
    
    return False


def _check_logical_impossibilities(adventure: AdventureGame) -> List[CoherenceIssue]:
    """Check for logically impossible situations."""
    
    issues = []
    
    for step_id, step in adventure.steps.items():
        narrative_lower = step.narrative.lower()
        
        # Check for impossible physics or situations
        impossible_patterns = [
            ("dead", "speak"),
            ("underwater", "fire"),
            ("invisible", "see yourself")
        ]
        
        for word1, word2 in impossible_patterns:
            if word1 in narrative_lower and word2 in narrative_lower:
                issues.append(CoherenceIssue(
                    "LOGICAL_IMPOSSIBILITY",
                    f"Impossible situation: {word1} and {word2} cannot coexist",
                    f"STEP_{step_id}",
                    "high"
                ))
    
    return issues


def _check_temporal_consistency(adventure: AdventureGame) -> List[CoherenceIssue]:
    """Check for temporal consistency issues."""
    
    issues = []
    
    # Check for time-related contradictions
    time_references = []
    
    for step_id, step in adventure.steps.items():
        narrative_lower = step.narrative.lower()
        
        # Look for time references
        time_words = ["morning", "afternoon", "evening", "night", "dawn", "dusk", "yesterday", "tomorrow"]
        
        for time_word in time_words:
            if time_word in narrative_lower:
                time_references.append((step_id, time_word))
    
    # Check for impossible time progressions
    if len(time_references) > 1:
        for i in range(len(time_references) - 1):
            current_step, current_time = time_references[i]
            next_step, next_time = time_references[i + 1]
            
            if _has_impossible_time_progression(current_time, next_time):
                issues.append(CoherenceIssue(
                    "TEMPORAL_INCONSISTENCY",
                    f"Impossible time progression: {current_time} to {next_time}",
                    f"STEP_{current_step} -> STEP_{next_step}",
                    "medium"
                ))
    
    return issues


def _has_impossible_time_progression(time1: str, time2: str) -> bool:
    """Check if time progression is impossible."""
    
    # Simple time order check
    time_order = ["dawn", "morning", "afternoon", "evening", "dusk", "night"]
    
    try:
        index1 = time_order.index(time1)
        index2 = time_order.index(time2)
        
        # If time goes backwards significantly, it might be inconsistent
        return index2 < index1 - 1
    except ValueError:
        return False


def _calculate_coherence_scores(
    plot_issues: List[CoherenceIssue],
    character_issues: List[CoherenceIssue],
    narrative_issues: List[CoherenceIssue],
    logic_issues: List[CoherenceIssue],
    adventure: AdventureGame
) -> Dict[str, float]:
    """Calculate various coherence scores."""
    
    # Count issues by severity
    all_issues = plot_issues + character_issues + narrative_issues + logic_issues
    
    critical_count = len([i for i in all_issues if i.severity == "critical"])
    high_count = len([i for i in all_issues if i.severity == "high"])
    medium_count = len([i for i in all_issues if i.severity == "medium"])
    low_count = len([i for i in all_issues if i.severity == "low"])
    
    # Calculate base score (start from 10, deduct for issues)
    base_score = 10.0
    
    # Deduct points based on severity
    base_score -= critical_count * 3.0
    base_score -= high_count * 2.0
    base_score -= medium_count * 1.0
    base_score -= low_count * 0.5
    
    consistency_score = max(0.0, base_score)
    
    # Readability score based on narrative quality
    readability_score = 8.0 - len(narrative_issues) * 0.5
    readability_score = max(0.0, min(10.0, readability_score))
    
    # Engagement score based on variety and flow
    engagement_score = 7.0
    if len(adventure.steps) > 5:
        engagement_score += 1.0  # Bonus for longer adventures
    if len(set(choice.target for step in adventure.steps.values() for choice in step.choices)) > 3:
        engagement_score += 1.0  # Bonus for variety
    
    engagement_score = max(0.0, min(10.0, engagement_score))
    
    # Overall score is weighted average
    overall_score = (consistency_score * 0.4 + readability_score * 0.3 + engagement_score * 0.3)
    
    return {
        "consistency": consistency_score,
        "readability": readability_score,
        "engagement": engagement_score,
        "overall": overall_score
    }


def _generate_coherence_recommendations(analysis: CoherenceAnalysis) -> List[str]:
    """Generate recommendations for improving coherence."""
    
    recommendations = []
    
    if analysis.plot_issues:
        recommendations.append("Address plot inconsistencies and missing elements")
    
    if analysis.character_issues:
        recommendations.append("Improve character consistency and development")
    
    if analysis.narrative_issues:
        recommendations.append("Enhance narrative flow and style consistency")
    
    if analysis.logic_issues:
        recommendations.append("Fix logical inconsistencies and impossible situations")
    
    if analysis.overall_coherence_score < 6.0:
        recommendations.append("Consider major revisions to improve overall coherence")
    elif analysis.overall_coherence_score < 8.0:
        recommendations.append("Minor improvements needed for better coherence")
    else:
        recommendations.append("Coherence is good, focus on polishing details")
    
    return recommendations


def _generate_coherence_report(analysis: CoherenceAnalysis, adventure: AdventureGame) -> str:
    """Generate a comprehensive coherence report."""
    
    lines = ["=== Coherence Analysis Report ===", ""]
    
    # Scores
    lines.append("COHERENCE SCORES:")
    lines.append(f"  Overall: {analysis.overall_coherence_score:.1f}/10")
    lines.append(f"  Consistency: {analysis.consistency_score:.1f}/10")
    lines.append(f"  Readability: {analysis.readability_score:.1f}/10")
    lines.append(f"  Engagement: {analysis.engagement_score:.1f}/10")
    lines.append("")
    
    # Issue Summary
    total_issues = len(analysis.plot_issues) + len(analysis.character_issues) + \
                  len(analysis.narrative_issues) + len(analysis.logic_issues)
    
    lines.append(f"ISSUES FOUND: {total_issues}")
    lines.append(f"  Plot Issues: {len(analysis.plot_issues)}")
    lines.append(f"  Character Issues: {len(analysis.character_issues)}")
    lines.append(f"  Narrative Issues: {len(analysis.narrative_issues)}")
    lines.append(f"  Logic Issues: {len(analysis.logic_issues)}")
    lines.append("")
    
    # Detailed Issues
    for issue_type, issues in [
        ("PLOT ISSUES", analysis.plot_issues),
        ("CHARACTER ISSUES", analysis.character_issues),
        ("NARRATIVE ISSUES", analysis.narrative_issues),
        ("LOGIC ISSUES", analysis.logic_issues)
    ]:
        if issues:
            lines.append(f"{issue_type}:")
            for issue in issues:
                lines.append(f"  • {issue}")
            lines.append("")
    
    # Adventure Statistics
    lines.append("ADVENTURE STATISTICS:")
    lines.append(f"  Total Steps: {len(adventure.steps)}")
    lines.append(f"  Total Choices: {sum(len(step.choices) for step in adventure.steps.values())}")
    lines.append(f"  Endings: {len(adventure.endings)}")
    lines.append("")
    
    return "\n".join(lines)