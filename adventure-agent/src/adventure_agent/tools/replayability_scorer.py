"""
Replayability Scorer Tool for the Adventure Generation Agent.

This tool analyzes variation between different playthroughs, calculates branching
complexity and uniqueness, and generates comprehensive replayability metrics.
"""

import itertools
from typing import Dict, List, Set, Tuple

from pydantic_ai import Agent, RunContext

from ..models import AdventureGame, ToolResult


class PlaythroughPath:
    """Represents a complete playthrough path."""
    
    def __init__(self, steps: List[str], choices_made: List[str], ending: str):
        self.steps = steps
        self.choices_made = choices_made
        self.ending = ending
        self.length = len(steps)
        self.unique_content = set(steps)
        
    def similarity_to(self, other: 'PlaythroughPath') -> float:
        """Calculate similarity to another playthrough (0-1 scale)."""
        if not self.steps and not other.steps:
            return 1.0
        
        common_steps = len(self.unique_content & other.unique_content)
        total_unique_steps = len(self.unique_content | other.unique_content)
        
        step_similarity = common_steps / total_unique_steps if total_unique_steps > 0 else 0.0
        
        # Consider ending similarity
        ending_similarity = 1.0 if self.ending == other.ending else 0.0
        
        # Weighted combination
        return step_similarity * 0.7 + ending_similarity * 0.3


class ReplayabilityAnalysis:
    """Analysis results for replayability scoring."""
    
    def __init__(self):
        self.total_possible_paths: int = 0
        self.unique_playthroughs: List[PlaythroughPath] = []
        self.path_diversity_score: float = 0.0
        self.content_variation_score: float = 0.0
        self.ending_variety_score: float = 0.0
        self.branching_complexity: float = 0.0
        self.replay_value_score: float = 0.0
        self.overall_replayability: float = 0.0


class ReplayabilityDependencies:
    """Dependencies for replayability analysis."""
    
    def __init__(self):
        self.analysis = ReplayabilityAnalysis()
        self.max_paths_to_analyze = 100  # Limit for performance
        self.min_replay_threshold = 3  # Minimum unique paths for good replayability


def create_replayability_agent() -> Agent[ReplayabilityDependencies, ReplayabilityAnalysis]:
    """Create replayability analysis agent."""
    return Agent[ReplayabilityDependencies, ReplayabilityAnalysis](
        'gemini-1.5-flash',
        deps_type=ReplayabilityDependencies,
        output_type=ReplayabilityAnalysis,
        system_prompt=(
            "You are a replayability expert. Analyze adventure paths for variety, "
            "uniqueness, and replay value. Ensure players have reasons to play "
            "through the adventure multiple times with different experiences."
        ),
    )


async def analyze_replayability(
    ctx: RunContext[ReplayabilityDependencies],
    adventure: AdventureGame
) -> ReplayabilityAnalysis:
    """
    Analyze the replayability of the adventure.
    
    Args:
        ctx: Agent context with dependencies
        adventure: Adventure to analyze
        
    Returns:
        ReplayabilityAnalysis containing replayability metrics
    """
    analysis = ctx.deps.analysis
    
    # Generate all possible playthroughs
    all_paths = _generate_all_playthroughs(adventure, ctx.deps.max_paths_to_analyze)
    analysis.unique_playthroughs = all_paths
    analysis.total_possible_paths = len(all_paths)
    
    # Calculate diversity metrics
    analysis.path_diversity_score = _calculate_path_diversity(all_paths)
    analysis.content_variation_score = _calculate_content_variation(all_paths, adventure)
    analysis.ending_variety_score = _calculate_ending_variety(all_paths)
    analysis.branching_complexity = _calculate_branching_complexity(adventure)
    analysis.replay_value_score = _calculate_replay_value(all_paths, adventure)
    analysis.overall_replayability = _calculate_overall_replayability(analysis)
    
    return analysis


async def score_replayability(adventure: AdventureGame) -> ToolResult:
    """
    Main replayability scoring function.
    
    Args:
        adventure: Adventure to score
        
    Returns:
        ToolResult with replayability analysis and recommendations
    """
    try:
        # Set up dependencies
        deps = ReplayabilityDependencies()
        
        # Perform comprehensive replayability analysis
        analysis = await _analyze_replayability_impl(adventure, deps)
        
        # Generate insights and recommendations
        insights = _generate_replayability_insights(analysis, adventure)
        recommendations = _generate_replayability_recommendations(analysis)
        
        # Generate detailed report
        report = _generate_replayability_report(analysis, adventure)
        
        # Determine success based on replayability score
        is_highly_replayable = analysis.overall_replayability >= 7.0
        
        return ToolResult(
            success=True,
            data={
                "analysis": analysis,
                "insights": insights,
                "recommendations": recommendations,
                "report": report,
                "metrics": {
                    "total_paths": analysis.total_possible_paths,
                    "path_diversity": analysis.path_diversity_score,
                    "content_variation": analysis.content_variation_score,
                    "ending_variety": analysis.ending_variety_score,
                    "branching_complexity": analysis.branching_complexity,
                    "replay_value": analysis.replay_value_score,
                    "overall_replayability": analysis.overall_replayability,
                    "is_highly_replayable": is_highly_replayable
                }
            },
            message=f"Replayability analysis: {analysis.overall_replayability:.1f}/10 overall score, {analysis.total_possible_paths} unique paths",
            metadata={
                "overall_score": analysis.overall_replayability,
                "total_paths": analysis.total_possible_paths,
                "highly_replayable": is_highly_replayable,
                "path_diversity": analysis.path_diversity_score,
                "ending_variety": analysis.ending_variety_score
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Replayability scoring failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


def _generate_all_playthroughs(adventure: AdventureGame, max_paths: int) -> List[PlaythroughPath]:
    """Generate all possible playthrough paths."""
    
    if "1" not in adventure.steps:
        return []
    
    all_paths = []
    
    def explore_path(current_step: str, path_steps: List[str], choices_made: List[str], visited: Set[str]):
        # Prevent infinite loops and overly long paths
        if len(path_steps) > 20 or current_step in visited or len(all_paths) >= max_paths:
            return
        
        new_visited = visited | {current_step}
        new_path_steps = path_steps + [current_step]
        
        if current_step not in adventure.steps:
            # This is an ending
            if current_step.startswith("ENDING_"):
                playthrough = PlaythroughPath(new_path_steps, choices_made, current_step)
                all_paths.append(playthrough)
            return
        
        step = adventure.steps[current_step]
        
        # Explore each choice
        for choice in step.choices:
            new_choices_made = choices_made + [f"{current_step}:{choice.label.value}"]
            
            if choice.target.startswith("STEP_"):
                target_step = choice.target.replace("STEP_", "")
                explore_path(target_step, new_path_steps, new_choices_made, new_visited)
            elif choice.target.startswith("ENDING_"):
                final_path = new_path_steps + [choice.target]
                playthrough = PlaythroughPath(final_path, new_choices_made, choice.target)
                all_paths.append(playthrough)
    
    explore_path("1", [], [], set())
    return all_paths


def _calculate_path_diversity(paths: List[PlaythroughPath]) -> float:
    """Calculate diversity between different playthrough paths (0-10 scale)."""
    
    if len(paths) < 2:
        return 0.0 if len(paths) == 0 else 5.0
    
    total_similarity = 0.0
    comparisons = 0
    
    # Compare all pairs of paths
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            similarity = paths[i].similarity_to(paths[j])
            total_similarity += similarity
            comparisons += 1
    
    if comparisons == 0:
        return 5.0
    
    avg_similarity = total_similarity / comparisons
    
    # Convert to diversity (lower similarity = higher diversity)
    diversity_score = (1.0 - avg_similarity) * 10
    
    return max(0.0, min(10.0, diversity_score))


def _calculate_content_variation(paths: List[PlaythroughPath], adventure: AdventureGame) -> float:
    """Calculate how much content variation exists across playthroughs (0-10 scale)."""
    
    if not paths:
        return 0.0
    
    total_steps = len(adventure.steps)
    if total_steps == 0:
        return 0.0
    
    # Calculate what percentage of content each path uses
    content_usage_ratios = []
    
    for path in paths:
        # Count unique steps seen in this path (excluding endings)
        unique_steps = set(step for step in path.steps if not step.startswith("ENDING_"))
        usage_ratio = len(unique_steps) / total_steps
        content_usage_ratios.append(usage_ratio)
    
    # Calculate variation in content usage
    if len(content_usage_ratios) < 2:
        return content_usage_ratios[0] * 10 if content_usage_ratios else 0.0
    
    min_usage = min(content_usage_ratios)
    max_usage = max(content_usage_ratios)
    avg_usage = sum(content_usage_ratios) / len(content_usage_ratios)
    
    # Variation score based on range and average
    variation_range = max_usage - min_usage
    variation_score = (variation_range * 5) + (avg_usage * 5)
    
    return max(0.0, min(10.0, variation_score))


def _calculate_ending_variety(paths: List[PlaythroughPath]) -> float:
    """Calculate variety in ending distribution (0-10 scale)."""
    
    if not paths:
        return 0.0
    
    # Count endings
    ending_counts = {}
    for path in paths:
        ending_counts[path.ending] = ending_counts.get(path.ending, 0) + 1
    
    total_paths = len(paths)
    unique_endings = len(ending_counts)
    
    if unique_endings == 0:
        return 0.0
    
    # Base score for having multiple endings
    variety_score = min(5.0, unique_endings * 2.0)
    
    # Bonus for balanced distribution
    if unique_endings > 1:
        # Calculate distribution balance
        proportions = [count / total_paths for count in ending_counts.values()]
        
        # Ideal is even distribution - calculate deviation from even
        ideal_proportion = 1.0 / unique_endings
        deviation = sum(abs(prop - ideal_proportion) for prop in proportions)
        balance_score = max(0.0, 5.0 - (deviation * 10))
        
        variety_score += balance_score
    
    return max(0.0, min(10.0, variety_score))


def _calculate_branching_complexity(adventure: AdventureGame) -> float:
    """Calculate complexity of branching structure (0-10 scale)."""
    
    if not adventure.steps:
        return 0.0
    
    total_choices = sum(len(step.choices) for step in adventure.steps.values())
    total_steps = len(adventure.steps)
    
    # Average choices per step
    avg_choices = total_choices / total_steps if total_steps > 0 else 0
    
    # Base complexity from choice count
    complexity_score = min(5.0, avg_choices * 2.0)
    
    # Bonus for variety in choice counts
    choice_counts = [len(step.choices) for step in adventure.steps.values()]
    if len(choice_counts) > 1:
        choice_variety = max(choice_counts) - min(choice_counts)
        complexity_score += min(2.0, choice_variety * 0.5)
    
    # Bonus for having conditional choices or consequences
    conditional_bonus = 0.0
    for step in adventure.steps.values():
        for choice in step.choices:
            if choice.conditions:
                conditional_bonus += 0.1
            if choice.consequences:
                conditional_bonus += 0.1
    
    complexity_score += min(3.0, conditional_bonus)
    
    return max(0.0, min(10.0, complexity_score))


def _calculate_replay_value(paths: List[PlaythroughPath], adventure: AdventureGame) -> float:
    """Calculate overall replay value (0-10 scale)."""
    
    if not paths:
        return 0.0
    
    replay_score = 0.0
    
    # Factor 1: Number of distinct paths
    path_count_score = min(4.0, len(paths) * 0.5)
    replay_score += path_count_score
    
    # Factor 2: Length variation
    if len(paths) > 1:
        path_lengths = [path.length for path in paths]
        min_length = min(path_lengths)
        max_length = max(path_lengths)
        length_variation = (max_length - min_length) / max(1, max_length)
        replay_score += length_variation * 2.0
    
    # Factor 3: Unique content per playthrough
    if paths:
        avg_unique_steps = sum(len(path.unique_content) for path in paths) / len(paths)
        total_steps = len(adventure.steps)
        uniqueness_ratio = avg_unique_steps / max(1, total_steps)
        replay_score += uniqueness_ratio * 2.0
    
    # Factor 4: Ending distribution
    ending_variety = len(set(path.ending for path in paths))
    replay_score += min(2.0, ending_variety * 0.5)
    
    return max(0.0, min(10.0, replay_score))


def _calculate_overall_replayability(analysis: ReplayabilityAnalysis) -> float:
    """Calculate overall replayability score (0-10 scale)."""
    
    # Weighted combination of factors
    overall_score = (
        analysis.path_diversity_score * 0.25 +
        analysis.content_variation_score * 0.20 +
        analysis.ending_variety_score * 0.20 +
        analysis.branching_complexity * 0.15 +
        analysis.replay_value_score * 0.20
    )
    
    return max(0.0, min(10.0, overall_score))


async def _analyze_replayability_impl(adventure: AdventureGame, deps: ReplayabilityDependencies) -> ReplayabilityAnalysis:
    """Implementation of replayability analysis."""
    
    analysis = ReplayabilityAnalysis()
    
    # Generate all possible playthroughs
    all_paths = _generate_all_playthroughs(adventure, deps.max_paths_to_analyze)
    analysis.unique_playthroughs = all_paths
    analysis.total_possible_paths = len(all_paths)
    
    # Calculate all metrics
    analysis.path_diversity_score = _calculate_path_diversity(all_paths)
    analysis.content_variation_score = _calculate_content_variation(all_paths, adventure)
    analysis.ending_variety_score = _calculate_ending_variety(all_paths)
    analysis.branching_complexity = _calculate_branching_complexity(adventure)
    analysis.replay_value_score = _calculate_replay_value(all_paths, adventure)
    analysis.overall_replayability = _calculate_overall_replayability(analysis)
    
    return analysis


def _generate_replayability_insights(analysis: ReplayabilityAnalysis, adventure: AdventureGame) -> List[str]:
    """Generate insights about replayability."""
    
    insights = []
    
    # Path analysis
    if analysis.total_possible_paths == 1:
        insights.append("Linear story with no branching - limited replayability")
    elif analysis.total_possible_paths < 3:
        insights.append("Few unique paths available - consider adding more choices")
    elif analysis.total_possible_paths > 20:
        insights.append("High path variety provides excellent replayability")
    else:
        insights.append(f"Moderate path variety with {analysis.total_possible_paths} unique playthroughs")
    
    # Diversity analysis
    if analysis.path_diversity_score > 8.0:
        insights.append("Paths are highly diverse - each playthrough feels unique")
    elif analysis.path_diversity_score < 4.0:
        insights.append("Paths are too similar - consider varying story content more")
    
    # Content variation
    if analysis.content_variation_score > 7.0:
        insights.append("Good content variation - players see different story elements")
    elif analysis.content_variation_score < 4.0:
        insights.append("Low content variation - most paths use similar content")
    
    # Ending variety
    if analysis.ending_variety_score > 7.0:
        insights.append("Excellent ending variety encourages multiple playthroughs")
    elif analysis.ending_variety_score < 4.0:
        insights.append("Limited ending variety - consider adding more endings")
    
    # Branching complexity
    if analysis.branching_complexity > 7.0:
        insights.append("Complex branching structure provides rich decision-making")
    elif analysis.branching_complexity < 4.0:
        insights.append("Simple branching - consider adding more choice complexity")
    
    # Overall assessment
    if analysis.overall_replayability >= 8.0:
        insights.append("High replayability - adventure strongly encourages multiple playthroughs")
    elif analysis.overall_replayability >= 6.0:
        insights.append("Moderate replayability - some incentive for replaying")
    else:
        insights.append("Low replayability - limited reasons to replay the adventure")
    
    return insights


def _generate_replayability_recommendations(analysis: ReplayabilityAnalysis) -> List[str]:
    """Generate recommendations for improving replayability."""
    
    recommendations = []
    
    if analysis.overall_replayability < 6.0:
        recommendations.append("Consider major structural changes to improve replayability")
    
    if analysis.path_diversity_score < 5.0:
        recommendations.append("Add more branching points to create diverse story paths")
    
    if analysis.content_variation_score < 5.0:
        recommendations.append("Create paths that explore different content areas")
    
    if analysis.ending_variety_score < 5.0:
        recommendations.append("Add more endings or balance existing ending distribution")
    
    if analysis.branching_complexity < 5.0:
        recommendations.append("Increase choice complexity with conditions and consequences")
    
    if analysis.total_possible_paths < 3:
        recommendations.append("Add more choice branches to create additional unique paths")
    
    if analysis.replay_value_score < 5.0:
        recommendations.append("Add incentives for replaying (hidden content, achievements, etc.)")
    
    # Positive reinforcement
    if analysis.overall_replayability >= 8.0:
        recommendations.append("Excellent replayability - maintain this quality in future content")
    
    return recommendations


def _generate_replayability_report(analysis: ReplayabilityAnalysis, adventure: AdventureGame) -> str:
    """Generate a comprehensive replayability report."""
    
    lines = ["=== Replayability Analysis Report ===", ""]
    
    # Overall Score
    lines.append(f"OVERALL REPLAYABILITY: {analysis.overall_replayability:.1f}/10")
    
    if analysis.overall_replayability >= 8.0:
        lines.append("🌟 HIGHLY REPLAYABLE")
    elif analysis.overall_replayability >= 6.0:
        lines.append("✅ MODERATELY REPLAYABLE")
    elif analysis.overall_replayability >= 4.0:
        lines.append("⚠️ LIMITED REPLAYABILITY")
    else:
        lines.append("❌ LOW REPLAYABILITY")
    
    lines.append("")
    
    # Detailed Scores
    lines.append("DETAILED SCORES:")
    lines.append(f"  Path Diversity: {analysis.path_diversity_score:.1f}/10")
    lines.append(f"  Content Variation: {analysis.content_variation_score:.1f}/10")
    lines.append(f"  Ending Variety: {analysis.ending_variety_score:.1f}/10")
    lines.append(f"  Branching Complexity: {analysis.branching_complexity:.1f}/10")
    lines.append(f"  Replay Value: {analysis.replay_value_score:.1f}/10")
    lines.append("")
    
    # Path Statistics
    lines.append("PATH STATISTICS:")
    lines.append(f"  Total Unique Paths: {analysis.total_possible_paths}")
    
    if analysis.unique_playthroughs:
        path_lengths = [path.length for path in analysis.unique_playthroughs]
        lines.append(f"  Average Path Length: {sum(path_lengths) / len(path_lengths):.1f} steps")
        lines.append(f"  Shortest Path: {min(path_lengths)} steps")
        lines.append(f"  Longest Path: {max(path_lengths)} steps")
        
        # Ending distribution
        ending_counts = {}
        for path in analysis.unique_playthroughs:
            ending_counts[path.ending] = ending_counts.get(path.ending, 0) + 1
        
        lines.append("")
        lines.append("ENDING DISTRIBUTION:")
        total_paths = len(analysis.unique_playthroughs)
        for ending, count in sorted(ending_counts.items()):
            percentage = (count / total_paths * 100) if total_paths > 0 else 0
            lines.append(f"  {ending}: {count} paths ({percentage:.1f}%)")
    
    lines.append("")
    
    # Adventure Structure
    lines.append("ADVENTURE STRUCTURE:")
    lines.append(f"  Total Steps: {len(adventure.steps)}")
    lines.append(f"  Total Endings: {len(adventure.endings)}")
    
    if adventure.steps:
        total_choices = sum(len(step.choices) for step in adventure.steps.values())
        avg_choices = total_choices / len(adventure.steps)
        lines.append(f"  Total Choices: {total_choices}")
        lines.append(f"  Average Choices per Step: {avg_choices:.1f}")
    
    lines.append("")
    
    # Recommendations
    lines.append("KEY RECOMMENDATIONS:")
    
    if analysis.overall_replayability < 4.0:
        lines.append("  🚨 Urgent: Major replayability improvements needed")
        lines.append("    - Add multiple branching paths")
        lines.append("    - Create diverse endings")
        lines.append("    - Vary content across playthroughs")
    elif analysis.overall_replayability < 6.0:
        lines.append("  ⚠️ Moderate improvements recommended:")
        if analysis.path_diversity_score < 5.0:
            lines.append("    - Increase path diversity")
        if analysis.ending_variety_score < 5.0:
            lines.append("    - Add more ending variety")
        if analysis.branching_complexity < 5.0:
            lines.append("    - Increase choice complexity")
    elif analysis.overall_replayability < 8.0:
        lines.append("  ✨ Minor improvements for excellence:")
        lines.append("    - Polish existing branches")
        lines.append("    - Add hidden content for discovery")
        lines.append("    - Balance path lengths")
    else:
        lines.append("  🎉 Excellent replayability achieved!")
        lines.append("    - Maintain current quality")
        lines.append("    - Consider adding seasonal content")
    
    return "\n".join(lines)


async def compare_playthroughs(adventure: AdventureGame) -> Dict[str, List[str]]:
    """
    Compare different playthroughs to highlight differences.
    
    Args:
        adventure: Adventure to analyze
        
    Returns:
        Dictionary mapping playthrough descriptions to step sequences
    """
    deps = ReplayabilityDependencies()
    deps.max_paths_to_analyze = 10  # Limit for comparison
    
    paths = _generate_all_playthroughs(adventure, deps.max_paths_to_analyze)
    
    comparison = {}
    
    for i, path in enumerate(paths[:5]):  # Compare first 5 paths
        path_description = f"Path {i+1} (to {path.ending})"
        step_sequence = []
        
        for step in path.steps:
            if step.startswith("ENDING_"):
                step_sequence.append(f"→ {step}")
            else:
                step_sequence.append(f"Step {step}")
        
        comparison[path_description] = step_sequence
    
    return comparison


async def find_replay_incentives(adventure: AdventureGame) -> List[str]:
    """
    Identify potential replay incentives in the adventure.
    
    Args:
        adventure: Adventure to analyze
        
    Returns:
        List of identified replay incentives
    """
    incentives = []
    
    # Check for multiple endings
    if len(adventure.endings) > 1:
        incentives.append(f"Multiple endings ({len(adventure.endings)}) encourage replaying for different outcomes")
    
    # Check for choice consequences
    consequence_count = sum(
        len(choice.consequences) 
        for step in adventure.steps.values() 
        for choice in step.choices
        if choice.consequences
    )
    
    if consequence_count > 0:
        incentives.append(f"Choice consequences ({consequence_count} total) create different experiences")
    
    # Check for conditional content
    condition_count = sum(
        len(choice.conditions)
        for step in adventure.steps.values()
        for choice in step.choices
        if choice.conditions
    )
    
    if condition_count > 0:
        incentives.append(f"Conditional choices ({condition_count} total) unlock different paths")
    
    # Check for inventory/stats usage
    if adventure.inventory or adventure.stats:
        incentives.append("Character progression and inventory provide gameplay variety")
    
    # Check for branching complexity
    deps = ReplayabilityDependencies()
    analysis = await _analyze_replayability_impl(adventure, deps)
    
    if analysis.total_possible_paths > 5:
        incentives.append(f"High path variety ({analysis.total_possible_paths} unique paths) rewards exploration")
    
    if not incentives:
        incentives.append("Limited replay incentives found - consider adding multiple paths and endings")
    
    return incentives