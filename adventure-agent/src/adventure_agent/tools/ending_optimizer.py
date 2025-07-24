"""
Ending Optimizer Tool for the Adventure Generation Agent.

This tool balances the distribution of success/failure/neutral outcomes,
analyzes player choice consequences, and ensures meaningful differentiation between endings.
"""

from typing import Dict, List, Set, Tuple

from pydantic_ai import Agent, RunContext

from ..models import AdventureGame, Choice, EndingType, ToolResult


class EndingAnalysis:
    """Analysis results for ending optimization."""
    
    def __init__(self):
        self.ending_distribution: Dict[str, int] = {}
        self.ending_accessibility: Dict[str, float] = {}
        self.choice_to_ending_paths: Dict[str, List[str]] = {}
        self.ending_quality_scores: Dict[str, float] = {}
        self.balance_score: float = 0.0
        self.accessibility_score: float = 0.0
        self.differentiation_score: float = 0.0
        self.overall_score: float = 0.0


class OptimizationSuggestion:
    """Suggestion for improving ending balance."""
    
    def __init__(self, suggestion_type: str, description: str, location: str, priority: str = "medium"):
        self.suggestion_type = suggestion_type
        self.description = description
        self.location = location
        self.priority = priority  # low, medium, high, critical
    
    def __str__(self):
        return f"[{self.priority.upper()}] {self.suggestion_type}: {self.description} ({self.location})"


class EndingDependencies:
    """Dependencies for ending optimization."""
    
    def __init__(self):
        self.analysis = EndingAnalysis()
        self.target_success_rate = 0.4  # 40% of paths should lead to success
        self.target_failure_rate = 0.35  # 35% to failure
        self.target_neutral_rate = 0.25  # 25% to neutral
        self.min_paths_per_ending = 1


def create_ending_agent() -> Agent[EndingDependencies, EndingAnalysis]:
    """Create ending optimization agent."""
    return Agent[EndingDependencies, EndingAnalysis](
        'gemini-1.5-flash',
        deps_type=EndingDependencies,
        output_type=EndingAnalysis,
        system_prompt=(
            "You are an ending balance expert. Analyze ending distribution, accessibility, "
            "and quality to ensure players have meaningful choices that lead to well-balanced "
            "outcomes with appropriate difficulty and satisfaction."
        ),
    )


async def analyze_ending_balance(
    ctx: RunContext[EndingDependencies],
    adventure: AdventureGame
) -> EndingAnalysis:
    """
    Analyze the balance of endings in the adventure.
    
    Args:
        ctx: Agent context with dependencies
        adventure: Adventure to analyze
        
    Returns:
        EndingAnalysis containing balance analysis
    """
    analysis = ctx.deps.analysis
    
    # Calculate ending distribution
    analysis.ending_distribution = _calculate_ending_distribution(adventure)
    
    # Calculate accessibility scores
    analysis.ending_accessibility = _calculate_ending_accessibility(adventure)
    
    # Map choices to ending paths
    analysis.choice_to_ending_paths = _map_choice_to_ending_paths(adventure)
    
    # Score ending quality
    analysis.ending_quality_scores = _score_ending_quality(adventure)
    
    # Calculate overall scores
    analysis.balance_score = _calculate_balance_score(analysis.ending_distribution, ctx.deps)
    analysis.accessibility_score = _calculate_accessibility_score(analysis.ending_accessibility)
    analysis.differentiation_score = _calculate_differentiation_score(adventure)
    analysis.overall_score = _calculate_overall_ending_score(analysis)
    
    return analysis


async def optimize_endings(adventure: AdventureGame) -> ToolResult:
    """
    Main ending optimization function.
    
    Args:
        adventure: Adventure to optimize
        
    Returns:
        ToolResult with optimized adventure and analysis
    """
    try:
        # Set up dependencies
        deps = EndingDependencies()
        
        # Analyze current ending balance
        analysis = await _analyze_ending_balance_impl(adventure, deps)
        
        # Generate optimization suggestions
        suggestions = await _generate_optimization_suggestions(adventure, analysis, deps)
        
        # Apply optimizations
        optimized_adventure = await _apply_optimizations(adventure, suggestions)
        
        # Re-analyze to get final stats
        final_analysis = await _analyze_ending_balance_impl(optimized_adventure, deps)
        
        # Generate improvement report
        improvements = _generate_improvement_report(analysis, final_analysis)
        
        return ToolResult(
            success=True,
            data={
                "optimized_adventure": optimized_adventure,
                "original_analysis": analysis,
                "final_analysis": final_analysis,
                "suggestions": suggestions,
                "improvements": improvements
            },
            message=f"Ending optimization: {final_analysis.overall_score:.1f}/10 overall score, {len(suggestions)} suggestions applied",
            metadata={
                "overall_score": final_analysis.overall_score,
                "balance_score": final_analysis.balance_score,
                "accessibility_score": final_analysis.accessibility_score,
                "differentiation_score": final_analysis.differentiation_score,
                "suggestions_count": len(suggestions)
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Ending optimization failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


def _calculate_ending_distribution(adventure: AdventureGame) -> Dict[str, int]:
    """Calculate how many paths lead to each ending."""
    
    distribution = {}
    
    # Build a graph of all possible paths
    paths = _find_all_paths_to_endings(adventure, "1", [])
    
    # Count paths to each ending
    for path in paths:
        ending = path[-1]  # Last element is the ending
        distribution[ending] = distribution.get(ending, 0) + 1
    
    return distribution


def _find_all_paths_to_endings(adventure: AdventureGame, current_step: str, current_path: List[str]) -> List[List[str]]:
    """Find all possible paths from a step to endings."""
    
    # Prevent infinite loops
    if len(current_path) > 20 or current_step in current_path:
        return []
    
    new_path = current_path + [current_step]
    
    if current_step not in adventure.steps:
        # This is an ending
        if current_step.startswith("ENDING_"):
            return [new_path]
        return []
    
    step = adventure.steps[current_step]
    all_paths = []
    
    for choice in step.choices:
        if choice.target.startswith("STEP_"):
            target_step = choice.target.replace("STEP_", "")
            paths = _find_all_paths_to_endings(adventure, target_step, new_path)
            all_paths.extend(paths)
        elif choice.target.startswith("ENDING_"):
            ending_path = new_path + [choice.target]
            all_paths.append(ending_path)
    
    return all_paths


def _calculate_ending_accessibility(adventure: AdventureGame) -> Dict[str, float]:
    """Calculate how accessible each ending is (0-1 scale)."""
    
    accessibility = {}
    
    # For each ending, calculate what percentage of choices lead to it
    total_choices = sum(len(step.choices) for step in adventure.steps.values())
    
    if total_choices == 0:
        return accessibility
    
    for ending_key in adventure.endings.keys():
        ending_target = f"ENDING_{ending_key.upper()}"
        
        # Count direct choices leading to this ending
        direct_choices = 0
        for step in adventure.steps.values():
            for choice in step.choices:
                if choice.target == ending_target:
                    direct_choices += 1
        
        # Calculate paths through other steps
        paths_to_ending = _find_all_paths_to_endings(adventure, "1", [])
        paths_to_this_ending = [path for path in paths_to_ending if path[-1] == ending_target]
        
        # Accessibility is based on number of paths and average path length
        if paths_to_this_ending:
            avg_path_length = sum(len(path) for path in paths_to_this_ending) / len(paths_to_this_ending)
            # Shorter paths are more accessible
            accessibility_score = len(paths_to_this_ending) / max(1, avg_path_length - 1)
            accessibility[ending_key] = min(1.0, accessibility_score / 3.0)  # Normalize
        else:
            accessibility[ending_key] = 0.0
    
    return accessibility


def _map_choice_to_ending_paths(adventure: AdventureGame) -> Dict[str, List[str]]:
    """Map each choice to the endings it can lead to."""
    
    choice_mapping = {}
    
    for step_id, step in adventure.steps.items():
        for i, choice in enumerate(step.choices):
            choice_key = f"STEP_{step_id}.CHOICE_{i+1}"
            
            if choice.target.startswith("ENDING_"):
                # Direct ending
                choice_mapping[choice_key] = [choice.target]
            elif choice.target.startswith("STEP_"):
                # Find all endings reachable from target step
                target_step = choice.target.replace("STEP_", "")
                paths = _find_all_paths_to_endings(adventure, target_step, [])
                endings = list(set(path[-1] for path in paths if path[-1].startswith("ENDING_")))
                choice_mapping[choice_key] = endings
            else:
                choice_mapping[choice_key] = []
    
    return choice_mapping


def _score_ending_quality(adventure: AdventureGame) -> Dict[str, float]:
    """Score the quality of each ending (0-10 scale)."""
    
    scores = {}
    
    for ending_key, ending_text in adventure.endings.items():
        score = 5.0  # Base score
        
        # Length scoring
        text_length = len(ending_text.strip())
        if text_length < 20:
            score -= 2.0  # Too short
        elif text_length > 200:
            score += 1.0  # Good detail
        elif text_length > 50:
            score += 0.5  # Adequate detail
        
        # Content quality scoring
        ending_lower = ending_text.lower()
        
        # Positive indicators
        if any(word in ending_lower for word in ["congratulations", "victory", "success", "triumph"]):
            score += 1.0
        
        if any(word in ending_lower for word in ["learned", "grown", "discovered", "achieved"]):
            score += 0.5
        
        # Negative indicators for poor quality
        if ending_text.strip().endswith("...") or ending_text.strip().endswith("."):
            pass  # Proper ending
        else:
            score -= 0.5  # Doesn't end properly
        
        # Emotional resonance
        if any(word in ending_lower for word in ["feel", "emotion", "heart", "proud", "satisfied"]):
            score += 0.5
        
        # Appropriateness for ending type
        if ending_key == "success":
            if any(word in ending_lower for word in ["failure", "defeat", "loss"]):
                score -= 1.0  # Inappropriate tone
        elif ending_key == "failure":
            if any(word in ending_lower for word in ["success", "victory", "triumph"]):
                score -= 1.0  # Inappropriate tone
        
        scores[ending_key] = max(0.0, min(10.0, score))
    
    return scores


def _calculate_balance_score(distribution: Dict[str, int], deps: EndingDependencies) -> float:
    """Calculate how well-balanced the ending distribution is."""
    
    if not distribution:
        return 0.0
    
    total_paths = sum(distribution.values())
    if total_paths == 0:
        return 0.0
    
    # Calculate actual ratios
    success_ratio = distribution.get("ENDING_SUCCESS", 0) / total_paths
    failure_ratio = distribution.get("ENDING_FAILURE", 0) / total_paths
    neutral_ratio = distribution.get("ENDING_NEUTRAL", 0) / total_paths
    
    # Calculate deviations from target ratios
    success_deviation = abs(success_ratio - deps.target_success_rate)
    failure_deviation = abs(failure_ratio - deps.target_failure_rate)
    neutral_deviation = abs(neutral_ratio - deps.target_neutral_rate)
    
    # Balance score (10 - penalties for deviations)
    balance_score = 10.0
    balance_score -= success_deviation * 10
    balance_score -= failure_deviation * 10
    balance_score -= neutral_deviation * 10
    
    return max(0.0, balance_score)


def _calculate_accessibility_score(accessibility: Dict[str, float]) -> float:
    """Calculate overall accessibility score."""
    
    if not accessibility:
        return 0.0
    
    # All endings should be reasonably accessible
    min_accessibility = min(accessibility.values())
    avg_accessibility = sum(accessibility.values()) / len(accessibility)
    
    # Score based on minimum and average
    score = (min_accessibility * 0.6 + avg_accessibility * 0.4) * 10
    
    return max(0.0, min(10.0, score))


def _calculate_differentiation_score(adventure: AdventureGame) -> float:
    """Calculate how well differentiated the endings are."""
    
    if len(adventure.endings) < 2:
        return 5.0  # Neutral score for single ending
    
    # Compare ending texts for similarity
    ending_texts = list(adventure.endings.values())
    
    total_comparisons = 0
    similarity_sum = 0.0
    
    for i in range(len(ending_texts)):
        for j in range(i + 1, len(ending_texts)):
            similarity = _calculate_text_similarity(ending_texts[i], ending_texts[j])
            similarity_sum += similarity
            total_comparisons += 1
    
    if total_comparisons == 0:
        return 5.0
    
    avg_similarity = similarity_sum / total_comparisons
    
    # Lower similarity means better differentiation
    differentiation_score = (1.0 - avg_similarity) * 10
    
    return max(0.0, min(10.0, differentiation_score))


def _calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts (0-1 scale)."""
    
    # Simple word-based similarity
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 and not words2:
        return 1.0
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0


def _calculate_overall_ending_score(analysis: EndingAnalysis) -> float:
    """Calculate overall ending optimization score."""
    
    # Weighted average of component scores
    overall = (
        analysis.balance_score * 0.4 +
        analysis.accessibility_score * 0.3 +
        analysis.differentiation_score * 0.3
    )
    
    return max(0.0, min(10.0, overall))


async def _analyze_ending_balance_impl(adventure: AdventureGame, deps: EndingDependencies) -> EndingAnalysis:
    """Implementation of ending balance analysis."""
    
    analysis = EndingAnalysis()
    
    # Calculate all metrics
    analysis.ending_distribution = _calculate_ending_distribution(adventure)
    analysis.ending_accessibility = _calculate_ending_accessibility(adventure)
    analysis.choice_to_ending_paths = _map_choice_to_ending_paths(adventure)
    analysis.ending_quality_scores = _score_ending_quality(adventure)
    
    # Calculate scores
    analysis.balance_score = _calculate_balance_score(analysis.ending_distribution, deps)
    analysis.accessibility_score = _calculate_accessibility_score(analysis.ending_accessibility)
    analysis.differentiation_score = _calculate_differentiation_score(adventure)
    analysis.overall_score = _calculate_overall_ending_score(analysis)
    
    return analysis


async def _generate_optimization_suggestions(
    adventure: AdventureGame,
    analysis: EndingAnalysis,
    deps: EndingDependencies
) -> List[OptimizationSuggestion]:
    """Generate suggestions for improving ending balance."""
    
    suggestions = []
    
    # Check balance issues
    if analysis.balance_score < 7.0:
        suggestions.extend(_suggest_balance_improvements(adventure, analysis, deps))
    
    # Check accessibility issues
    if analysis.accessibility_score < 6.0:
        suggestions.extend(_suggest_accessibility_improvements(adventure, analysis))
    
    # Check differentiation issues
    if analysis.differentiation_score < 6.0:
        suggestions.extend(_suggest_differentiation_improvements(adventure, analysis))
    
    # Check ending quality issues
    suggestions.extend(_suggest_quality_improvements(adventure, analysis))
    
    return suggestions


def _suggest_balance_improvements(
    adventure: AdventureGame,
    analysis: EndingAnalysis,
    deps: EndingDependencies
) -> List[OptimizationSuggestion]:
    """Suggest improvements for ending balance."""
    
    suggestions = []
    
    total_paths = sum(analysis.ending_distribution.values())
    if total_paths == 0:
        return suggestions
    
    # Check if success rate is too low
    success_paths = analysis.ending_distribution.get("ENDING_SUCCESS", 0)
    success_ratio = success_paths / total_paths
    
    if success_ratio < deps.target_success_rate - 0.1:
        suggestions.append(OptimizationSuggestion(
            "INCREASE_SUCCESS_PATHS",
            f"Add more paths to success ending (current: {success_ratio:.1%}, target: {deps.target_success_rate:.1%})",
            "ENDING_DISTRIBUTION",
            "high"
        ))
    
    # Check if failure rate is too high
    failure_paths = analysis.ending_distribution.get("ENDING_FAILURE", 0)
    failure_ratio = failure_paths / total_paths
    
    if failure_ratio > deps.target_failure_rate + 0.1:
        suggestions.append(OptimizationSuggestion(
            "REDUCE_FAILURE_PATHS",
            f"Reduce paths to failure ending (current: {failure_ratio:.1%}, target: {deps.target_failure_rate:.1%})",
            "ENDING_DISTRIBUTION",
            "medium"
        ))
    
    # Check for missing neutral paths
    neutral_paths = analysis.ending_distribution.get("ENDING_NEUTRAL", 0)
    
    if neutral_paths == 0 and len(adventure.endings) > 2:
        suggestions.append(OptimizationSuggestion(
            "ADD_NEUTRAL_PATHS",
            "Add paths to neutral ending for better balance",
            "ENDING_DISTRIBUTION",
            "medium"
        ))
    
    return suggestions


def _suggest_accessibility_improvements(
    adventure: AdventureGame,
    analysis: EndingAnalysis
) -> List[OptimizationSuggestion]:
    """Suggest improvements for ending accessibility."""
    
    suggestions = []
    
    # Find inaccessible endings
    for ending_key, accessibility in analysis.ending_accessibility.items():
        if accessibility < 0.1:  # Very low accessibility
            suggestions.append(OptimizationSuggestion(
                "IMPROVE_ENDING_ACCESSIBILITY",
                f"Ending '{ending_key}' is difficult to reach (accessibility: {accessibility:.1%})",
                f"ENDING_{ending_key.upper()}",
                "high"
            ))
        elif accessibility < 0.3:  # Low accessibility
            suggestions.append(OptimizationSuggestion(
                "IMPROVE_ENDING_ACCESSIBILITY",
                f"Ending '{ending_key}' has low accessibility (accessibility: {accessibility:.1%})",
                f"ENDING_{ending_key.upper()}",
                "medium"
            ))
    
    return suggestions


def _suggest_differentiation_improvements(
    adventure: AdventureGame,
    analysis: EndingAnalysis
) -> List[OptimizationSuggestion]:
    """Suggest improvements for ending differentiation."""
    
    suggestions = []
    
    if analysis.differentiation_score < 6.0:
        suggestions.append(OptimizationSuggestion(
            "IMPROVE_ENDING_DIFFERENTIATION",
            "Endings are too similar - make them more distinct in tone, content, and consequences",
            "ALL_ENDINGS",
            "medium"
        ))
    
    # Check for very short endings
    for ending_key, ending_text in adventure.endings.items():
        if len(ending_text.strip()) < 30:
            suggestions.append(OptimizationSuggestion(
                "EXPAND_ENDING_CONTENT",
                f"Ending '{ending_key}' is too brief - add more detail and emotional impact",
                f"ENDING_{ending_key.upper()}",
                "medium"
            ))
    
    return suggestions


def _suggest_quality_improvements(
    adventure: AdventureGame,
    analysis: EndingAnalysis
) -> List[OptimizationSuggestion]:
    """Suggest improvements for ending quality."""
    
    suggestions = []
    
    for ending_key, quality_score in analysis.ending_quality_scores.items():
        if quality_score < 5.0:
            suggestions.append(OptimizationSuggestion(
                "IMPROVE_ENDING_QUALITY",
                f"Ending '{ending_key}' has low quality score ({quality_score:.1f}/10) - improve content and emotional impact",
                f"ENDING_{ending_key.upper()}",
                "high"
            ))
        elif quality_score < 7.0:
            suggestions.append(OptimizationSuggestion(
                "ENHANCE_ENDING_QUALITY",
                f"Ending '{ending_key}' could be enhanced (score: {quality_score:.1f}/10)",
                f"ENDING_{ending_key.upper()}",
                "medium"
            ))
    
    return suggestions


async def _apply_optimizations(
    adventure: AdventureGame,
    suggestions: List[OptimizationSuggestion]
) -> AdventureGame:
    """Apply optimization suggestions to the adventure."""
    
    optimized_adventure = adventure.model_copy()
    
    # Group suggestions by type and apply them
    for suggestion in suggestions:
        if suggestion.suggestion_type == "INCREASE_SUCCESS_PATHS":
            optimized_adventure = await _increase_success_paths(optimized_adventure)
        elif suggestion.suggestion_type == "REDUCE_FAILURE_PATHS":
            optimized_adventure = await _reduce_failure_paths(optimized_adventure)
        elif suggestion.suggestion_type == "ADD_NEUTRAL_PATHS":
            optimized_adventure = await _add_neutral_paths(optimized_adventure)
        elif suggestion.suggestion_type == "IMPROVE_ENDING_ACCESSIBILITY":
            optimized_adventure = await _improve_ending_accessibility(optimized_adventure, suggestion.location)
        elif suggestion.suggestion_type == "EXPAND_ENDING_CONTENT":
            optimized_adventure = await _expand_ending_content(optimized_adventure, suggestion.location)
    
    return optimized_adventure


async def _increase_success_paths(adventure: AdventureGame) -> AdventureGame:
    """Increase paths leading to success ending."""
    
    modified_steps = adventure.steps.copy()
    
    # Find steps where we can change failure choices to success
    for step_id, step in modified_steps.items():
        failure_choices = [i for i, choice in enumerate(step.choices) if choice.target == "ENDING_FAILURE"]
        
        if failure_choices and len(failure_choices) > 1:
            # Change one failure choice to success
            choice_index = failure_choices[0]
            new_choices = step.choices.copy()
            new_choices[choice_index] = new_choices[choice_index].model_copy(update={"target": "ENDING_SUCCESS"})
            modified_steps[step_id] = step.model_copy(update={"choices": new_choices})
            break  # Only modify one step at a time
    
    return adventure.model_copy(update={"steps": modified_steps})


async def _reduce_failure_paths(adventure: AdventureGame) -> AdventureGame:
    """Reduce paths leading to failure ending."""
    
    modified_steps = adventure.steps.copy()
    
    # Find steps where we can change failure choices to neutral or success
    for step_id, step in modified_steps.items():
        failure_choices = [i for i, choice in enumerate(step.choices) if choice.target == "ENDING_FAILURE"]
        
        if failure_choices:
            # Change one failure choice to neutral
            choice_index = failure_choices[0]
            new_choices = step.choices.copy()
            target = "ENDING_NEUTRAL" if "neutral" in adventure.endings else "ENDING_SUCCESS"
            new_choices[choice_index] = new_choices[choice_index].model_copy(update={"target": target})
            modified_steps[step_id] = step.model_copy(update={"choices": new_choices})
            break
    
    return adventure.model_copy(update={"steps": modified_steps})


async def _add_neutral_paths(adventure: AdventureGame) -> AdventureGame:
    """Add paths leading to neutral ending."""
    
    # Ensure neutral ending exists
    if "neutral" not in adventure.endings:
        new_endings = adventure.endings.copy()
        new_endings["neutral"] = "Your journey concludes with mixed results. You have learned valuable lessons, though the outcome remains uncertain."
        adventure = adventure.model_copy(update={"endings": new_endings})
    
    modified_steps = adventure.steps.copy()
    
    # Find a step where we can add a neutral path
    for step_id, step in modified_steps.items():
        if len(step.choices) < 4:  # Can add another choice
            # Add a neutral choice
            new_choices = step.choices.copy()
            from ..models import ChoiceLabel
            
            # Find next available label
            used_labels = {choice.label for choice in new_choices}
            available_labels = [ChoiceLabel.A, ChoiceLabel.B, ChoiceLabel.C, ChoiceLabel.D]
            next_label = None
            
            for label in available_labels:
                if label not in used_labels:
                    next_label = label
                    break
            
            if next_label:
                new_choice = Choice(
                    label=next_label,
                    description="Take a cautious middle path",
                    target="ENDING_NEUTRAL",
                    conditions=[],
                    consequences=[]
                )
                new_choices.append(new_choice)
                modified_steps[step_id] = step.model_copy(update={"choices": new_choices})
                break
    
    return adventure.model_copy(update={"steps": modified_steps})


async def _improve_ending_accessibility(adventure: AdventureGame, location: str) -> AdventureGame:
    """Improve accessibility of a specific ending."""
    
    # Extract ending name from location
    if "ENDING_" in location:
        ending_name = location.replace("ENDING_", "").lower()
        target_ending = f"ENDING_{ending_name.upper()}"
        
        # Find steps that could lead to this ending
        modified_steps = adventure.steps.copy()
        
        for step_id, step in modified_steps.items():
            # If this step leads to other endings, add a choice for this ending
            if len(step.choices) < 4 and not any(choice.target == target_ending for choice in step.choices):
                new_choices = step.choices.copy()
                from ..models import ChoiceLabel
                
                # Find next available label
                used_labels = {choice.label for choice in new_choices}
                available_labels = [ChoiceLabel.A, ChoiceLabel.B, ChoiceLabel.C, ChoiceLabel.D]
                
                for label in available_labels:
                    if label not in used_labels:
                        new_choice = Choice(
                            label=label,
                            description=f"Pursue the path to {ending_name}",
                            target=target_ending,
                            conditions=[],
                            consequences=[]
                        )
                        new_choices.append(new_choice)
                        modified_steps[step_id] = step.model_copy(update={"choices": new_choices})
                        break
                break
        
        return adventure.model_copy(update={"steps": modified_steps})
    
    return adventure


async def _expand_ending_content(adventure: AdventureGame, location: str) -> AdventureGame:
    """Expand the content of a specific ending."""
    
    if "ENDING_" in location:
        ending_name = location.replace("ENDING_", "").lower()
        
        if ending_name in adventure.endings:
            current_text = adventure.endings[ending_name]
            
            # Add more content based on ending type
            if ending_name == "success":
                expanded_text = current_text + " Your courage and determination have paid off, and you can be proud of what you've accomplished. The skills you've gained and the experiences you've had will serve you well in future adventures."
            elif ending_name == "failure":
                expanded_text = current_text + " Though this particular path didn't lead to success, every setback is an opportunity to learn and grow. Your journey has taught you valuable lessons that will help you in future endeavors."
            elif ending_name == "neutral":
                expanded_text = current_text + " Sometimes the most important outcomes aren't about winning or losing, but about the journey itself and what you discover along the way. Your experience has been meaningful, regardless of the final result."
            else:
                expanded_text = current_text + " This outcome reflects the choices you made throughout your adventure, each decision shaping your path and ultimate destination."
            
            new_endings = adventure.endings.copy()
            new_endings[ending_name] = expanded_text
            
            return adventure.model_copy(update={"endings": new_endings})
    
    return adventure


def _generate_improvement_report(original: EndingAnalysis, final: EndingAnalysis) -> Dict[str, float]:
    """Generate a report of improvements made."""
    
    return {
        "balance_score_improvement": final.balance_score - original.balance_score,
        "accessibility_score_improvement": final.accessibility_score - original.accessibility_score,
        "differentiation_score_improvement": final.differentiation_score - original.differentiation_score,
        "overall_score_improvement": final.overall_score - original.overall_score,
        "original_overall_score": original.overall_score,
        "final_overall_score": final.overall_score
    }


async def generate_ending_report(adventure: AdventureGame) -> str:
    """
    Generate a comprehensive ending analysis report.
    
    Args:
        adventure: Adventure to analyze
        
    Returns:
        Formatted ending analysis report
    """
    deps = EndingDependencies()
    analysis = await _analyze_ending_balance_impl(adventure, deps)
    
    lines = ["=== Ending Analysis Report ===", ""]
    
    # Overall Scores
    lines.append("OVERALL SCORES:")
    lines.append(f"  Overall: {analysis.overall_score:.1f}/10")
    lines.append(f"  Balance: {analysis.balance_score:.1f}/10")
    lines.append(f"  Accessibility: {analysis.accessibility_score:.1f}/10")
    lines.append(f"  Differentiation: {analysis.differentiation_score:.1f}/10")
    lines.append("")
    
    # Distribution Analysis
    if analysis.ending_distribution:
        lines.append("ENDING DISTRIBUTION:")
        total_paths = sum(analysis.ending_distribution.values())
        for ending, count in analysis.ending_distribution.items():
            percentage = (count / total_paths * 100) if total_paths > 0 else 0
            lines.append(f"  {ending}: {count} paths ({percentage:.1f}%)")
        lines.append("")
    
    # Accessibility Analysis
    if analysis.ending_accessibility:
        lines.append("ENDING ACCESSIBILITY:")
        for ending, accessibility in analysis.ending_accessibility.items():
            lines.append(f"  {ending}: {accessibility:.1%}")
        lines.append("")
    
    # Quality Scores
    if analysis.ending_quality_scores:
        lines.append("ENDING QUALITY SCORES:")
        for ending, score in analysis.ending_quality_scores.items():
            lines.append(f"  {ending}: {score:.1f}/10")
        lines.append("")
    
    # Recommendations
    lines.append("RECOMMENDATIONS:")
    if analysis.balance_score < 7.0:
        lines.append("  • Improve ending distribution balance")
    if analysis.accessibility_score < 6.0:
        lines.append("  • Make endings more accessible to players")
    if analysis.differentiation_score < 6.0:
        lines.append("  • Increase differentiation between endings")
    if analysis.overall_score >= 8.0:
        lines.append("  • Ending structure is well-balanced!")
    
    return "\n".join(lines)