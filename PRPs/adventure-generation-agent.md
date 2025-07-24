name: "Adventure Generation Agent: AI-Powered .adv File Creator"
description: |

## Purpose
Create a production-ready Pydantic AI agent system that generates complete, balanced .adv adventure files from author style templates and story content files. The agent will include 10 specialized tools for storyline generation, validation, optimization, and quality assurance, with a modern CLI interface supporting batch processing and visualization.

## Core Principles
1. **Context is King**: Comprehensive understanding of .adv format and narrative structure
2. **Validation Loops**: Multiple quality gates with self-correction capabilities
3. **Modular Architecture**: Clean separation of concerns following CLAUDE.md patterns
4. **Type Safety**: Leverage Pydantic AI's structured outputs and validation
5. **Modern Tooling**: Use uv, Typer, and 2025 Python best practices

---

## Goal
Build a sophisticated multi-tool AI agent that transforms author personas and story outlines into fully playable .adv adventure files compatible with the existing JavaScript CYOA game engine, with comprehensive quality assurance and optimization features.

## Why
- **Business Value**: Automates the complex, time-intensive process of writing branching narrative adventures
- **Integration**: Seamlessly works with existing CYOA game engine without manual editing
- **Quality**: Ensures narrative coherence, character consistency, and balanced gameplay through AI-powered analysis
- **Scalability**: Enables rapid creation of multiple adventures from different author/story combinations

## What
A CLI-based Python application featuring:
- Primary Adventure Generation Agent with 10 specialized tools
- Support for .author and .story input file formats
- Complete .adv file generation with proper formatting
- Real-time validation and optimization during generation
- Batch processing capabilities for multiple combinations
- Flow visualization for debugging complex narratives
- Streaming CLI interface with progress feedback

### Success Criteria
- [ ] Agent generates syntactically valid .adv files that load in the JavaScript game engine
- [ ] All 10 agent tools function correctly with proper error handling
- [ ] Generated adventures maintain narrative coherence and character consistency
- [ ] Branch balancing prevents dead ends and ensures replayability
- [ ] CLI supports all specified modes (single, batch, validate, visualize)
- [ ] Comprehensive test suite covers all functionality
- [ ] Code follows CLAUDE.md patterns and passes all quality gates

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/agents/
  why: Core agent creation patterns, dependency injection, tool registration
  
- url: https://ai.pydantic.dev/tools/
  why: Function tools, validation, structured outputs, error handling patterns
  
- url: https://ai.pydantic.dev/multi-agent-applications/
  why: Agent composition patterns, though this is single-agent with multiple tools
  
- url: https://ai.pydantic.dev/output/
  why: Structured output validation, custom output types, streaming responses
  
- file: examples/Terry_Pratchett.author
  why: Author persona format and structure for input parsing
  
- file: examples/The_Color_Of_Magic_CYOA.story
  why: Story requirements format and narrative structure expectations
  
- file: examples/demo.adv
  why: Target .adv file format with all required sections and syntax
  
- file: src/fileParser.js
  why: Complete .adv parsing logic showing exact format requirements and validation rules
  
- file: CLAUDE.md
  why: Project coding standards, module organization, testing patterns
  
- url: https://typer.tiangolo.com/
  why: Modern CLI framework patterns for 2025, better than argparse
  
- url: https://docs.astral.sh/uv/guides/projects/
  why: Modern Python project setup with uv package manager
```

### Current Codebase tree
```bash
.
├── examples/
│   ├── Terry_Pratchett.author          # Author persona template
│   ├── The_Color_Of_Magic_CYOA.story   # Story requirements template
│   ├── George_Lucas.author             # Star Wars author style
│   ├── BlackHawks_TroublesInHyperspace_CYOA.story  # Star Wars story
│   ├── demo.adv                        # Example .adv file
│   ├── BlackHawks_TroublesInHyperspace.adv         # Complex .adv example
│   └── ...
├── src/
│   ├── fileParser.js                   # JavaScript .adv parser (reference)
│   └── ...
├── CLAUDE.md                          # Project coding standards
├── INITIAL.md                         # Feature requirements
└── PRPs/
    └── templates/
        └── prp_base.md
```

### Desired Codebase tree with files to be added
```bash
.
├── adventure_agent/                    # Main package
│   ├── __init__.py                    # Package init
│   ├── agent.py                       # Main Adventure Generation Agent
│   ├── models.py                      # Pydantic data models
│   ├── tools/                         # Agent tools package
│   │   ├── __init__.py
│   │   ├── storyline_generator.py     # Core narrative generation
│   │   ├── adv_validator.py           # Format validation
│   │   ├── branch_pruner.py           # Dead end removal
│   │   ├── character_tracker.py       # Character consistency
│   │   ├── coherence_analyzer.py      # Plot logic validation
│   │   ├── inventory_integrator.py    # Game mechanics generation
│   │   ├── ending_optimizer.py        # Outcome balancing
│   │   ├── choice_analyzer.py         # Impact verification
│   │   ├── flow_visualizer.py         # Story mapping
│   │   └── replayability_scorer.py    # Replay analysis
│   ├── parsers/                       # Input/output handling
│   │   ├── __init__.py
│   │   ├── author_parser.py           # .author file parsing
│   │   ├── story_parser.py            # .story file parsing
│   │   └── adv_generator.py           # .adv file generation
│   └── cli.py                         # Typer-based CLI interface
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── test_agent.py                  # Agent integration tests
│   ├── test_tools/                    # Tool-specific tests
│   │   ├── __init__.py
│   │   ├── test_storyline_generator.py
│   │   ├── test_adv_validator.py
│   │   └── ...
│   ├── test_parsers/                  # Parser tests
│   │   ├── __init__.py
│   │   ├── test_author_parser.py
│   │   ├── test_story_parser.py
│   │   └── test_adv_generator.py
│   ├── test_cli.py                    # CLI tests
│   └── fixtures/                      # Test data
│       ├── test_author.author
│       ├── test_story.story
│       └── expected_output.adv
├── pyproject.toml                     # uv project configuration
├── README.md                          # Updated documentation
└── agent.py                           # Entry point script
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: .adv format is very strict - fileParser.js shows exact requirements
# - Section headers must be [SECTION_NAME] and [/SECTION_NAME] for closing
# - STEP_X sections require [NARRATIVE] and [CHOICES] subsections
# - Choice format: "A) Description → TARGET {conditions; consequences}"
# - Must include GAME_NAME, MAIN_MENU, at least one STEP_X, and ENDING_X sections

# CRITICAL: Pydantic AI structured output validation
# - Use output_type parameter for structured responses
# - ModelRetry exception for self-correction loops
# - RunContext for accessing dependencies and conversation history

# CRITICAL: Large content generation challenges
# - Story generation can hit token limits with complex narratives
# - Need chunking strategy for large adventures
# - Character tracking across many story branches requires careful state management

# CRITICAL: uv project setup (2025 best practices)
# - Use pyproject.toml instead of requirements.txt
# - uv.lock file should be committed for reproducible builds
# - uv run automatically manages environment and dependencies

# GOTCHA: Typer CLI async support
# - Use typer.run() for sync functions, asyncio.run() for async
# - Streaming output requires careful handling of async iterators
```

## Implementation Blueprint

### Data models and structure

Create the core data models first to ensure type safety and consistency.
```python
# adventure_agent/models.py - Core Pydantic models
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from enum import Enum

class AuthorPersona(BaseModel):
    voice_and_tone: List[str]
    narrative_style: List[str] 
    world_elements: List[str]
    character_development: List[str]
    themes: List[str]

class StoryRequirements(BaseModel):
    setting: Dict[str, str]
    main_character: Dict[str, str]
    plot: str
    npcs: List[Dict[str, str]]
    branches: List[Dict[str, str]]
    technical_requirements: Dict[str, Union[str, int, List[str]]]

class Choice(BaseModel):
    label: str  # A, B, C, D
    description: str
    target: str  # STEP_X or ENDING_X
    conditions: List[str] = []
    consequences: List[str] = []

class StoryStep(BaseModel):
    step_id: str  # "1", "2", etc.
    narrative: str
    choices: List[Choice]

class AdventureGame(BaseModel):
    game_name: str
    ask_for_name: bool = False
    main_menu: List[str]
    steps: Dict[str, StoryStep]
    endings: Dict[str, str]  # success, failure, neutral
    inventory: Dict[str, Union[str, int]] = {}
    stats: Dict[str, Union[str, int]] = {}
    variables: Dict[str, Union[str, int]] = {}
```

### List of tasks to be completed to fulfill the PRP in the order they should be completed

```yaml
Task 1: Project Setup and Core Models
CREATE pyproject.toml:
  - Use uv init for project structure
  - Add pydantic-ai, typer, pytest dependencies  
  - Configure build system and Python version requirements

CREATE adventure_agent/models.py:
  - MIRROR patterns from CLAUDE.md for Pydantic models
  - Define AuthorPersona, StoryRequirements, AdventureGame models
  - Include comprehensive validation and field descriptions

Task 2: Input File Parsers
CREATE adventure_agent/parsers/author_parser.py:
  - Parse .author files into AuthorPersona models
  - Handle markdown sections and bullet points
  - PATTERN: Use existing examples/Terry_Pratchett.author structure

CREATE adventure_agent/parsers/story_parser.py:
  - Parse .story files into StoryRequirements models
  - Extract technical requirements and story elements
  - PATTERN: Follow examples/The_Color_Of_Magic_CYOA.story format

CREATE adventure_agent/parsers/adv_generator.py:
  - Generate .adv format from AdventureGame models
  - CRITICAL: Exactly match src/fileParser.js expected format
  - Include proper section headers and choice syntax

Task 3: Core Agent Tools (Phase 1 - Generation)
CREATE adventure_agent/tools/storyline_generator.py:
  - Main narrative generation from author + story inputs
  - Handle branching logic and step progression
  - GOTCHA: Manage token limits with chunking strategy

CREATE adventure_agent/tools/character_tracker.py:
  - Maintain character consistency across branches
  - Track NPC appearances and dialogue patterns
  - PATTERN: Use RunContext for state management

CREATE adventure_agent/tools/inventory_integrator.py:
  - Generate appropriate items and stats based on story
  - Integrate game mechanics into narrative choices
  - Reference existing .adv examples for patterns

Task 4: Validation and Optimization Tools (Phase 2)
CREATE adventure_agent/tools/adv_validator.py:
  - Validate generated .adv syntax against fileParser.js rules
  - Check all required sections and proper formatting
  - CRITICAL: Use ModelRetry for self-correction

CREATE adventure_agent/tools/branch_pruner.py:
  - Identify and fix dead ends in story flow
  - Ensure all paths lead to proper endings
  - Optimize story tree structure

CREATE adventure_agent/tools/coherence_analyzer.py:
  - Validate plot logic and narrative flow
  - Check for continuity errors and inconsistencies
  - Score narrative quality metrics

Task 5: Advanced Analysis Tools (Phase 3)
CREATE adventure_agent/tools/ending_optimizer.py:
  - Balance distribution of success/failure/neutral outcomes
  - Analyze player choice consequences
  - Ensure meaningful differentiation between endings

CREATE adventure_agent/tools/choice_analyzer.py:
  - Verify choices lead to meaningfully different outcomes
  - Validate choice descriptions and consequences
  - Score choice impact and player agency

CREATE adventure_agent/tools/replayability_scorer.py:
  - Analyze variation between different playthroughs
  - Calculate branching complexity and uniqueness
  - Generate replayability metrics

CREATE adventure_agent/tools/flow_visualizer.py:
  - Generate visual story maps for debugging
  - Create ASCII or graphical flow charts
  - Export to common formats (PNG, SVG, DOT)

Task 6: Main Agent Integration
CREATE adventure_agent/agent.py:
  - PATTERN: Follow Pydantic AI agent creation from documentation
  - Register all 10 tools with proper dependencies
  - Configure structured output and error handling
  - Implement streaming for long-running generation

Task 7: CLI Interface
CREATE adventure_agent/cli.py:
  - PATTERN: Use Typer for modern CLI (better than argparse in 2025)
  - Implement all CLI modes: single, batch, validate, visualize
  - Add streaming output and progress indicators
  - GOTCHA: Handle async agent calls properly with Typer

CREATE agent.py (entry point):
  - Simple script to run CLI
  - Follow CLAUDE.md patterns for entry points

Task 8: Comprehensive Testing
CREATE tests/test_agent.py:
  - Integration tests for full agent workflow
  - Test with real .author/.story examples
  - Validate generated .adv files load in game engine

CREATE tests for each tool:
  - Unit tests for all 10 tools
  - Mock external dependencies appropriately
  - Test error conditions and self-correction

CREATE tests/test_cli.py:
  - Test all CLI modes and options
  - Validate streaming output and error handling
  - Test batch processing functionality

Task 9: Documentation and Polish
UPDATE README.md:
  - Installation and usage instructions
  - Examples of .author/.story file formats
  - CLI reference and workflow documentation

CREATE example files:
  - Additional .author/.story combinations for testing
  - Generated .adv examples showing quality
```

### Per task pseudocode as needed

```python
# Task 3: Storyline Generator Tool
@agent.tool
async def generate_storyline(
    ctx: RunContext[None], 
    author: AuthorPersona, 
    story: StoryRequirements
) -> AdventureGame:
    """Transform author style and story into branching narrative adventure."""
    
    # PATTERN: Use structured output for complex generation
    generation_request = f"""
    Create a {story.technical_requirements.get('length', 10)}-step adventure 
    in the style of {author.voice_and_tone} with {story.plot}.
    Include {len(story.branches)} major branching paths.
    """
    
    # GOTCHA: Handle large content with chunking
    if story.technical_requirements.get('length', 10) > 20:
        # Generate in chunks to avoid token limits
        chunks = await generate_in_chunks(generation_request, chunk_size=5)
        adventure = await combine_chunks(chunks)
    else:
        adventure = await generate_single_pass(generation_request)
    
    # CRITICAL: Validate structure before returning
    if not validate_adventure_structure(adventure):
        raise ModelRetry("Generated adventure has structural issues")
    
    return adventure

# Task 4: ADV Validator Tool  
@agent.tool
async def validate_adv_format(
    ctx: RunContext[None], 
    adventure: AdventureGame
) -> ValidationResult:
    """Validate .adv format against JavaScript parser requirements."""
    
    # CRITICAL: Check all required sections from fileParser.js
    errors = []
    
    # Required sections validation
    if not adventure.game_name:
        errors.append("Missing [GAME_NAME] section")
    
    if not adventure.main_menu:
        errors.append("Missing [MAIN_MENU] section")
        
    if not adventure.steps:
        errors.append("No [STEP_X] sections found")
    
    # Choice format validation  
    for step in adventure.steps.values():
        for choice in step.choices:
            if not re.match(r'^[A-D]\)', choice.label):
                errors.append(f"Invalid choice label: {choice.label}")
            
            if choice.target not in adventure.steps and \
               not choice.target.startswith('ENDING_'):
                errors.append(f"Invalid choice target: {choice.target}")
    
    # PATTERN: Use ModelRetry for self-correction
    if errors:
        error_summary = "\n".join(errors)
        raise ModelRetry(f"Validation errors found:\n{error_summary}")
    
    return ValidationResult(valid=True, errors=[])
```

### Integration Points
```yaml
FILE_FORMATS:
  - input: ".author and .story files in examples/ directory"
  - output: ".adv files compatible with src/fileParser.js"
  - validation: "Generated files must load without errors in JavaScript engine"
  
ENVIRONMENT:
  - python: "Use uv for environment management as specified in CLAUDE.md"
  - dependencies: "All in pyproject.toml, no requirements.txt"
  - testing: "pytest with fixtures matching examples/ structure"
  
CLI_INTEGRATION:
  - pattern: "Follow examples/cli.py structure if available"
  - streaming: "Real-time output for long-running generations"
  - error_handling: "Graceful degradation with helpful error messages"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
uv run ruff check adventure_agent/ --fix  # Auto-fix what's possible
uv run mypy adventure_agent/               # Type checking

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests for each new feature/file/function
```python
# CREATE comprehensive test suite following CLAUDE.md patterns
def test_author_parser_happy_path():
    """Basic author file parsing works"""
    with open('examples/Terry_Pratchett.author', 'r') as f:
        content = f.read()
    
    persona = parse_author_file(content)
    assert isinstance(persona, AuthorPersona)
    assert len(persona.voice_and_tone) > 0
    assert "witty" in " ".join(persona.voice_and_tone).lower()

def test_storyline_generation_with_constraints():
    """Generated stories respect length and branch constraints"""
    author = AuthorPersona(voice_and_tone=["humorous", "witty"])
    story = StoryRequirements(
        technical_requirements={"length": 5, "branches": 2}
    )
    
    adventure = await generate_storyline_sync(author, story)
    assert len(adventure.steps) == 5
    assert count_unique_branches(adventure) >= 2

def test_adv_validator_catches_format_errors():
    """Validator identifies missing required sections"""
    invalid_adventure = AdventureGame(
        game_name="",  # Invalid - empty name
        main_menu=[],  # Invalid - empty menu
        steps={},      # Invalid - no steps
        endings={}
    )
    
    with pytest.raises(ValidationError):
        validate_adv_format_sync(invalid_adventure)
```

```bash
# Run and iterate until passing:
uv run pytest tests/ -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test with Real Game Engine
```bash
# Test generated .adv files actually work with JavaScript engine
uv run python -m adventure_agent.cli \
  --author examples/Terry_Pratchett.author \
  --story examples/The_Color_Of_Magic_CYOA.story \
  --output test_output.adv

# Validate output loads in JavaScript game
cd src && node -e "
const fs = require('fs');
const { parseFile } = require('./fileParser.js');
const content = fs.readFileSync('../test_output.adv', 'utf8');
try {
  const game = parseFile(content);
  console.log('✅ Generated .adv file is valid');
  console.log('Game name:', game.gameName);
  console.log('Steps:', Object.keys(game.steps).length);
} catch (error) {
  console.error('❌ Generated .adv file is invalid:', error.message);
  process.exit(1);
}
"

# Expected: ✅ Generated .adv file is valid
```

### Level 4: CLI Integration Test
```bash
# Test all CLI modes work correctly
uv run python agent.py --help  # Should show Typer-generated help

# Single file generation
uv run python agent.py \
  --author examples/Terry_Pratchett.author \
  --story examples/The_Color_Of_Magic_CYOA.story \
  --output discworld_test.adv

# Batch processing
mkdir -p test_output
uv run python agent.py --batch \
  --author-dir examples/ \
  --story-dir examples/ \
  --output-dir test_output/

# Validation mode
uv run python agent.py --validate examples/demo.adv

# Visualization mode  
uv run python agent.py --visualize \
  --input examples/demo.adv \
  --output flow_chart.png

# Expected: All modes complete successfully with appropriate output
```

## Final validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check adventure_agent/`
- [ ] No type errors: `uv run mypy adventure_agent/`
- [ ] Generated .adv files load successfully in JavaScript game engine
- [ ] All 10 agent tools function correctly with proper validation
- [ ] CLI supports all specified modes with streaming output
- [ ] Batch processing handles multiple author/story combinations
- [ ] Flow visualization generates readable story maps
- [ ] Error handling provides helpful feedback for all failure modes
- [ ] Documentation is complete and accurate

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode story elements - use dynamic generation based on inputs
- ❌ Don't skip .adv format validation - integration with game engine is critical
- ❌ Don't ignore token limits - large stories need chunking strategies  
- ❌ Don't use sync functions in Pydantic AI contexts - agents are async by design
- ❌ Don't create monolithic tools - each should have single responsibility
- ❌ Don't skip character consistency tracking - breaks narrative immersion
- ❌ Don't generate stories without proper ending balance - affects gameplay
- ❌ Don't ignore branch analysis - dead ends ruin player experience

## Quality Score: 9/10

**Confidence Level**: Very High - This PRP provides comprehensive context including:
- ✅ Complete .adv format specification from existing JavaScript parser
- ✅ Real examples of input formats (.author/.story files)  
- ✅ Modern 2025 Python best practices (uv, Typer, Pydantic AI)
- ✅ Detailed implementation blueprint with proper task sequencing
- ✅ Executable validation gates that verify integration with existing game engine
- ✅ Anti-patterns and gotchas from research to prevent common mistakes
- ✅ Modular architecture following CLAUDE.md patterns

**Potential Risk Areas**: Story generation token limits and character consistency across complex branching narratives, but mitigation strategies are included in the implementation plan.