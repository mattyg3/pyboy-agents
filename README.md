# PyBoy Agents

An AI-powered Game Boy emulator agent system that uses computer vision, memory reading, LLM-based planning, and pathfinding to autonomously play Pokémon Red. This project demonstrates how to build intelligent agents that can perceive game state, make decisions using language models, and execute actions with precise navigation in real-time within a Game Boy emulation environment.

## 🎮 Overview

PyBoy Agents combines several AI techniques to create an autonomous Pokémon trainer:

- **Computer Vision**: OCR-based text recognition with template matching to read in-game dialogue and menus
- **Memory Reading**: Direct access to Game Boy RAM to extract precise game state information
- **LLM-Powered Planning**: Language models (Ollama/OpenAI) for strategic decision making and destination planning
- **Pathfinding**: A* algorithm for optimal navigation through the game world
- **Map Analysis**: Collision detection and walkability matrix generation from ROM data
- **Skill Execution**: Low-level input automation using PyBoy's button press system

## 🏗️ Architecture

The system follows a modular agent architecture with LangGraph orchestration:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Perception    │───▶│  LLM Agents     │───▶│  Pathfinding    │───▶│  Skill Executor │
│     Agent       │    │  (LangGraph)    │    │  (A* Algorithm) │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
    Game State              Action Plan              Navigation Path        Button Inputs
    (Memory + OCR)          (Structured LLM)         (Coordinate Seq)       (PyBoy Events)
```

### Core Components

- **`perception.py`**: Extracts game state through screen capture (OCR) and RAM reading
- **`agents/pathing_agent.py`**: LLM-powered agent that determines navigation destinations using structured outputs
- **`agents/init_llm.py`**: LLM initialization (supports Ollama and OpenAI)
- **`path_finder.py`**: A* pathfinding algorithm implementation for optimal navigation
- **`map_collision_read.py`**: Reads map data from ROM, generates walkability matrices, and detects warp tiles
- **`planner.py`**: Rule-based planning system with pre-defined action macros
- **`skills.py`**: Executes plans by converting them to PyBoy button inputs
- **`run_emulator.py`**: Main game loop orchestrating perception, LLM agents, pathfinding, and execution

## 🚀 Features

### Game State Perception
- **Visual Recognition**: OCR-based text reading with template matching from game screen
- **Memory Analysis**: Direct RAM access for precise Pokémon stats, battle state, location data, and player position
- **State Tracking**: Maintains awareness of current scene, battle status, map ID, and player coordinates

### LLM-Powered Strategic Planning
- **Structured Outputs**: Uses Pydantic models for type-safe LLM responses
- **Pathing Agent**: LLM determines optimal destinations based on current map state and objectives
- **LangGraph Integration**: Multi-agent orchestration workflow for complex decision making
- **LangSmith Tracing**: Full observability and debugging of agent workflows

### Navigation & Pathfinding
- **A* Pathfinding**: Optimal path calculation through walkability matrices
- **Map Collision Detection**: Reads collision data directly from ROM blocksets
- **Warp Tile Detection**: Identifies doors and map transitions
- **Map Connections**: Understands connections between maps in different directions
- **Real-time Position Tracking**: Continuous player position monitoring

### Action Execution
- **Button Automation**: Precise timing control for Game Boy inputs
- **Skill Macros**: Reusable action sequences for complex maneuvers
- **State-Aware Actions**: Context-sensitive input handling

## 📋 Prerequisites

- Python 3.8+
- Tesseract OCR installed and configured (for OCR fallback)
- Pokémon Red ROM file
- Ollama installed (for local LLM) OR OpenAI API key (for cloud LLM)
- Windows/Linux/macOS

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pyboy-agents.git
   cd pyboy-agents
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Tesseract OCR** (optional, for OCR fallback)
   - Download and install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
   - Update the path in `src/pokemon_agent/perception.py`:
     ```python
     pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
     ```

4. **Set up LLM** (choose one):
   - **Ollama (Recommended for local execution)**:
     ```bash
     # Install Ollama from https://ollama.ai
     ollama pull gemma3:4b  # or your preferred model
     ```
   - **OpenAI**:
     ```bash
     # Store API key securely using keyring
     python -c "import keyring; keyring.set_password('openai', 'api_key', 'your-api-key')"
     ```

5. **Configure LangSmith** (optional, for tracing):
   ```bash
   python -c "import keyring; keyring.set_password('langsmith', 'api_key', 'your-langsmith-api-key')"
   ```

6. **Add Pokémon Red ROM**
   - Place `pokemon_red.gb` in the `ROMs/` directory

## 🎯 Usage

### Basic Usage

Run the main emulator loop:

```bash
python src/pokemon_agent/run_emulator.py
```

Or import and run programmatically:

```python
from pokemon_agent.run_emulator import run

ROM_PATH = 'ROMs/pokemon_red.gb'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pre-save.sav'
SAVE_STATE_PATH = 'src/pokemon_agent/saves/saved_gamestate.sav'

run(ROM_PATH, LOAD_STATE_PATH, SAVE_STATE_PATH)
```

The agent will:
1. Load a pre-configured save state
2. Read current map and player position
3. Use LLM to determine navigation goals
4. Calculate optimal path using A* algorithm
5. Navigate to destination autonomously

### Configuration

Key parameters in `src/pokemon_agent/run_emulator.py`:

```python
ROM_PATH = 'ROMs/pokemon_red.gb'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_postfight_pallettown.sav'
SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV.sav'
```

LLM configuration in `src/pokemon_agent/agents/init_llm.py`:

```python
# Ollama (default)
llm = ChatOllama(model="gemma3:4b", temperature=1.0, top_k=64, top_p=0.95)

# Or OpenAI (uncomment and configure)
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

### Customizing Behavior

- **Modify LLM prompts**: Edit `src/pokemon_agent/agents/pathing_agent.py`
- **Add new pathing tasks**: Extend the pathing agent's task description
- **Adjust pathfinding**: Modify `src/pokemon_agent/path_finder.py`
- **Add new macros**: Edit `src/pokemon_agent/utils/saved_macros.py`
- **Enhance perception**: Extend `src/pokemon_agent/perception.py`
- **Modify map reading**: Update `src/pokemon_agent/map_collision_read.py`

## 📁 Project Structure

```
pyboy-agents/
├── src/
│   ├── main.py                    # Entry point (currently commented out)
│   └── pokemon_agent/
│       ├── agents/                # LLM-powered agents
│       │   ├── init_llm.py       # LLM initialization (Ollama/OpenAI)
│       │   └── pathing_agent.py  # Pathfinding destination agent
│       ├── perception.py          # Game state perception (OCR + RAM)
│       ├── planner.py             # Rule-based action planning
│       ├── skills.py              # Input execution
│       ├── run_emulator.py        # Main emulator loop (entry point)
│       ├── path_finder.py         # A* pathfinding implementation
│       ├── map_collision_read.py  # Map reading and collision detection
│       ├── map_render_from_rom.py # Map visualization utilities
│       ├── OCR.py                 # OCR processing with template matching
│       ├── font_templates.py      # Font template matching system
│       ├── process_map_data.py    # Map data processing utilities
│       ├── saves/                 # Save state files
│       └── utils/
│           ├── data_classes.py    # Game state data structures
│           ├── saved_macros.py    # Pre-defined action sequences
│           ├── utility_funcs.py   # Helper functions
│           └── ref_data/          # Pokémon game reference data
│               ├── maps/          # Map definitions, collision data, blocksets
│               ├── fonts/         # Font templates for OCR
│               └── *.json         # Game data (Pokedex, moves, types, etc.)
├── ROMs/                          # Game ROM files
├── tests/                         # Test files
├── dev_files/                     # Development utilities and tests
├── requirements.txt               # Python dependencies
└── pyproject.toml                 # Project metadata
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/
```

## 🔧 Technical Details

### LLM Agent Architecture
- **LangGraph**: Orchestrates multi-agent workflows with state management
- **Structured Outputs**: Uses Pydantic BaseModel for type-safe LLM responses
- **Pathing Agent**: Takes map state, player position, and task description, returns destination coordinates

### Memory Reading
The agent reads directly from Game Boy RAM to extract:
- Pokémon stats (HP, level, moves, types)
- Battle state information (turn order, move effects)
- Player position (map ID, X/Y coordinates, facing direction)
- Current scene/context

### Pathfinding
- **A* Algorithm**: Optimal path calculation with Manhattan distance heuristic
- **Walkability Matrices**: Generated from ROM collision data
- **Dynamic Path Calculation**: Recalculates as player moves
- **Next-Step Optimization**: Efficiently calculates only the immediate next move

### Map System
- **ROM Data Reading**: Reads map blocks, blocksets, and tilesets directly from ROM
- **Collision Detection**: Generates walkability matrices per environment type
- **Warp Detection**: Identifies doors and map transition points
- **Map Connections**: Understands directional connections between maps

### Computer Vision
- **Template Matching**: Custom font templates for accurate text recognition
- **OpenCV Preprocessing**: Image preprocessing for better OCR accuracy
- **Region-Based OCR**: Focuses on specific screen regions (dialogue, menus)
- **Tesseract Fallback**: Optional Tesseract OCR for generic text recognition

### Action Macros
Pre-defined sequences for common game scenarios:
- Game initialization
- Battle sequences
- Wild Pokémon encounters
- Navigation patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [PyBoy](https://github.com/Baekalfen/PyBoy) - Game Boy emulator framework
- [LangChain](https://github.com/langchain-ai/langchain) & [LangGraph](https://github.com/langchain-ai/langgraph) - LLM agent orchestration
- [Ollama](https://ollama.ai) - Local LLM runtime
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Text recognition
- Pokémon Red - Nintendo's classic Game Boy game

## 🔮 Future Enhancements

- [x] LLM-powered strategic planning
- [x] A* pathfinding for exploration
- [x] Map collision detection from ROM data
- [ ] Multi-agent coordination for complex tasks
- [ ] Battle strategy optimization with LLM
- [ ] Reinforcement learning integration
- [ ] Support for other Pokémon games
- [ ] Real-time performance optimization
- [ ] GUI for monitoring agent state

---

**Note**: This project is for educational and research purposes. Pokémon is a trademark of Nintendo/Game Freak. Please ensure you own legitimate copies of any games you run with this emulator.