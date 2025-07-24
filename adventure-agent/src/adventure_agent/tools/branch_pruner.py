"""
Branch Pruner Tool for the Adventure Generation Agent.

This tool identifies and fixes dead ends in story flow, ensuring all paths lead to
meaningful conclusions and optimizing the story tree structure.
"""

from typing import Dict, List, Set, Tuple

from pydantic_ai import Agent, RunContext

from ..models import AdventureGame, Choice, ChoiceLabel, EndingType, StoryStep, ToolResult


class BranchAnalysis:
    """Analysis results for story branching."""
    
    def __init__(self):
        self.dead_ends: List[str] = []
        self.unreachable_steps: List[str] = []
        self.orphaned_choices: List[Tuple[str, int]] = []  # (step_id, choice_index)
        self.ending_distribution: Dict[str, int] = {}
        self.path_lengths: Dict[str, int] = {}
        self.branching_factor: Dict[str, int] = {}
        self.critical_path_steps: List[str] = []


class BranchDependencies:
    """Dependencies for branch pruning."""
    
    def __init__(self):
        self.analysis = BranchAnalysis()
        self.max_path_length = 20
        self.min_path_length = 3


def create_branch_agent() -> Agent[BranchDependencies, BranchAnalysis]:
    """Create branch pruning agent."""
    return Agent[BranchDependencies, BranchAnalysis](
        'gemini-1.5-flash',
        deps_type=BranchDependencies,
        output_type=BranchAnalysis,
        system_prompt=(
            "You are a story flow expert. Identify dead ends, optimize branching "
            "paths, and ensure every story route leads to meaningful conclusions. "
            "Maintain narrative balance while eliminating structural problems."
        ),
    )


async def analyze_branch_structure(
    ctx: RunContext[BranchDependencies],
    adventure: AdventureGame
) -> BranchAnalysis:
    """
    Analyze the branching structure of the adventure.
    
    Args:
        ctx: Agent context with dependencies
        adventure: Adventure to analyze
        
    Returns:
        BranchAnalysis containing structure analysis
    """
    analysis = ctx.deps.analysis
    
    # Build step graph
    step_graph = _build_step_graph(adventure)
    
    # Find reachable steps from start
    reachable_steps = _find_reachable_steps(step_graph, "1")
    
    # Identify unreachable steps
    all_steps = set(adventure.steps.keys())
    analysis.unreachable_steps = list(all_steps - reachable_steps)
    
    # Find dead ends
    analysis.dead_ends = _find_dead_ends(adventure, step_graph)
    
    # Find orphaned choices
    analysis.orphaned_choices = _find_orphaned_choices(adventure, step_graph)
    
    # Analyze ending distribution
    analysis.ending_distribution = _analyze_ending_distribution(adventure, step_graph)
    
    # Calculate path lengths
    analysis.path_lengths = _calculate_path_lengths(step_graph, "1")
    
    # Calculate branching factors
    analysis.branching_factor = _calculate_branching_factors(adventure)
    
    # Identify critical path
    analysis.critical_path_steps = _find_critical_path(step_graph, "1")
    
    return analysis


async def prune_branches(adventure: AdventureGame) -> ToolResult:
    """
    Main branch pruning function.
    
    Args:
        adventure: Adventure to prune and optimize
        
    Returns:
        ToolResult with pruned adventure and analysis
    """
    try:
        # Set up dependencies
        deps = BranchDependencies()
        
        # Analyze current structure
        analysis = await _analyze_adventure_structure(adventure, deps)
        
        # Create optimized adventure
        optimized_adventure = adventure.model_copy()
        
        # Remove unreachable steps
        optimized_adventure = await _remove_unreachable_steps(optimized_adventure, analysis)
        
        # Fix dead ends
        optimized_adventure = await _fix_dead_ends(optimized_adventure, analysis)
        
        # Remove orphaned choices
        optimized_adventure = await _remove_orphaned_choices(optimized_adventure, analysis)
        
        # Balance ending distribution
        optimized_adventure = await _balance_ending_distribution(optimized_adventure, analysis)
        
        # Optimize path lengths
        optimized_adventure = await _optimize_path_lengths(optimized_adventure, analysis)
        
        # Re-analyze to get final stats
        final_analysis = await _analyze_adventure_structure(optimized_adventure, deps)
        
        # Generate improvement report
        improvements = _generate_improvement_report(analysis, final_analysis)
        
        return ToolResult(
            success=True,
            data={
                "optimized_adventure": optimized_adventure,
                "original_analysis": analysis,
                "final_analysis": final_analysis,
                "improvements": improvements
            },
            message=f"Pruned {len(analysis.dead_ends)} dead ends, removed {len(analysis.unreachable_steps)} unreachable steps",
            metadata={
                "dead_ends_fixed": len(analysis.dead_ends),
                "unreachable_removed": len(analysis.unreachable_steps),
                "orphaned_choices_cleaned": len(analysis.orphaned_choices),
                "optimization_type": "comprehensive"
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Branch pruning failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


def _build_step_graph(adventure: AdventureGame) -> Dict[str, Set[str]]:
    """Build a graph representing step connections."""
    
    graph = {}
    
    for step_id, step in adventure.steps.items():
        connections = set()
        
        for choice in step.choices:
            if choice.target.startswith("STEP_"):
                target_step = choice.target.replace("STEP_", "")
                connections.add(target_step)
            # Endings are terminal nodes
            elif choice.target.startswith("ENDING_"):
                connections.add(choice.target)
        
        graph[step_id] = connections
    
    return graph


def _find_reachable_steps(graph: Dict[str, Set[str]], start_step: str) -> Set[str]:
    """Find all steps reachable from the start step."""
    
    visited = set()
    to_visit = {start_step}
    
    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        
        visited.add(current)
        
        # Add connected steps (only actual steps, not endings)
        if current in graph:
            for target in graph[current]:
                if target.startswith("STEP_") or target.isdigit():
                    target_clean = target.replace("STEP_", "") if target.startswith("STEP_") else target
                    if target_clean not in visited:
                        to_visit.add(target_clean)
    
    return visited


def _find_dead_ends(adventure: AdventureGame, graph: Dict[str, Set[str]]) -> List[str]:
    """Find steps that don't lead to any endings."""
    
    dead_ends = []
    
    for step_id, connections in graph.items():
        if not connections:
            # Step has no choices - this is a dead end
            dead_ends.append(step_id)
        else:
            # Check if any path from this step leads to an ending
            if not _has_path_to_ending(step_id, graph, set()):
                dead_ends.append(step_id)
    
    return dead_ends


def _has_path_to_ending(step_id: str, graph: Dict[str, Set[str]], visited: Set[str]) -> bool:
    """Check if a step has any path to an ending."""
    
    if step_id in visited:
        return False  # Circular reference
    
    visited.add(step_id)
    
    if step_id not in graph:
        return False
    
    connections = graph[step_id]
    
    for target in connections:
        if target.startswith("ENDING_"):
            return True
        elif target.startswith("STEP_") or target.isdigit():
            target_clean = target.replace("STEP_", "") if target.startswith("STEP_") else target
            if _has_path_to_ending(target_clean, graph, visited.copy()):
                return True
    
    return False


def _find_orphaned_choices(adventure: AdventureGame, graph: Dict[str, Set[str]]) -> List[Tuple[str, int]]:
    """Find choices that point to non-existent steps."""
    
    orphaned = []
    all_steps = set(adventure.steps.keys())
    all_endings = set()
    
    # Collect all valid ending targets
    for ending_key in adventure.endings.keys():
        all_endings.add(f"ENDING_{ending_key.upper()}")
    
    # Add standard endings
    all_endings.update(["ENDING_SUCCESS", "ENDING_FAILURE", "ENDING_NEUTRAL"])
    
    for step_id, step in adventure.steps.items():
        for i, choice in enumerate(step.choices):
            if choice.target.startswith("STEP_"):
                target_step = choice.target.replace("STEP_", "")
                if target_step not in all_steps:
                    orphaned.append((step_id, i))
            elif choice.target.startswith("ENDING_"):
                if choice.target not in all_endings:
                    orphaned.append((step_id, i))
    
    return orphaned


def _analyze_ending_distribution(adventure: AdventureGame, graph: Dict[str, Set[str]]) -> Dict[str, int]:
    """Analyze how many paths lead to each ending."""
    
    distribution = {}
    
    # Count paths to each ending
    for step_id in graph:
        ending_paths = _find_ending_paths(step_id, graph, set())
        for ending in ending_paths:
            distribution[ending] = distribution.get(ending, 0) + 1
    
    return distribution


def _find_ending_paths(step_id: str, graph: Dict[str, Set[str]], visited: Set[str]) -> Set[str]:
    """Find all endings reachable from a step."""
    
    if step_id in visited:
        return set()
    
    visited.add(step_id)
    endings = set()
    
    if step_id not in graph:
        return endings
    
    for target in graph[step_id]:
        if target.startswith("ENDING_"):
            endings.add(target)
        elif target.startswith("STEP_") or target.isdigit():
            target_clean = target.replace("STEP_", "") if target.startswith("STEP_") else target
            endings.update(_find_ending_paths(target_clean, graph, visited.copy()))
    
    return endings


def _calculate_path_lengths(graph: Dict[str, Set[str]], start_step: str) -> Dict[str, int]:
    """Calculate shortest path lengths from start to each step."""
    
    distances = {start_step: 0}
    queue = [(start_step, 0)]
    
    while queue:
        current_step, current_distance = queue.pop(0)
        
        if current_step not in graph:
            continue
        
        for target in graph[current_step]:
            if target.startswith("STEP_") or target.isdigit():
                target_clean = target.replace("STEP_", "") if target.startswith("STEP_") else target
                new_distance = current_distance + 1
                
                if target_clean not in distances or distances[target_clean] > new_distance:
                    distances[target_clean] = new_distance
                    queue.append((target_clean, new_distance))
    
    return distances


def _calculate_branching_factors(adventure: AdventureGame) -> Dict[str, int]:
    """Calculate branching factor for each step."""
    
    factors = {}
    
    for step_id, step in adventure.steps.items():
        factors[step_id] = len(step.choices)
    
    return factors


def _find_critical_path(graph: Dict[str, Set[str]], start_step: str) -> List[str]:
    """Find the critical path (longest path without branching)."""
    
    path = [start_step]
    current = start_step
    
    while current in graph and len(graph[current]) == 1:
        next_step = list(graph[current])[0]
        if next_step.startswith("STEP_") or next_step.isdigit():
            next_clean = next_step.replace("STEP_", "") if next_step.startswith("STEP_") else next_step
            if next_clean not in path:  # Avoid cycles
                path.append(next_clean)
                current = next_clean
            else:
                break
        else:
            break
    
    return path


async def _analyze_adventure_structure(adventure: AdventureGame, deps: BranchDependencies) -> BranchAnalysis:
    """Perform comprehensive structure analysis."""
    
    analysis = BranchAnalysis()
    
    # Build step graph
    step_graph = _build_step_graph(adventure)
    
    # Find reachable steps
    reachable_steps = _find_reachable_steps(step_graph, "1")
    all_steps = set(adventure.steps.keys())
    analysis.unreachable_steps = list(all_steps - reachable_steps)
    
    # Find dead ends
    analysis.dead_ends = _find_dead_ends(adventure, step_graph)
    
    # Find orphaned choices
    analysis.orphaned_choices = _find_orphaned_choices(adventure, step_graph)
    
    # Analyze ending distribution
    analysis.ending_distribution = _analyze_ending_distribution(adventure, step_graph)
    
    # Calculate metrics
    analysis.path_lengths = _calculate_path_lengths(step_graph, "1")
    analysis.branching_factor = _calculate_branching_factors(adventure)
    analysis.critical_path_steps = _find_critical_path(step_graph, "1")
    
    return analysis


async def _remove_unreachable_steps(adventure: AdventureGame, analysis: BranchAnalysis) -> AdventureGame:
    """Remove steps that can't be reached from the start."""
    
    if not analysis.unreachable_steps:
        return adventure
    
    # Create new steps dict without unreachable steps
    reachable_steps = {
        step_id: step for step_id, step in adventure.steps.items()
        if step_id not in analysis.unreachable_steps
    }
    
    return adventure.model_copy(update={"steps": reachable_steps})


async def _fix_dead_ends(adventure: AdventureGame, analysis: BranchAnalysis) -> AdventureGame:
    """Fix dead end steps by adding appropriate choices."""
    
    if not analysis.dead_ends:
        return adventure
    
    fixed_steps = adventure.steps.copy()
    
    for dead_end_id in analysis.dead_ends:
        if dead_end_id not in fixed_steps:
            continue
        
        step = fixed_steps[dead_end_id]
        
        # If step has no choices, add some
        if not step.choices:
            new_choices = [
                Choice(
                    label=ChoiceLabel.A,
                    description="Continue your journey",
                    target="ENDING_SUCCESS",
                    conditions=[],
                    consequences=[]
                ),
                Choice(
                    label=ChoiceLabel.B,
                    description="Reconsider your approach",
                    target="ENDING_NEUTRAL",
                    conditions=[],
                    consequences=[]
                )
            ]
            
            fixed_steps[dead_end_id] = step.model_copy(update={"choices": new_choices})
    
    return adventure.model_copy(update={"steps": fixed_steps})


async def _remove_orphaned_choices(adventure: AdventureGame, analysis: BranchAnalysis) -> AdventureGame:
    """Remove choices that point to non-existent targets."""
    
    if not analysis.orphaned_choices:
        return adventure
    
    fixed_steps = adventure.steps.copy()
    
    # Group orphaned choices by step
    orphaned_by_step = {}
    for step_id, choice_index in analysis.orphaned_choices:
        if step_id not in orphaned_by_step:
            orphaned_by_step[step_id] = []
        orphaned_by_step[step_id].append(choice_index)
    
    # Remove orphaned choices (in reverse order to maintain indices)
    for step_id, choice_indices in orphaned_by_step.items():
        if step_id not in fixed_steps:
            continue
        
        step = fixed_steps[step_id]
        new_choices = step.choices.copy()
        
        # Remove in reverse order
        for choice_index in sorted(choice_indices, reverse=True):
            if 0 <= choice_index < len(new_choices):
                new_choices.pop(choice_index)
        
        # Ensure step still has at least one choice
        if not new_choices:
            new_choices = [
                Choice(
                    label=ChoiceLabel.A,
                    description="Continue",
                    target="ENDING_NEUTRAL",
                    conditions=[],
                    consequences=[]
                )
            ]
        
        fixed_steps[step_id] = step.model_copy(update={"choices": new_choices})
    
    return adventure.model_copy(update={"steps": fixed_steps})


async def _balance_ending_distribution(adventure: AdventureGame, analysis: BranchAnalysis) -> AdventureGame:
    """Balance the distribution of paths leading to different endings."""
    
    distribution = analysis.ending_distribution
    
    if not distribution:
        return adventure
    
    # Calculate target distribution
    total_paths = sum(distribution.values())
    target_success_ratio = 0.4  # 40% success paths
    target_failure_ratio = 0.35  # 35% failure paths
    target_neutral_ratio = 0.25  # 25% neutral paths
    
    current_success = distribution.get("ENDING_SUCCESS", 0) / total_paths if total_paths > 0 else 0
    current_failure = distribution.get("ENDING_FAILURE", 0) / total_paths if total_paths > 0 else 0
    
    # If distribution is severely imbalanced, adjust some choice targets
    if current_success < 0.2 or current_success > 0.7:
        # Find steps to adjust
        return await _adjust_choice_targets(adventure, analysis, target_success_ratio)
    
    return adventure


async def _adjust_choice_targets(adventure: AdventureGame, analysis: BranchAnalysis, target_ratio: float) -> AdventureGame:
    """Adjust choice targets to improve ending distribution."""
    
    # This is a simplified version - in practice, you'd want more sophisticated logic
    adjusted_steps = adventure.steps.copy()
    
    # Find steps with multiple choices leading to the same ending type
    for step_id, step in adjusted_steps.items():
        ending_targets = [choice.target for choice in step.choices if choice.target.startswith("ENDING_")]
        
        # If all choices lead to failure, change one to success
        if len(ending_targets) > 1 and all(target == "ENDING_FAILURE" for target in ending_targets):
            # Change the first choice to success
            new_choices = step.choices.copy()
            new_choices[0] = new_choices[0].model_copy(update={"target": "ENDING_SUCCESS"})
            adjusted_steps[step_id] = step.model_copy(update={"choices": new_choices})
    
    return adventure.model_copy(update={"steps": adjusted_steps})


async def _optimize_path_lengths(adventure: AdventureGame, analysis: BranchAnalysis) -> AdventureGame:
    """Optimize path lengths to avoid very short or very long paths."""
    
    path_lengths = analysis.path_lengths
    
    # Find very short paths (less than 3 steps)
    short_paths = [step_id for step_id, length in path_lengths.items() if length < 3]
    
    # Find very long paths (more than 15 steps)
    long_paths = [step_id for step_id, length in path_lengths.items() if length > 15]
    
    if not short_paths and not long_paths:
        return adventure
    
    # For now, just return the adventure - full optimization would require complex restructuring
    return adventure


def _generate_improvement_report(original: BranchAnalysis, final: BranchAnalysis) -> Dict[str, int]:
    """Generate a report of improvements made."""
    
    return {
        "dead_ends_removed": len(original.dead_ends) - len(final.dead_ends),
        "unreachable_steps_removed": len(original.unreachable_steps) - len(final.unreachable_steps),
        "orphaned_choices_fixed": len(original.orphaned_choices) - len(final.orphaned_choices),
        "average_path_length_before": sum(original.path_lengths.values()) / len(original.path_lengths) if original.path_lengths else 0,
        "average_path_length_after": sum(final.path_lengths.values()) / len(final.path_lengths) if final.path_lengths else 0,
        "critical_path_length_before": len(original.critical_path_steps),
        "critical_path_length_after": len(final.critical_path_steps)
    }


async def generate_branch_report(adventure: AdventureGame) -> str:
    """
    Generate a comprehensive branch analysis report.
    
    Args:
        adventure: Adventure to analyze
        
    Returns:
        Formatted branch analysis report
    """
    deps = BranchDependencies()
    analysis = await _analyze_adventure_structure(adventure, deps)
    
    lines = ["=== Branch Structure Analysis ===", ""]
    
    # Overview
    lines.append(f"Total Steps: {len(adventure.steps)}")
    lines.append(f"Reachable Steps: {len(adventure.steps) - len(analysis.unreachable_steps)}")
    lines.append(f"Dead Ends: {len(analysis.dead_ends)}")
    lines.append(f"Orphaned Choices: {len(analysis.orphaned_choices)}")
    lines.append("")
    
    # Path Analysis
    if analysis.path_lengths:
        avg_length = sum(analysis.path_lengths.values()) / len(analysis.path_lengths)
        max_length = max(analysis.path_lengths.values())
        min_length = min(analysis.path_lengths.values())
        
        lines.append("Path Length Analysis:")
        lines.append(f"  Average: {avg_length:.1f} steps")
        lines.append(f"  Range: {min_length} - {max_length} steps")
        lines.append(f"  Critical Path: {len(analysis.critical_path_steps)} steps")
        lines.append("")
    
    # Ending Distribution
    if analysis.ending_distribution:
        lines.append("Ending Distribution:")
        total = sum(analysis.ending_distribution.values())
        for ending, count in analysis.ending_distribution.items():
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"  {ending}: {count} paths ({percentage:.1f}%)")
        lines.append("")
    
    # Issues
    if analysis.dead_ends:
        lines.append("Dead Ends Found:")
        for dead_end in analysis.dead_ends:
            lines.append(f"  • Step {dead_end}")
        lines.append("")
    
    if analysis.unreachable_steps:
        lines.append("Unreachable Steps:")
        for step in analysis.unreachable_steps:
            lines.append(f"  • Step {step}")
        lines.append("")
    
    # Recommendations
    lines.append("Recommendations:")
    if analysis.dead_ends:
        lines.append("  • Fix dead end steps by adding choices leading to endings")
    if analysis.unreachable_steps:
        lines.append("  • Remove unreachable steps or add paths to reach them")
    if analysis.orphaned_choices:
        lines.append("  • Fix orphaned choices pointing to non-existent targets")
    if not analysis.dead_ends and not analysis.unreachable_steps and not analysis.orphaned_choices:
        lines.append("  • Branch structure looks good!")
    
    return "\n".join(lines)


async def visualize_story_flow(adventure: AdventureGame) -> str:
    """
    Generate a text-based visualization of story flow.
    
    Args:
        adventure: Adventure to visualize
        
    Returns:
        ASCII art representation of story flow
    """
    lines = ["Story Flow Visualization", "=" * 25, ""]
    
    # Build graph
    graph = _build_step_graph(adventure)
    
    # Start from step 1
    lines.append("START → Step 1")
    
    def visualize_step(step_id: str, depth: int = 1, visited: Set[str] = None) -> List[str]:
        if visited is None:
            visited = set()
        
        if step_id in visited or depth > 10:  # Prevent infinite loops and excessive depth
            return [f"{'  ' * depth}└─ (already visited or max depth)"]
        
        visited.add(step_id)
        step_lines = []
        
        if step_id in adventure.steps:
            step = adventure.steps[step_id]
            for i, choice in enumerate(step.choices):
                choice_symbol = "├─" if i < len(step.choices) - 1 else "└─"
                indent = "  " * depth
                
                if choice.target.startswith("STEP_"):
                    target_step = choice.target.replace("STEP_", "")
                    step_lines.append(f"{indent}{choice_symbol} {choice.label.value}) {choice.description[:40]}...")
                    step_lines.append(f"{indent}   └─ Step {target_step}")
                    step_lines.extend(visualize_step(target_step, depth + 2, visited.copy()))
                else:
                    step_lines.append(f"{indent}{choice_symbol} {choice.label.value}) {choice.description[:40]}...")
                    step_lines.append(f"{indent}   └─ {choice.target}")
        
        return step_lines
    
    lines.extend(visualize_step("1"))
    
    return "\n".join(lines)