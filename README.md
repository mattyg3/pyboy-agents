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

The system follows a modular multi-agent architecture with LangGraph orchestration:

```
┌─────────────────┐    ┌─────────────────────────────────────────────────────────┐
│   Perception     │───▶│              Multi-Agent System (LangGraph)              │
│   (Memory+OCR)   │    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
└─────────────────┘    │  │  Goals   │  │  Battle  │  │ Pathing │  │ Unstuck  │ │
         │              │  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │ │
         ▼              │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
    Game State          └─────────────────────────────────────────────────────────┘
    (Memory + OCR)                    │                       │
                                       ▼                       ▼
                              ┌─────────────────┐    ┌─────────────────┐
                              │  Pathfinding    │───▶│  Skill Executor │
                              │  (A* Algorithm) │    │                 │
                              └─────────────────┘    └─────────────────┘
                                       │                       │
                                       ▼                       ▼
                              Navigation Path        Button Inputs
                              (Coordinate Seq)       (PyBoy Events)
```

### Core Components

- **`plugins/perception.py`**: Extracts game state through screen capture (OCR) and RAM reading
- **`agents/goals_agent.py`**: LLM-powered agent that determines high-level objectives and next actions
- **`agents/battle_agent.py`**: LLM-powered agent for battle decision making
- **`agents/pathing_agent.py`**: Executes navigation commands (enter buildings, move between maps, talk to NPCs)
- **`agents/unstuck_agent.py`**: Vision-based agent that handles stuck situations using screenshot analysis
- **`agents/init_llm.py`**: LLM initialization (currently uses LM Studio, supports Ollama and OpenAI)
- **`plugins/path_finder.py`**: A* pathfinding algorithm implementation for optimal navigation
- **`utils/map_collision_read.py`**: Reads map data from ROM, generates walkability matrices, and detects warp tiles
- **`plugins/skills.py`**: Executes plans by converting them to PyBoy button inputs
- **`plugins/progress_tracking.py`**: Tracks game progress through RAM flags and dialog history
- **`plugins/OCR.py`**: OCR processing with template matching for text recognition
- **`src/main.py`**: Main game loop orchestrating perception, LLM agents, pathfinding, and execution

## 🚀 Features

### Game State Perception
- **Visual Recognition**: OCR-based text reading with template matching from game screen
- **Memory Analysis**: Direct RAM access for precise Pokémon stats, battle state, location data, and player position
- **State Tracking**: Maintains awareness of current scene, battle status, map ID, and player coordinates

### LLM-Powered Strategic Planning
- **Multi-Agent System**: Four specialized agents working together:
  - **Goals Agent**: Determines high-level objectives and next best actions based on game progress
  - **Battle Agent**: Makes tactical battle decisions (move selection, running)
  - **Pathing Agent**: Executes navigation tasks (entering buildings, moving between maps, talking to NPCs)
  - **Unstuck Agent**: Vision-based recovery agent that analyzes screenshots when the agent gets stuck
- **LangGraph Integration**: Multi-agent orchestration workflow for complex decision making
- **Progress Tracking**: Monitors game progress through RAM flags and dialog history
- **Dialog Logging**: Captures and processes in-game dialogue for context

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
- LM Studio installed and running (for local LLM) OR Ollama/OpenAI configured
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
   - Update the path in `src/pokemon_agent/plugins/perception.py`:
     ```python
     pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
     ```

4. **Set up LLM** (choose one):
   - **LM Studio (Currently used)**:
     ```bash
     # Install LM Studio from https://lmstudio.ai
     # Download and load a model (e.g., qwen/qwen3-4b-thinking-2507)
     # Ensure LM Studio server is running
     ```
   - **Ollama** (alternative):
     ```bash
     # Install Ollama from https://ollama.ai
     ollama pull gemma3:4b  # or your preferred model
     # Uncomment Ollama code in src/pokemon_agent/agents/init_llm.py
     ```
   - **OpenAI** (alternative):
     ```bash
     # Store API key securely using keyring
     python -c "import keyring; keyring.set_password('openai', 'api_key', 'your-api-key')"
     # Uncomment OpenAI code in src/pokemon_agent/agents/init_llm.py
     ```

6. **Add Pokémon Red ROM**
   - Place `pokemon_red.gb` in the `ROMs/` directory

## 🎯 Usage

### Basic Usage

Run the main emulator loop:

```bash
python src/main.py
```

Or import and run programmatically:

```python
from src.main import run

ROM_PATH = 'ROMs/pokemon_red.gb'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV_oak_task.sav'
SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV.sav'

run(ROM_PATH, LOAD_STATE_PATH, SAVE_STATE_PATH)
```

The agent will:
1. Load a pre-configured save state
2. Read current map and player position
3. Use Goals Agent (LLM) to determine next best action
4. Use Pathing Agent to execute navigation (enter buildings, move between maps, talk to NPCs)
5. Calculate optimal path using A* algorithm
6. Navigate to destination autonomously
7. Handle battles with Battle Agent when encountered
8. Use Unstuck Agent if the agent gets stuck

### Configuration

Key parameters in `src/main.py`:

```python
ROM_PATH = 'ROMs/pokemon_red.gb'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV_oak_task.sav'
SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_DEV_got_townmap.sav'
```

LLM configuration in `src/pokemon_agent/agents/init_llm.py`:

```python
# LM Studio (currently used)
import lmstudio as lms
llm_model = lms.llm("qwen/qwen3-4b-thinking-2507")

# Or Ollama (uncomment and configure)
# from langchain_ollama import ChatOllama
# llm = ChatOllama(model="gemma3:4b", temperature=1.0, top_k=64, top_p=0.95)

# Or OpenAI (uncomment and configure)
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

### Customizing Behavior

- **Modify LLM prompts**: Edit agent files in `src/pokemon_agent/agents/`
  - `goals_agent.py` - High-level goal planning
  - `battle_agent.py` - Battle strategy
  - `unstuck_agent.py` - Stuck situation recovery
- **Add new pathing tasks**: Extend `src/pokemon_agent/agents/pathing_agent.py`
- **Adjust pathfinding**: Modify `src/pokemon_agent/plugins/path_finder.py`
- **Add new macros**: Edit `src/pokemon_agent/utils/saved_macros.py`
- **Enhance perception**: Extend `src/pokemon_agent/plugins/perception.py`
- **Modify map reading**: Update `src/pokemon_agent/utils/map_collision_read.py`
- **Adjust progress tracking**: Modify `src/pokemon_agent/plugins/progress_tracking.py`

## 📁 Project Structure

```
pyboy-agents/
├── src/
│   ├── main.py                    # Main entry point and emulator loop
│   └── pokemon_agent/
│       ├── agents/                # LLM-powered agents
│       │   ├── init_llm.py       # LLM initialization (LM Studio/Ollama/OpenAI)
│       │   ├── goals_agent.py    # High-level goal planning agent
│       │   ├── battle_agent.py   # Battle decision agent
│       │   ├── pathing_agent.py  # Navigation execution agent
│       │   ├── unstuck_agent.py  # Vision-based recovery agent
│       │   └── tools_agent.py    # Tool-calling agent (if needed)
│       ├── plugins/               # Core functionality modules
│       │   ├── perception.py     # Game state perception (OCR + RAM)
│       │   ├── path_finder.py    # A* pathfinding implementation
│       │   ├── skills.py         # Input execution
│       │   ├── OCR.py            # OCR processing with template matching
│       │   └── progress_tracking.py  # Game progress tracking
│       ├── utils/                 # Utility modules
│       │   ├── map_collision_read.py  # Map reading and collision detection
│       │   ├── map_render_from_rom.py # Map visualization utilities
│       │   ├── saved_macros.py   # Pre-defined action sequences
│       │   └── utility_funcs.py # Helper functions
│       ├── data/                  # Game reference data
│       │   ├── *.json            # Game data (Pokedex, moves, types, RAM addresses)
│       │   ├── fonts/            # Font templates for OCR
│       │   └── pokered_data/     # ROM data structures
│       ├── maps/                  # Map data
│       │   ├── blocksets/        # Map blockset files
│       │   ├── tilesets/         # Tileset files
│       │   ├── map_files/        # Individual map block files
│       │   └── *.json            # Map headers, connections, objects, collision data
│       ├── saves/                 # Save states and logs
│       │   ├── *.sav             # PyBoy save state files
│       │   ├── dialog_log.txt    # Captured dialogue log
│       │   └── agent_states/     # Agent state snapshots
│       └── scripts/               # Data processing scripts
├── ROMs/                          # Game ROM files
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
- **Multi-Agent System**: Four specialized agents:
  - **Goals Agent**: Determines next best action based on game progress and long-term goals
  - **Battle Agent**: Selects optimal moves during battles
  - **Pathing Agent**: Executes navigation commands (enter, move, talk)
  - **Unstuck Agent**: Vision-based recovery using screenshot analysis
- **State Management**: Each agent maintains its own state with TypedDict
- **Progress Integration**: Goals agent uses progress tracker to understand game state

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
- **State Trackers**: Separate trackers for battle and overworld states
- **Dialog Logging**: Captures and processes in-game dialogue
- **Vision-Based Recovery**: Unstuck agent uses screenshot analysis to recover from stuck situations
- **Tesseract Fallback**: Optional Tesseract OCR for generic text recognition

### Action Execution
- **Button Automation**: Precise timing control for Game Boy inputs
- **Skill Macros**: Reusable action sequences for complex maneuvers (via `saved_macros.py`)
- **State-Aware Actions**: Context-sensitive input handling
- **Dialog Handling**: Automatic dialog advancement
- **Battle Execution**: Automated battle move selection and execution

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
- [LM Studio](https://lmstudio.ai) - Local LLM runtime (currently used)
- [Ollama](https://ollama.ai) - Alternative local LLM runtime
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Text recognition
- Pokémon Red - Nintendo's classic Game Boy game

## 🔮 Future Enhancements

- [x] LLM-powered strategic planning
- [x] A* pathfinding for exploration
- [x] Map collision detection from ROM data
- [x] Multi-agent coordination for complex tasks
- [x] Battle strategy optimization with LLM
- [x] Vision-based recovery agent
- [x] Progress tracking system
- [ ] Reinforcement learning integration
- [ ] Support for other Pokémon games
- [ ] Real-time performance optimization
- [ ] GUI for monitoring agent state
- [ ] Enhanced dialog understanding and context

---

**Note**: This project is for educational and research purposes. Pokémon is a trademark of Nintendo/Game Freak. Please ensure you own legitimate copies of any games you run with this emulator.