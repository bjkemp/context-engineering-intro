# Adventure Generation Agent

🤖 **AI-powered .adv file creator with 10 specialized tools for generating balanced, engaging adventures**

The Adventure Generation Agent is a sophisticated multi-tool AI system that transforms author personas and story outlines into fully playable .adv adventure files. Built with Pydantic AI and modern Python best practices, it ensures narrative coherence, character consistency, and balanced gameplay through comprehensive quality assurance.

## 🎯 Features

### ⚡ 10 Specialized AI Tools
1. **Storyline Generator** - Core narrative generation with chunking for large adventures
2. **Character Tracker** - Maintains character consistency across story branches  
3. **Inventory Integrator** - Generates game mechanics and balances progression
4. **ADV Validator** - Ensures compatibility with JavaScript game engine
5. **Branch Pruner** - Eliminates dead ends and optimizes story flow
6. **Coherence Analyzer** - Validates plot logic and narrative consistency
7. **Ending Optimizer** - Balances outcome distribution and accessibility
8. **Choice Analyzer** - Ensures meaningful player agency and differentiation
9. **Replayability Scorer** - Analyzes variation and replay value
10. **Flow Visualizer** - Generates story maps and flow diagrams

### 🚀 Key Capabilities
- **Complete .adv Generation** - From author style + story → playable adventure
- **Quality Assurance Pipeline** - Multiple validation layers with self-correction
- **Batch Processing** - Generate multiple adventures from different combinations
- **Real-time Streaming** - Watch the generation process with live feedback
- **Modern CLI** - Typer-based interface with rich terminal output
- **Format Validation** - Ensures generated files work with existing game engine

## 🔧 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd adventure-agent

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .

# Set up your API key
cp .env.example .env
# Edit .env and add your Google AI or OpenAI API key
```

### API Key Setup

You need either a Google AI API key (recommended) or OpenAI API key:

**Option 1: Google AI (Gemini) - Recommended**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Add to `.env` file: `GOOGLE_API_KEY=your_key_here`

**Option 2: OpenAI**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` file: `OPENAI_API_KEY=your_key_here`

### Basic Usage

```bash
# Generate a single adventure
uv run python3 agent.py generate examples/Terry_Pratchett.author examples/The_Color_Of_Magic_CYOA.story

# Generate with custom output and quality threshold
uv run python3 agent.py generate \
  examples/George_Lucas.author \
  examples/BlackHawks_TroublesInHyperspace_CYOA.story \
  --output my_adventure.adv \
  --quality 8.0

# Batch generate all combinations
uv run python3 agent.py batch examples/ examples/ --output-dir generated/

# Validate an existing .adv file
uv run python3 agent.py validate my_adventure.adv --verbose

# Generate flow visualization
uv run python3 agent.py visualize my_adventure.adv --format ascii

# Analyze adventure quality
uv run python3 agent.py analyze my_adventure.adv --type quality
```

## 📁 Project Structure

```
adventure-agent/
├── src/adventure_agent/
│   ├── agent.py              # Main Adventure Generation Agent
│   ├── models.py             # Pydantic data models
│   ├── cli.py                # Typer-based CLI interface
│   ├── parsers/              # Input/output file handling
│   │   ├── author_parser.py  # .author file parsing
│   │   ├── story_parser.py   # .story file parsing
│   │   └── adv_generator.py  # .adv file generation
│   └── tools/                # 10 specialized AI tools
│       ├── storyline_generator.py
│       ├── character_tracker.py
│       ├── inventory_integrator.py
│       ├── adv_validator.py
│       ├── branch_pruner.py
│       ├── coherence_analyzer.py
│       ├── ending_optimizer.py
│       ├── choice_analyzer.py
│       ├── replayability_scorer.py
│       └── flow_visualizer.py
├── tests/                    # Comprehensive test suite
├── examples/                 # Example .author and .story files
├── agent.py                  # Entry point script
└── pyproject.toml           # uv project configuration
```

## 📋 File Formats

### .author Files
Define the writing style and narrative voice:

```markdown
# Voice and Tone
- Witty and satirical
- Humorous undertones
- Ironic observations

# Narrative Style
- Descriptive prose
- Character-driven storytelling
- Third-person omniscient

# World Elements
- Fantasy setting with modern sensibilities
- Magical bureaucracy
- Anthropomorphic Death

# Character Development
- Growth through adversity
- Humor in the face of tragedy
- Reluctant heroes

# Themes
- Good vs evil (but it's complicated)
- The power of friendship
- Bureaucracy and society
```

### .story Files
Define the adventure requirements and structure:

```markdown
# Setting
Location: Ankh-Morpork
Time Period: Fantasy/Medieval
Atmosphere: Bustling magical city

# Main Character
Name: Rincewind
Background: Incompetent wizard
Motivation: Survival and avoiding responsibility

# Plot
Rincewind must deliver an important message from the Unseen University to the Patrician's Palace, but various magical and mundane obstacles keep getting in his way.

# NPCs
- The Librarian: Wise orangutan who provides cryptic assistance
- Lord Vetinari: The Patrician expecting the message
- Luggage: Rincewind's magical travel chest

# Branches
- Diplomatic Approach: Use official channels and proper procedures
- Sneaky Route: Avoid attention through back alleys
- Magical Solution: Use unreliable magic to solve problems

# Technical Requirements
Length: 8-12 story steps
Branches: 3 major branching points
Endings: 3 (success, failure, neutral)
Complexity: Medium
```

### Generated .adv Files
Compatible with the existing JavaScript CYOA game engine:

```
[GAME_NAME]
The Adventure of Rincewind
[/GAME_NAME]

[MAIN_MENU]
Start New Game
Load Game
Exit
[/MAIN_MENU]

[STEP_1]
[NARRATIVE]
You stand in the dusty halls of Unseen University, clutching an important message...
[/NARRATIVE]

[CHOICES]
A) Take the direct route through the city → STEP_2
B) Try the sneaky back-alley approach → STEP_3
[/CHOICES]
[/STEP_1]

[ENDING_SUCCESS]
Congratulations! You successfully delivered the message and saved the day.
[/ENDING_SUCCESS]
```

## 🎮 CLI Commands

### Generate Adventures
```bash
# Single adventure generation
uv run python3 agent.py generate AUTHOR_FILE STORY_FILE [OPTIONS]

Options:
  --output, -o TEXT         Output .adv file path
  --quality, -q FLOAT       Quality threshold (0-10) [default: 7.0]
  --no-streaming           Disable streaming output
  --verbose, -v            Enable verbose output
```

### Batch Processing
```bash
# Generate all combinations
uv run python3 agent.py batch AUTHOR_DIR STORY_DIR [OPTIONS]

Options:
  --output-dir, -o TEXT     Output directory [default: output]
  --quality, -q FLOAT       Quality threshold [default: 7.0]
  --max, -m INTEGER         Maximum combinations [default: 10]
```

### Validation & Analysis
```bash
# Validate .adv file format
uv run python3 agent.py validate ADVENTURE_FILE [--verbose]

# Generate flow visualization
uv run python3 agent.py visualize ADVENTURE_FILE [OPTIONS]
  --format, -f              ascii, dot, mermaid, json [default: ascii]
  --output, -o TEXT         Output file path

# Analyze adventure quality
uv run python3 agent.py analyze ADVENTURE_FILE [OPTIONS]
  --author TEXT             Author file for context
  --story TEXT              Story file for context
  --type, -t TEXT           quality, branch, ending, choice [default: quality]
```

### Utilities
```bash
# Show file information
uv run python3 agent.py info FILE

# List examples
uv run python3 agent.py examples --list

# Copy examples to directory
uv run python3 agent.py examples --copy-to DIRECTORY
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=adventure_agent

# Run specific test category
uv run pytest tests/test_tools/
uv run pytest tests/test_parsers/
uv run pytest tests/test_agent.py
```

## 🔄 Quality Pipeline

The Adventure Generation Agent uses a sophisticated 10-stage pipeline:

1. **Storyline Generation** - Creates base narrative structure
2. **Character Tracking** - Ensures character consistency  
3. **Inventory Integration** - Adds game mechanics
4. **Format Validation** - Verifies .adv compatibility
5. **Branch Optimization** - Removes dead ends
6. **Coherence Analysis** - Checks plot logic
7. **Ending Optimization** - Balances outcomes
8. **Choice Analysis** - Validates player agency
9. **Replayability Scoring** - Measures replay value
10. **Flow Visualization** - Maps story structure

Each stage includes validation and self-correction capabilities, ensuring high-quality output that meets the specified quality threshold.

## 📊 Quality Metrics

The system tracks multiple quality dimensions:

- **Overall Quality Score** (0-10) - Weighted combination of all metrics
- **Format Validation** - Compliance with .adv specification
- **Narrative Coherence** - Plot logic and consistency
- **Character Consistency** - Character behavior across branches
- **Choice Quality** - Meaningful player agency and differentiation
- **Replayability** - Variation and replay incentives
- **Branch Balance** - Ending distribution and accessibility

## 🔗 Integration

Generated .adv files are designed to work seamlessly with the existing JavaScript CYOA game engine. The ADV Validator tool ensures complete compatibility by validating against the same parsing rules used by the game engine.

## 🛠️ Development

### Adding New Tools

To add a new analysis tool:

1. Create tool file in `src/adventure_agent/tools/`
2. Implement async functions with `ToolResult` returns
3. Add tool to main agent pipeline in `agent.py`
4. Create corresponding tests
5. Update CLI if needed

### Extending File Formats

The parser system is modular and can be extended to support additional input formats. See the existing parsers for patterns.

### Quality Thresholds

Quality thresholds can be customized per use case:
- **6.0+** - Basic quality, suitable for testing
- **7.0+** - Production quality (default)
- **8.0+** - High quality for premium content
- **9.0+** - Exceptional quality for showcase content

## 📚 Examples

The `examples/` directory contains sample files:

- `Terry_Pratchett.author` - Discworld-style humorous fantasy
- `George_Lucas.author` - Epic space opera style
- `The_Color_Of_Magic_CYOA.story` - Fantasy adventure story
- `BlackHawks_TroublesInHyperspace_CYOA.story` - Space adventure
- `demo.adv` - Example generated adventure file

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the existing patterns
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

Built with modern Python tools:
- **Pydantic AI** - Agent framework and structured outputs
- **Typer** - Modern CLI framework
- **uv** - Fast Python package management
- **Rich** - Beautiful terminal output
- **Pytest** - Comprehensive testing

---

**Ready to create amazing adventures?** Start with `uv run python3 agent.py examples --list` to see available examples, then generate your first adventure with the provided sample files!