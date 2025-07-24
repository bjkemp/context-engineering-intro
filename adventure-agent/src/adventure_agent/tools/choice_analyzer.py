"""
Choice Analyzer Tool for the Adventure Generation Agent.

This tool verifies that choices lead to meaningfully different outcomes,
validates choice descriptions and consequences, and scores choice impact and player agency.
"""

from typing import Dict, List, Set, Tuple

from pydantic_ai import Agent, RunContext

from ..models import AdventureGame, Choice, ToolResult


class ChoiceImpactAnalysis:
    """Analysis of choice impact and consequences."""
    
    def __init__(self):
        self.choice_impact_scores: Dict[str, float] = {}
        self.choice_differentiation: Dict[str, float] = {}
        self.consequence_consistency: Dict[str, float] = {}
        self.player_agency_score: float = 0.0
        self.meaningful_choices_ratio: float = 0.0
        self.choice_quality_score: float = 0.0
        self.overall_choice_score: float = 0.0


class ChoiceIssue:
    """Represents an issue with a choice."""
    
    def __init__(self, issue_type: str, description: str, location: str, severity: str = "medium"):
        self.issue_type = issue_type
        self.description = description
        self.location = location
        self.severity = severity  # low, medium, high, critical
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.issue_type}: {self.description} ({self.location})"


class ChoiceDependencies:
    """Dependencies for choice analysis."""
    
    def __init__(self):
        self.analysis = ChoiceImpactAnalysis()
        self.min_impact_threshold = 0.3
        self.min_differentiation_threshold = 0.5


def create_choice_agent() -> Agent[ChoiceDependencies, ChoiceImpactAnalysis]:
    """Create choice analysis agent."""
    return Agent[ChoiceDependencies, ChoiceImpactAnalysis](
        'gemini-1.5-flash',
        deps_type=ChoiceDependencies,
        output_type=ChoiceImpactAnalysis,
        system_prompt=(
            "You are a choice impact expert. Analyze player choices for meaningful "
            "differentiation, consequence consistency, and overall impact on the "
            "story. Ensure every choice matters and leads to distinct outcomes."
        ),
    )


async def analyze_choice_impact(
    ctx: RunContext[ChoiceDependencies],
    adventure: AdventureGame
) -> ChoiceImpactAnalysis:
    """
    Analyze the impact and quality of choices in the adventure.
    
    Args:
        ctx: Agent context with dependencies
        adventure: Adventure to analyze
        
    Returns:
        ChoiceImpactAnalysis containing choice analysis
    """
    analysis = ctx.deps.analysis
    
    # Analyze impact of each choice
    analysis.choice_impact_scores = _calculate_choice_impact_scores(adventure)
    
    # Analyze choice differentiation
    analysis.choice_differentiation = _calculate_choice_differentiation(adventure)
    
    # Analyze consequence consistency
    analysis.consequence_consistency = _analyze_consequence_consistency(adventure)
    
    # Calculate player agency
    analysis.player_agency_score = _calculate_player_agency_score(adventure)
    
    # Calculate meaningful choices ratio
    analysis.meaningful_choices_ratio = _calculate_meaningful_choices_ratio(analysis, ctx.deps)
    
    # Calculate overall quality
    analysis.choice_quality_score = _calculate_choice_quality_score(adventure)
    analysis.overall_choice_score = _calculate_overall_choice_score(analysis)
    
    return analysis


async def analyze_choices(adventure: AdventureGame) -> ToolResult:
    """
    Main choice analysis function.
    
    Args:
        adventure: Adventure to analyze
        
    Returns:
        ToolResult with choice analysis and recommendations
    """
    try:
        # Set up dependencies
        deps = ChoiceDependencies()
        
        # Perform comprehensive choice analysis
        analysis = await _analyze_choices_impl(adventure, deps)
        
        # Identify choice issues
        issues = await _identify_choice_issues(adventure, analysis, deps)
        
        # Generate recommendations
        recommendations = _generate_choice_recommendations(analysis, issues)
        
        # Generate detailed report
        report = _generate_choice_report(analysis, adventure, issues)
        
        # Count issues by severity
        critical_issues = len([i for i in issues if i.severity == "critical"])
        high_issues = len([i for i in issues if i.severity == "high"])
        total_issues = len(issues)
        
        return ToolResult(
            success=critical_issues == 0,
            data={
                "analysis": analysis,
                "issues": issues,
                "recommendations": recommendations,
                "report": report,
                "issue_summary": {
                    "total_issues": total_issues,
                    "critical_issues": critical_issues,
                    "high_issues": high_issues,
                    "meaningful_choices_ratio": analysis.meaningful_choices_ratio,
                    "player_agency_score": analysis.player_agency_score
                }
            },
            message=f"Choice analysis: {analysis.overall_choice_score:.1f}/10 overall score, {total_issues} issues found",
            metadata={
                "overall_score": analysis.overall_choice_score,
                "player_agency": analysis.player_agency_score,
                "meaningful_ratio": analysis.meaningful_choices_ratio,
                "total_issues": total_issues,
                "critical_issues": critical_issues
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Choice analysis failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


def _calculate_choice_impact_scores(adventure: AdventureGame) -> Dict[str, float]:
    """Calculate impact score for each choice (0-1 scale)."""
    
    impact_scores = {}
    
    for step_id, step in adventure.steps.items():
        for i, choice in enumerate(step.choices):
            choice_key = f"STEP_{step_id}.CHOICE_{i+1}"
            
            # Calculate impact based on multiple factors
            impact_score = 0.0
            
            # 1. Target impact (where does it lead?)
            if choice.target.startswith("ENDING_"):
                impact_score += 0.4  # High impact - direct ending
            elif choice.target.startswith("STEP_"):
                # Medium impact - leads to another step
                impact_score += 0.2
            
            # 2. Consequence impact
            if choice.consequences:
                impact_score += min(0.3, len(choice.consequences) * 0.1)
            
            # 3. Condition complexity
            if choice.conditions:
                impact_score += min(0.2, len(choice.conditions) * 0.05)
            
            # 4. Description quality/complexity
            description_length = len(choice.description.strip())
            if description_length > 20:
                impact_score += 0.1
            
            # Normalize to 0-1 scale
            impact_scores[choice_key] = min(1.0, impact_score)
    
    return impact_scores


def _calculate_choice_differentiation(adventure: AdventureGame) -> Dict[str, float]:
    """Calculate how different choices are within each step."""
    
    differentiation_scores = {}
    
    for step_id, step in adventure.steps.items():
        if len(step.choices) < 2:
            # Single choice gets neutral score
            for i, choice in enumerate(step.choices):
                choice_key = f"STEP_{step_id}.CHOICE_{i+1}"
                differentiation_scores[choice_key] = 0.5
            continue
        
        # Compare each choice with others in the same step
        for i, choice in enumerate(step.choices):
            choice_key = f"STEP_{step_id}.CHOICE_{i+1}"
            
            total_difference = 0.0
            comparisons = 0
            
            for j, other_choice in enumerate(step.choices):
                if i != j:
                    # Calculate difference between choices
                    difference = _calculate_choice_difference(choice, other_choice)
                    total_difference += difference
                    comparisons += 1
            
            if comparisons > 0:
                avg_difference = total_difference / comparisons
                differentiation_scores[choice_key] = avg_difference
            else:
                differentiation_scores[choice_key] = 0.5
    
    return differentiation_scores


def _calculate_choice_difference(choice1: Choice, choice2: Choice) -> float:
    """Calculate difference between two choices (0-1 scale)."""
    
    difference = 0.0
    
    # 1. Target difference
    if choice1.target != choice2.target:
        difference += 0.4
    
    # 2. Description difference
    desc_similarity = _calculate_text_similarity(choice1.description, choice2.description)
    difference += (1.0 - desc_similarity) * 0.3
    
    # 3. Consequence difference
    if choice1.consequences != choice2.consequences:
        consequence_similarity = _calculate_list_similarity(choice1.consequences, choice2.consequences)
        difference += (1.0 - consequence_similarity) * 0.2
    
    # 4. Condition difference
    if choice1.conditions != choice2.conditions:
        condition_similarity = _calculate_list_similarity(choice1.conditions, choice2.conditions)
        difference += (1.0 - condition_similarity) * 0.1
    
    return min(1.0, difference)


def _calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two text strings."""
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 and not words2:
        return 1.0
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0


def _calculate_list_similarity(list1: List[str], list2: List[str]) -> float:
    """Calculate similarity between two lists of strings."""
    
    if not list1 and not list2:
        return 1.0
    
    if not list1 or not list2:
        return 0.0
    
    set1 = set(list1)
    set2 = set(list2)
    
    intersection = set1 & set2
    union = set1 | set2
    
    return len(intersection) / len(union) if union else 0.0


def _analyze_consequence_consistency(adventure: AdventureGame) -> Dict[str, float]:
    """Analyze consistency between choice descriptions and consequences."""
    
    consistency_scores = {}
    
    for step_id, step in adventure.steps.items():
        for i, choice in enumerate(step.choices):
            choice_key = f"STEP_{step_id}.CHOICE_{i+1}"
            
            # Check if consequences make sense for the choice
            consistency_score = _check_choice_consequence_consistency(choice)
            consistency_scores[choice_key] = consistency_score
    
    return consistency_scores


def _check_choice_consequence_consistency(choice: Choice) -> float:
    """Check if choice consequences are consistent with the choice description."""
    
    if not choice.consequences:
        return 0.5  # Neutral - no consequences to check
    
    description_lower = choice.description.lower()
    consistency_score = 1.0  # Start with perfect score
    
    for consequence in choice.consequences:
        consequence_lower = consequence.lower()
        
        # Check for obvious inconsistencies
        if "dangerous" in description_lower or "fight" in description_lower:
            if "health +" in consequence_lower:
                consistency_score -= 0.2  # Inconsistent - dangerous action giving health
        
        if "helpful" in description_lower or "aid" in description_lower:
            if "reputation -" in consequence_lower:
                consistency_score -= 0.2  # Inconsistent - helpful action losing reputation
        
        if "negotiate" in description_lower or "diplomatic" in description_lower:
            if "violence" in consequence_lower or "combat" in consequence_lower:
                consistency_score -= 0.3  # Very inconsistent
        
        if "careful" in description_lower or "cautious" in description_lower:
            if "reckless" in consequence_lower or "bold" in consequence_lower:
                consistency_score -= 0.2
    
    return max(0.0, consistency_score)


def _calculate_player_agency_score(adventure: AdventureGame) -> float:
    """Calculate overall player agency score (0-10 scale)."""
    
    total_choices = 0
    meaningful_choices = 0
    
    for step in adventure.steps.values():
        total_choices += len(step.choices)
        
        # Count meaningful choices (those with different targets or consequences)
        if len(step.choices) > 1:
            targets = set(choice.target for choice in step.choices)
            
            if len(targets) > 1:
                meaningful_choices += len(step.choices)
            else:
                # Same targets but different consequences might still be meaningful
                for choice in step.choices:
                    if choice.consequences:
                        meaningful_choices += 1
    
    if total_choices == 0:
        return 0.0
    
    agency_ratio = meaningful_choices / total_choices
    
    # Additional factors
    choice_variety = len(set(choice.target for step in adventure.steps.values() for choice in step.choices))
    variety_bonus = min(2.0, choice_variety * 0.2)
    
    # Convert to 0-10 scale
    agency_score = (agency_ratio * 8.0) + variety_bonus
    
    return min(10.0, agency_score)


def _calculate_meaningful_choices_ratio(analysis: ChoiceImpactAnalysis, deps: ChoiceDependencies) -> float:
    """Calculate the ratio of choices that have meaningful impact."""
    
    if not analysis.choice_impact_scores:
        return 0.0
    
    meaningful_count = sum(1 for score in analysis.choice_impact_scores.values() 
                          if score >= deps.min_impact_threshold)
    
    total_count = len(analysis.choice_impact_scores)
    
    return meaningful_count / total_count if total_count > 0 else 0.0


def _calculate_choice_quality_score(adventure: AdventureGame) -> float:
    """Calculate overall choice quality score (0-10 scale)."""
    
    total_score = 0.0
    total_choices = 0
    
    for step in adventure.steps.values():
        for choice in step.choices:
            total_choices += 1
            
            # Quality factors
            choice_score = 5.0  # Base score
            
            # Description quality
            desc_length = len(choice.description.strip())
            if desc_length < 10:
                choice_score -= 2.0  # Too short
            elif desc_length > 100:
                choice_score -= 1.0  # Too long
            elif 20 <= desc_length <= 80:
                choice_score += 1.0  # Good length
            
            # Has consequences
            if choice.consequences:
                choice_score += 1.0
            
            # Has conditions (shows complexity)
            if choice.conditions:
                choice_score += 0.5
            
            # Descriptive language
            if any(word in choice.description.lower() for word in ["carefully", "boldly", "wisely", "cleverly"]):
                choice_score += 0.5
            
            total_score += max(0.0, min(10.0, choice_score))
    
    return total_score / total_choices if total_choices > 0 else 0.0


def _calculate_overall_choice_score(analysis: ChoiceImpactAnalysis) -> float:
    """Calculate overall choice analysis score."""
    
    # Weighted combination of factors
    overall_score = (
        analysis.player_agency_score * 0.3 +
        analysis.meaningful_choices_ratio * 10 * 0.25 +
        analysis.choice_quality_score * 0.25 +
        (sum(analysis.choice_differentiation.values()) / len(analysis.choice_differentiation) * 10 if analysis.choice_differentiation else 5.0) * 0.2
    )
    
    return min(10.0, max(0.0, overall_score))


async def _analyze_choices_impl(adventure: AdventureGame, deps: ChoiceDependencies) -> ChoiceImpactAnalysis:
    """Implementation of choice analysis."""
    
    analysis = ChoiceImpactAnalysis()
    
    # Calculate all metrics
    analysis.choice_impact_scores = _calculate_choice_impact_scores(adventure)
    analysis.choice_differentiation = _calculate_choice_differentiation(adventure)
    analysis.consequence_consistency = _analyze_consequence_consistency(adventure)
    analysis.player_agency_score = _calculate_player_agency_score(adventure)
    analysis.meaningful_choices_ratio = _calculate_meaningful_choices_ratio(analysis, deps)
    analysis.choice_quality_score = _calculate_choice_quality_score(adventure)
    analysis.overall_choice_score = _calculate_overall_choice_score(analysis)
    
    return analysis


async def _identify_choice_issues(
    adventure: AdventureGame,
    analysis: ChoiceImpactAnalysis,
    deps: ChoiceDependencies
) -> List[ChoiceIssue]:
    """Identify issues with choices."""
    
    issues = []
    
    # Check for low-impact choices
    for choice_key, impact_score in analysis.choice_impact_scores.items():
        if impact_score < deps.min_impact_threshold:
            issues.append(ChoiceIssue(
                "LOW_IMPACT_CHOICE",
                f"Choice has low impact (score: {impact_score:.2f})",
                choice_key,
                "medium"
            ))
    
    # Check for poor differentiation
    for choice_key, diff_score in analysis.choice_differentiation.items():
        if diff_score < deps.min_differentiation_threshold:
            issues.append(ChoiceIssue(
                "POOR_CHOICE_DIFFERENTIATION",
                f"Choice is too similar to others (differentiation: {diff_score:.2f})",
                choice_key,
                "medium"
            ))
    
    # Check for inconsistent consequences
    for choice_key, consistency_score in analysis.consequence_consistency.items():
        if consistency_score < 0.5:
            issues.append(ChoiceIssue(
                "INCONSISTENT_CONSEQUENCES",
                f"Choice consequences don't match description (consistency: {consistency_score:.2f})",
                choice_key,
                "high"
            ))
    
    # Check for steps with all identical targets
    for step_id, step in adventure.steps.items():
        if len(step.choices) > 1:
            targets = set(choice.target for choice in step.choices)
            if len(targets) == 1:
                issues.append(ChoiceIssue(
                    "IDENTICAL_CHOICE_TARGETS",
                    "All choices in step lead to the same target",
                    f"STEP_{step_id}",
                    "high"
                ))
    
    # Check for very short choice descriptions
    for step_id, step in adventure.steps.items():
        for i, choice in enumerate(step.choices):
            if len(choice.description.strip()) < 5:
                choice_key = f"STEP_{step_id}.CHOICE_{i+1}"
                issues.append(ChoiceIssue(
                    "TOO_SHORT_DESCRIPTION",
                    f"Choice description is too short: '{choice.description}'",
                    choice_key,
                    "medium"
                ))
    
    # Check for missing consequences on impactful choices
    for step_id, step in adventure.steps.items():
        for i, choice in enumerate(step.choices):
            choice_key = f"STEP_{step_id}.CHOICE_{i+1}"
            impact_score = analysis.choice_impact_scores.get(choice_key, 0)
            
            if impact_score > 0.5 and not choice.consequences:
                issues.append(ChoiceIssue(
                    "MISSING_CONSEQUENCES",
                    "High-impact choice lacks consequences",
                    choice_key,
                    "medium"
                ))
    
    return issues


def _generate_choice_recommendations(analysis: ChoiceImpactAnalysis, issues: List[ChoiceIssue]) -> List[str]:
    """Generate recommendations for improving choices."""
    
    recommendations = []
    
    if analysis.player_agency_score < 6.0:
        recommendations.append("Increase player agency by adding more meaningful choice consequences")
    
    if analysis.meaningful_choices_ratio < 0.6:
        recommendations.append("Make more choices meaningful by varying their outcomes and consequences")
    
    if analysis.choice_quality_score < 6.0:
        recommendations.append("Improve choice descriptions and add more consequences")
    
    # Issue-specific recommendations
    issue_types = {issue.issue_type for issue in issues}
    
    if "LOW_IMPACT_CHOICE" in issue_types:
        recommendations.append("Add consequences to low-impact choices to make them more meaningful")
    
    if "POOR_CHOICE_DIFFERENTIATION" in issue_types:
        recommendations.append("Make choices more distinct in description, target, and consequences")
    
    if "INCONSISTENT_CONSEQUENCES" in issue_types:
        recommendations.append("Align choice consequences with their descriptions")
    
    if "IDENTICAL_CHOICE_TARGETS" in issue_types:
        recommendations.append("Vary choice targets to provide different story paths")
    
    if not recommendations and analysis.overall_choice_score >= 8.0:
        recommendations.append("Choice structure is excellent - maintain quality across all choices")
    
    return recommendations


def _generate_choice_report(
    analysis: ChoiceImpactAnalysis,
    adventure: AdventureGame,
    issues: List[ChoiceIssue]
) -> str:
    """Generate a comprehensive choice analysis report."""
    
    lines = ["=== Choice Analysis Report ===", ""]
    
    # Overall Scores
    lines.append("OVERALL SCORES:")
    lines.append(f"  Choice Quality: {analysis.overall_choice_score:.1f}/10")
    lines.append(f"  Player Agency: {analysis.player_agency_score:.1f}/10")
    lines.append(f"  Meaningful Choices: {analysis.meaningful_choices_ratio:.1%}")
    lines.append(f"  Choice Descriptions: {analysis.choice_quality_score:.1f}/10")
    lines.append("")
    
    # Choice Statistics
    total_choices = sum(len(step.choices) for step in adventure.steps.values())
    avg_choices_per_step = total_choices / len(adventure.steps) if adventure.steps else 0
    
    lines.append("CHOICE STATISTICS:")
    lines.append(f"  Total Choices: {total_choices}")
    lines.append(f"  Average Choices per Step: {avg_choices_per_step:.1f}")
    lines.append(f"  Steps with Choices: {len(adventure.steps)}")
    lines.append("")
    
    # Impact Analysis
    if analysis.choice_impact_scores:
        impact_scores = list(analysis.choice_impact_scores.values())
        avg_impact = sum(impact_scores) / len(impact_scores)
        high_impact_count = sum(1 for score in impact_scores if score > 0.7)
        
        lines.append("IMPACT ANALYSIS:")
        lines.append(f"  Average Impact Score: {avg_impact:.2f}")
        lines.append(f"  High Impact Choices: {high_impact_count}")
        lines.append(f"  Low Impact Choices: {sum(1 for score in impact_scores if score < 0.3)}")
        lines.append("")
    
    # Differentiation Analysis
    if analysis.choice_differentiation:
        diff_scores = list(analysis.choice_differentiation.values())
        avg_differentiation = sum(diff_scores) / len(diff_scores)
        
        lines.append("DIFFERENTIATION ANALYSIS:")
        lines.append(f"  Average Differentiation: {avg_differentiation:.2f}")
        lines.append(f"  Well-Differentiated Choices: {sum(1 for score in diff_scores if score > 0.7)}")
        lines.append(f"  Poorly Differentiated: {sum(1 for score in diff_scores if score < 0.5)}")
        lines.append("")
    
    # Issues Summary
    if issues:
        lines.append("ISSUES FOUND:")
        issue_counts = {}
        for issue in issues:
            issue_counts[issue.issue_type] = issue_counts.get(issue.issue_type, 0) + 1
        
        for issue_type, count in issue_counts.items():
            lines.append(f"  {issue_type}: {count}")
        lines.append("")
        
        # Show critical/high issues
        critical_high_issues = [i for i in issues if i.severity in ["critical", "high"]]
        if critical_high_issues:
            lines.append("CRITICAL/HIGH ISSUES:")
            for issue in critical_high_issues[:5]:  # Show first 5
                lines.append(f"  • {issue}")
            if len(critical_high_issues) > 5:
                lines.append(f"  ... and {len(critical_high_issues) - 5} more")
            lines.append("")
    
    # Recommendations section would go here
    lines.append("RECOMMENDATIONS:")
    if analysis.overall_choice_score >= 8.0:
        lines.append("  • Excellent choice structure - maintain quality")
    else:
        lines.append("  • Focus on improving choice differentiation and impact")
        lines.append("  • Add meaningful consequences to low-impact choices")
        lines.append("  • Ensure choice descriptions clearly indicate different outcomes")
    
    return "\n".join(lines)


async def suggest_choice_improvements(adventure: AdventureGame) -> List[str]:
    """
    Suggest specific improvements for choice quality.
    
    Args:
        adventure: Adventure to analyze
        
    Returns:
        List of specific improvement suggestions
    """
    deps = ChoiceDependencies()
    analysis = await _analyze_choices_impl(adventure, deps)
    issues = await _identify_choice_issues(adventure, analysis, deps)
    
    suggestions = []
    
    # Group issues by step
    step_issues = {}
    for issue in issues:
        if "STEP_" in issue.location:
            step_id = issue.location.split(".")[0]
            if step_id not in step_issues:
                step_issues[step_id] = []
            step_issues[step_id].append(issue)
    
    # Generate step-specific suggestions
    for step_id, step_issue_list in step_issues.items():
        step_num = step_id.replace("STEP_", "")
        
        if any(issue.issue_type == "IDENTICAL_CHOICE_TARGETS" for issue in step_issue_list):
            suggestions.append(f"Step {step_num}: Vary choice targets to create different story paths")
        
        if any(issue.issue_type == "POOR_CHOICE_DIFFERENTIATION" for issue in step_issue_list):
            suggestions.append(f"Step {step_num}: Make choice descriptions more distinct and specific")
        
        if any(issue.issue_type == "LOW_IMPACT_CHOICE" for issue in step_issue_list):
            suggestions.append(f"Step {step_num}: Add consequences to make choices more impactful")
    
    # General suggestions
    if analysis.player_agency_score < 6.0:
        suggestions.append("Overall: Increase player agency by adding more branching paths")
    
    if analysis.meaningful_choices_ratio < 0.5:
        suggestions.append("Overall: Make more choices meaningful by varying outcomes")
    
    return suggestions