"""
Flow Visualizer Tool for the Adventure Generation Agent.

This tool generates visual story maps for debugging complex narratives,
creates ASCII or graphical flow charts, and exports to common formats.
"""

from typing import Dict, List, Set, Tuple, Optional

from pydantic_ai import Agent, RunContext

from ..models import AdventureGame, ToolResult


class FlowNode:
    """Represents a node in the story flow."""
    
    def __init__(self, node_id: str, node_type: str, label: str, content: str = ""):
        self.node_id = node_id
        self.node_type = node_type  # step, ending, choice
        self.label = label
        self.content = content
        self.connections: List['FlowConnection'] = []
        self.position: Tuple[int, int] = (0, 0)
        self.level = 0


class FlowConnection:
    """Represents a connection between nodes."""
    
    def __init__(self, from_node: str, to_node: str, choice_label: str = "", conditions: List[str] = None):
        self.from_node = from_node
        self.to_node = to_node
        self.choice_label = choice_label
        self.conditions = conditions or []
        self.description = ""


class FlowVisualization:
    """Complete flow visualization data."""
    
    def __init__(self):
        self.nodes: Dict[str, FlowNode] = {}
        self.connections: List[FlowConnection] = []
        self.ascii_diagram: str = ""
        self.dot_graph: str = ""
        self.complexity_score: float = 0.0
        self.max_depth: int = 0


class FlowDependencies:
    """Dependencies for flow visualization."""
    
    def __init__(self):
        self.visualization = FlowVisualization()
        self.max_width = 120  # ASCII diagram width
        self.compact_mode = False


def create_flow_agent() -> Agent[FlowDependencies, FlowVisualization]:
    """Create flow visualization agent."""
    return Agent[FlowDependencies, FlowVisualization](
        'gemini-1.5-flash',
        deps_type=FlowDependencies,
        output_type=FlowVisualization,
        system_prompt=(
            "You are a story flow visualization expert. Create clear, readable "
            "diagrams that help developers understand complex narrative structures, "
            "identify flow issues, and debug branching logic."
        ),
    )


async def visualize_story_flow(
    ctx: RunContext[FlowDependencies],
    adventure: AdventureGame
) -> FlowVisualization:
    """
    Create a comprehensive visualization of the story flow.
    
    Args:
        ctx: Agent context with dependencies
        adventure: Adventure to visualize
        
    Returns:
        FlowVisualization containing all visualization formats
    """
    viz = ctx.deps.visualization
    
    # Build flow graph
    _build_flow_graph(adventure, viz)
    
    # Calculate layout
    _calculate_layout(viz)
    
    # Generate ASCII diagram
    viz.ascii_diagram = _generate_ascii_diagram(viz, ctx.deps.max_width)
    
    # Generate DOT graph
    viz.dot_graph = _generate_dot_graph(viz)
    
    # Calculate complexity metrics
    viz.complexity_score = _calculate_flow_complexity(viz)
    viz.max_depth = _calculate_max_depth(viz)
    
    return viz


async def generate_flow_visualization(adventure: AdventureGame) -> ToolResult:
    """
    Main flow visualization function.
    
    Args:
        adventure: Adventure to visualize
        
    Returns:
        ToolResult with visualization data and diagrams
    """
    try:
        # Set up dependencies
        deps = FlowDependencies()
        
        # Generate comprehensive visualization
        viz = await _generate_visualization_impl(adventure, deps)
        
        # Generate different output formats
        formats = {
            "ascii": viz.ascii_diagram,
            "dot": viz.dot_graph,
            "summary": _generate_flow_summary(viz, adventure)
        }
        
        # Generate analysis insights
        insights = _generate_flow_insights(viz, adventure)
        
        return ToolResult(
            success=True,
            data={
                "visualization": viz,
                "formats": formats,
                "insights": insights,
                "metrics": {
                    "total_nodes": len(viz.nodes),
                    "total_connections": len(viz.connections),
                    "complexity_score": viz.complexity_score,
                    "max_depth": viz.max_depth
                }
            },
            message=f"Flow visualization generated: {len(viz.nodes)} nodes, {len(viz.connections)} connections, complexity {viz.complexity_score:.1f}",
            metadata={
                "node_count": len(viz.nodes),
                "connection_count": len(viz.connections),
                "complexity": viz.complexity_score,
                "max_depth": viz.max_depth
            }
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Flow visualization failed: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )


def _build_flow_graph(adventure: AdventureGame, viz: FlowVisualization):
    """Build the flow graph from the adventure structure."""
    
    # Add step nodes
    for step_id, step in adventure.steps.items():
        node = FlowNode(
            node_id=f"STEP_{step_id}",
            node_type="step",
            label=f"Step {step_id}",
            content=step.narrative[:100] + "..." if len(step.narrative) > 100 else step.narrative
        )
        viz.nodes[node.node_id] = node
    
    # Add ending nodes
    for ending_key, ending_text in adventure.endings.items():
        node_id = f"ENDING_{ending_key.upper()}"
        node = FlowNode(
            node_id=node_id,
            node_type="ending",
            label=f"Ending: {ending_key.title()}",
            content=ending_text[:100] + "..." if len(ending_text) > 100 else ending_text
        )
        viz.nodes[node_id] = node
    
    # Add connections based on choices
    for step_id, step in adventure.steps.items():
        from_node = f"STEP_{step_id}"
        
        for choice in step.choices:
            connection = FlowConnection(
                from_node=from_node,
                to_node=choice.target,
                choice_label=choice.label.value if choice.label else "",
                conditions=choice.conditions
            )
            connection.description = choice.description
            viz.connections.append(connection)
            
            # Add connection to source node
            if from_node in viz.nodes:
                viz.nodes[from_node].connections.append(connection)


def _calculate_layout(viz: FlowVisualization):
    """Calculate positions for nodes in the visualization."""
    
    if not viz.nodes:
        return
    
    # Start with step 1 if it exists
    start_node = "STEP_1"
    if start_node not in viz.nodes:
        start_node = list(viz.nodes.keys())[0]
    
    # Calculate levels (depth from start)
    visited = set()
    level_nodes = {0: [start_node]}
    current_level = 0
    
    while current_level in level_nodes and level_nodes[current_level]:
        next_level_nodes = []
        
        for node_id in level_nodes[current_level]:
            if node_id in visited:
                continue
            
            visited.add(node_id)
            viz.nodes[node_id].level = current_level
            
            # Find connections to next level
            for connection in viz.connections:
                if connection.from_node == node_id and connection.to_node not in visited:
                    if connection.to_node not in next_level_nodes:
                        next_level_nodes.append(connection.to_node)
        
        if next_level_nodes:
            current_level += 1
            level_nodes[current_level] = next_level_nodes
    
    # Assign positions within levels
    for level, nodes in level_nodes.items():
        for i, node_id in enumerate(nodes):
            if node_id in viz.nodes:
                viz.nodes[node_id].position = (i * 20, level * 10)


def _generate_ascii_diagram(viz: FlowVisualization, max_width: int) -> str:
    """Generate ASCII art diagram of the flow."""
    
    if not viz.nodes:
        return "No nodes to visualize"
    
    lines = ["Story Flow Diagram", "=" * 20, ""]
    
    # Group nodes by level
    levels = {}
    for node in viz.nodes.values():
        level = node.level
        if level not in levels:
            levels[level] = []
        levels[level].append(node)
    
    # Generate level by level
    for level in sorted(levels.keys()):
        nodes = levels[level]
        
        # Level header
        lines.append(f"Level {level}:")
        lines.append("-" * 8)
        
        # Draw nodes
        for node in nodes:
            node_symbol = _get_node_symbol(node.node_type)
            node_line = f"{node_symbol} {node.label}"
            
            if node.content and len(node.content) > 0:
                # Truncate content to fit
                max_content_length = max_width - len(node_line) - 5
                if len(node.content) > max_content_length:
                    content = node.content[:max_content_length-3] + "..."
                else:
                    content = node.content
                node_line += f" | {content}"
            
            lines.append(f"  {node_line}")
            
            # Show connections
            node_connections = [c for c in viz.connections if c.from_node == node.node_id]
            for connection in node_connections:
                choice_info = f"[{connection.choice_label}]" if connection.choice_label else ""
                target_info = connection.to_node.replace("STEP_", "Step ").replace("ENDING_", "End: ")
                
                desc = connection.description[:30] + "..." if len(connection.description) > 30 else connection.description
                
                if choice_info:
                    conn_line = f"    {choice_info} {desc} → {target_info}"
                else:
                    conn_line = f"    {desc} → {target_info}"
                
                lines.append(conn_line)
        
        lines.append("")
    
    return "\n".join(lines)


def _get_node_symbol(node_type: str) -> str:
    """Get ASCII symbol for node type."""
    
    symbols = {
        "step": "●",
        "ending": "◆",
        "choice": "○"
    }
    return symbols.get(node_type, "●")


def _generate_dot_graph(viz: FlowVisualization) -> str:
    """Generate Graphviz DOT format diagram."""
    
    lines = [
        "digraph StoryFlow {",
        "  rankdir=TB;",
        "  node [shape=box, style=rounded];",
        "  edge [fontsize=10];",
        ""
    ]
    
    # Add nodes
    for node in viz.nodes.values():
        node_style = _get_dot_node_style(node.node_type)
        
        # Escape label for DOT format
        label = node.label.replace('"', '\\"')
        if node.content:
            content = node.content[:50].replace('"', '\\"').replace('\n', '\\n')
            label += f"\\n{content}"
        
        lines.append(f'  "{node.node_id}" [label="{label}", {node_style}];')
    
    lines.append("")
    
    # Add connections
    for connection in viz.connections:
        edge_label = ""
        if connection.choice_label:
            edge_label = connection.choice_label
        if connection.description:
            desc = connection.description[:20] + "..." if len(connection.description) > 20 else connection.description
            edge_label += f": {desc}" if edge_label else desc
        
        edge_attr = f'label="{edge_label}"' if edge_label else ""
        
        lines.append(f'  "{connection.from_node}" -> "{connection.to_node}" [{edge_attr}];')
    
    lines.append("}")
    
    return "\n".join(lines)


def _get_dot_node_style(node_type: str) -> str:
    """Get Graphviz DOT style for node type."""
    
    styles = {
        "step": "fillcolor=lightblue, style=filled",
        "ending": "fillcolor=lightcoral, style=filled",
        "choice": "fillcolor=lightgreen, style=filled"
    }
    return styles.get(node_type, "")


def _calculate_flow_complexity(viz: FlowVisualization) -> float:
    """Calculate complexity score for the flow (0-10 scale)."""
    
    if not viz.nodes:
        return 0.0
    
    complexity = 0.0
    
    # Factor 1: Node count
    node_count = len(viz.nodes)
    complexity += min(3.0, node_count * 0.2)
    
    # Factor 2: Connection density
    connection_count = len(viz.connections)
    if node_count > 0:
        density = connection_count / node_count
        complexity += min(3.0, density * 1.5)
    
    # Factor 3: Branching factor
    step_nodes = [n for n in viz.nodes.values() if n.node_type == "step"]
    if step_nodes:
        total_branches = sum(len(node.connections) for node in step_nodes)
        avg_branches = total_branches / len(step_nodes)
        complexity += min(2.0, avg_branches * 0.5)
    
    # Factor 4: Depth
    max_level = max(node.level for node in viz.nodes.values()) if viz.nodes else 0
    complexity += min(2.0, max_level * 0.2)
    
    return min(10.0, complexity)


def _calculate_max_depth(viz: FlowVisualization) -> int:
    """Calculate maximum depth of the flow."""
    
    if not viz.nodes:
        return 0
    
    return max(node.level for node in viz.nodes.values())


async def _generate_visualization_impl(adventure: AdventureGame, deps: FlowDependencies) -> FlowVisualization:
    """Implementation of flow visualization generation."""
    
    viz = FlowVisualization()
    
    # Build the flow graph
    _build_flow_graph(adventure, viz)
    
    # Calculate layout
    _calculate_layout(viz)
    
    # Generate diagrams
    viz.ascii_diagram = _generate_ascii_diagram(viz, deps.max_width)
    viz.dot_graph = _generate_dot_graph(viz)
    
    # Calculate metrics
    viz.complexity_score = _calculate_flow_complexity(viz)
    viz.max_depth = _calculate_max_depth(viz)
    
    return viz


def _generate_flow_summary(viz: FlowVisualization, adventure: AdventureGame) -> str:
    """Generate a text summary of the flow structure."""
    
    lines = ["=== Story Flow Summary ===", ""]
    
    # Basic statistics
    step_count = len([n for n in viz.nodes.values() if n.node_type == "step"])
    ending_count = len([n for n in viz.nodes.values() if n.node_type == "ending"])
    
    lines.append("STRUCTURE:")
    lines.append(f"  Steps: {step_count}")
    lines.append(f"  Endings: {ending_count}")
    lines.append(f"  Connections: {len(viz.connections)}")
    lines.append(f"  Max Depth: {viz.max_depth}")
    lines.append(f"  Complexity: {viz.complexity_score:.1f}/10")
    lines.append("")
    
    # Path analysis
    lines.append("FLOW ANALYSIS:")
    
    # Find start nodes (nodes with no incoming connections)
    incoming_targets = {conn.to_node for conn in viz.connections}
    start_nodes = [node.node_id for node in viz.nodes.values() if node.node_id not in incoming_targets]
    
    if start_nodes:
        lines.append(f"  Entry Points: {len(start_nodes)}")
        for start in start_nodes[:3]:  # Show first 3
            lines.append(f"    - {start}")
    
    # Find end nodes (nodes with no outgoing connections)
    outgoing_sources = {conn.from_node for conn in viz.connections}
    end_nodes = [node.node_id for node in viz.nodes.values() if node.node_id not in outgoing_sources]
    
    if end_nodes:
        lines.append(f"  Terminal Points: {len(end_nodes)}")
        for end in end_nodes[:3]:  # Show first 3
            lines.append(f"    - {end}")
    
    lines.append("")
    
    # Branching analysis
    step_nodes = [n for n in viz.nodes.values() if n.node_type == "step"]
    if step_nodes:
        branch_counts = [len(node.connections) for node in step_nodes]
        avg_branches = sum(branch_counts) / len(branch_counts)
        max_branches = max(branch_counts)
        
        lines.append("BRANCHING:")
        lines.append(f"  Average Choices per Step: {avg_branches:.1f}")
        lines.append(f"  Maximum Choices: {max_branches}")
        
        # Find most complex step
        if max_branches > 0:
            complex_steps = [node for node in step_nodes if len(node.connections) == max_branches]
            if complex_steps:
                lines.append(f"  Most Complex Step: {complex_steps[0].label}")
    
    return "\n".join(lines)


def _generate_flow_insights(viz: FlowVisualization, adventure: AdventureGame) -> List[str]:
    """Generate insights about the flow structure."""
    
    insights = []
    
    # Complexity analysis
    if viz.complexity_score > 8.0:
        insights.append("High complexity flow - may be challenging for players to navigate")
    elif viz.complexity_score < 3.0:
        insights.append("Simple flow structure - consider adding more branching for interest")
    else:
        insights.append("Moderate complexity provides good balance of choice and clarity")
    
    # Depth analysis
    if viz.max_depth > 15:
        insights.append("Very deep story structure - ensure all paths remain engaging")
    elif viz.max_depth < 3:
        insights.append("Shallow story structure - consider extending narrative depth")
    
    # Node distribution
    step_count = len([n for n in viz.nodes.values() if n.node_type == "step"])
    ending_count = len([n for n in viz.nodes.values() if n.node_type == "ending"])
    
    if ending_count == 1:
        insights.append("Single ending limits replayability - consider multiple outcomes")
    elif ending_count > step_count / 2:
        insights.append("High ending-to-step ratio provides good outcome variety")
    
    # Connection analysis
    if len(viz.connections) == 0:
        insights.append("No connections found - story structure may be incomplete")
    elif len(viz.connections) < step_count:
        insights.append("Low connection density - some steps may be isolated")
    
    # Branching patterns
    step_nodes = [n for n in viz.nodes.values() if n.node_type == "step"]
    if step_nodes:
        branch_counts = [len(node.connections) for node in step_nodes]
        if all(count <= 1 for count in branch_counts):
            insights.append("Linear story with no meaningful choices")
        elif any(count > 4 for count in branch_counts):
            insights.append("Some steps have many choices - ensure all are meaningful")
    
    return insights


async def export_to_format(adventure: AdventureGame, format_type: str) -> str:
    """
    Export flow visualization to specific format.
    
    Args:
        adventure: Adventure to visualize
        format_type: Type of export (ascii, dot, mermaid, json)
        
    Returns:
        Exported visualization in requested format
    """
    deps = FlowDependencies()
    viz = await _generate_visualization_impl(adventure, deps)
    
    if format_type.lower() == "ascii":
        return viz.ascii_diagram
    elif format_type.lower() == "dot":
        return viz.dot_graph
    elif format_type.lower() == "mermaid":
        return _generate_mermaid_diagram(viz)
    elif format_type.lower() == "json":
        return _generate_json_export(viz)
    else:
        return f"Unsupported format: {format_type}"


def _generate_mermaid_diagram(viz: FlowVisualization) -> str:
    """Generate Mermaid diagram format."""
    
    lines = ["graph TD"]
    
    # Add nodes
    for node in viz.nodes.values():
        node_shape = _get_mermaid_node_shape(node.node_type)
        node_id = node.node_id.replace("-", "_")
        label = node.label.replace('"', "'")
        
        lines.append(f"  {node_id}{node_shape[0]}{label}{node_shape[1]}")
    
    # Add connections
    for connection in viz.connections:
        from_id = connection.from_node.replace("-", "_")
        to_id = connection.to_node.replace("-", "_")
        
        label = ""
        if connection.choice_label:
            label = connection.choice_label
        if connection.description:
            desc = connection.description[:15] + "..." if len(connection.description) > 15 else connection.description
            label += f": {desc}" if label else desc
        
        if label:
            lines.append(f"  {from_id} -->|{label}| {to_id}")
        else:
            lines.append(f"  {from_id} --> {to_id}")
    
    return "\n".join(lines)


def _get_mermaid_node_shape(node_type: str) -> Tuple[str, str]:
    """Get Mermaid node shape for node type."""
    
    shapes = {
        "step": ("[", "]"),
        "ending": ("((", "))"),
        "choice": ("(", ")")
    }
    return shapes.get(node_type, ("[", "]"))


def _generate_json_export(viz: FlowVisualization) -> str:
    """Generate JSON export of the flow structure."""
    
    import json
    
    export_data = {
        "nodes": [],
        "connections": [],
        "metadata": {
            "complexity_score": viz.complexity_score,
            "max_depth": viz.max_depth,
            "node_count": len(viz.nodes),
            "connection_count": len(viz.connections)
        }
    }
    
    # Export nodes
    for node in viz.nodes.values():
        node_data = {
            "id": node.node_id,
            "type": node.node_type,
            "label": node.label,
            "content": node.content,
            "level": node.level,
            "position": {"x": node.position[0], "y": node.position[1]}
        }
        export_data["nodes"].append(node_data)
    
    # Export connections
    for connection in viz.connections:
        conn_data = {
            "from": connection.from_node,
            "to": connection.to_node,
            "choice_label": connection.choice_label,
            "description": connection.description,
            "conditions": connection.conditions
        }
        export_data["connections"].append(conn_data)
    
    return json.dumps(export_data, indent=2)


async def analyze_flow_bottlenecks(adventure: AdventureGame) -> List[str]:
    """
    Identify potential bottlenecks in the story flow.
    
    Args:
        adventure: Adventure to analyze
        
    Returns:
        List of identified bottlenecks and issues
    """
    deps = FlowDependencies()
    viz = await _generate_visualization_impl(adventure, deps)
    
    bottlenecks = []
    
    # Find nodes with many incoming connections (convergence points)
    incoming_counts = {}
    for connection in viz.connections:
        target = connection.to_node
        incoming_counts[target] = incoming_counts.get(target, 0) + 1
    
    for node_id, count in incoming_counts.items():
        if count > 3:
            bottlenecks.append(f"Convergence bottleneck at {node_id} ({count} incoming paths)")
    
    # Find nodes with many outgoing connections (decision overload)
    outgoing_counts = {}
    for connection in viz.connections:
        source = connection.from_node
        outgoing_counts[source] = outgoing_counts.get(source, 0) + 1
    
    for node_id, count in outgoing_counts.items():
        if count > 5:
            bottlenecks.append(f"Choice overload at {node_id} ({count} choices)")
    
    # Find isolated nodes
    all_connected = set()
    for connection in viz.connections:
        all_connected.add(connection.from_node)
        all_connected.add(connection.to_node)
    
    isolated = [node.node_id for node in viz.nodes.values() if node.node_id not in all_connected]
    for isolated_node in isolated:
        bottlenecks.append(f"Isolated node: {isolated_node}")
    
    # Find very long paths
    if viz.max_depth > 12:
        bottlenecks.append(f"Very deep structure (depth: {viz.max_depth}) may lose player engagement")
    
    if not bottlenecks:
        bottlenecks.append("No significant flow bottlenecks detected")
    
    return bottlenecks