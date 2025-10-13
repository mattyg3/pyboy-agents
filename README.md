# PyBoy Agents

An AI-powered Game Boy emulator agent system that uses computer vision, memory reading, and planning to autonomously play Pokémon Red. This project demonstrates how to build intelligent agents that can perceive game state, make decisions, and execute actions in real-time within a Game Boy emulation environment.

## 🎮 Overview

PyBoy Agents combines several AI techniques to create an autonomous Pokémon trainer:

- **Computer Vision**: OCR-based text recognition to read in-game dialogue and menus
- **Memory Reading**: Direct access to Game Boy RAM to extract precise game state information
- **Planning**: Rule-based and LLM-powered decision making for game strategy
- **Skill Execution**: Low-level input automation using PyBoy's button press system

## 🏗️ Architecture

The system follows a modular agent architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Perception    │───▶│     Planner     │───▶│  Skill Executor │
│     Agent       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
    Game State              Action Plan              Button Inputs
```

### Core Components

- **`perception.py`**: Extracts game state through screen capture and RAM reading
- **`planner.py`**: Generates action plans based on current state and objectives  
- **`skills.py`**: Executes plans by converting them to PyBoy button inputs
- **`run_emulator.py`**: Main game loop orchestrating perception, planning, and execution

## 🚀 Features

### Game State Perception
- **Visual Recognition**: OCR-based text reading from game screen
- **Memory Analysis**: Direct RAM access for precise Pokémon stats, battle state, and location data
- **State Tracking**: Maintains awareness of current scene, battle status, and player position

### Strategic Planning
- **Macro Sequences**: Pre-defined action sequences for common scenarios (game start, battles, wild encounters)
- **Adaptive Planning**: Dynamic decision making based on current game state
- **Goal-Oriented Behavior**: Focused objectives like catching Pokémon or winning battles

### Action Execution
- **Button Automation**: Precise timing control for Game Boy inputs
- **Skill Macros**: Reusable action sequences for complex maneuvers
- **State-Aware Actions**: Context-sensitive input handling

## 📋 Prerequisites

- Python 3.8+
- Tesseract OCR installed and configured
- Pokémon Red ROM file
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

3. **Configure Tesseract OCR**
   - Download and install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
   - Update the path in `src/pokemon_agent/perception.py`:
     ```python
     pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
     ```

4. **Add Pokémon Red ROM**
   - Place `pokemon_red.gb` in the `ROMs/` directory

## 🎯 Usage

### Basic Usage

```bash
python src/main.py
```

The agent will:
1. Load a pre-configured save state
2. Navigate through the game start sequence
3. Engage in Pokémon battles
4. Explore the game world autonomously

### Configuration

Modify key parameters in `src/main.py`:

```python
ROM_PATH = 'ROMS/pokemon_red.gb'
SAVE_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander.sav'
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'
```

### Customizing Behavior

- **Add new macros**: Edit `src/pokemon_agent/utils/saved_macros.py`
- **Modify planning logic**: Update `src/pokemon_agent/planner.py`
- **Enhance perception**: Extend `src/pokemon_agent/perception.py`

## 📁 Project Structure

```
pyboy-agents/
├── src/
│   ├── main.py                    # Main execution script
│   └── pokemon_agent/
│       ├── perception.py          # Game state perception
│       ├── planner.py             # Action planning
│       ├── skills.py              # Input execution
│       ├── run_emulator.py        # Emulator management
│       ├── saves/                 # Save state files
│       └── utils/
│           ├── data_classes.py    # Game state data structures
│           ├── saved_macros.py    # Pre-defined action sequences
│           ├── utility_funcs.py   # Helper functions
│           └── ref_data/          # Pokémon game reference data
├── ROMs/                          # Game ROM files
├── tests/                         # Test files
└── requirements.txt               # Python dependencies
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/
```

## 🔧 Technical Details

### Memory Reading
The agent reads directly from Game Boy RAM to extract:
- Pokémon stats (HP, level, moves)
- Battle state information
- Player position and inventory
- Current scene/context

### Computer Vision
- Uses OpenCV for image preprocessing
- Tesseract OCR for text extraction
- Focuses on dialogue regions for contextual understanding

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
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Text recognition
- Pokémon Red - Nintendo's classic Game Boy game

## 🔮 Future Enhancements

- [ ] LLM-powered strategic planning
- [ ] Multi-Pokémon battle strategies
- [ ] Advanced pathfinding for exploration
- [ ] Support for other Pokémon games
- [ ] Reinforcement learning integration
- [ ] Real-time performance optimization

---

**Note**: This project is for educational and research purposes. Pokémon is a trademark of Nintendo/Game Freak. Please ensure you own legitimate copies of any games you run with this emulator.