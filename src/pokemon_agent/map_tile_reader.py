from pyboy import PyBoy
import time

# Load ROM (make sure the path is correct)
pyboy = PyBoy('ROMS/pokemon_red.gb', window='SDL2')  # Use 'SDL2' for GUI window
# pyboy.set_emulation_speed(0)
# Load Save State
LOAD_STATE_PATH = 'src/pokemon_agent/saves/pokemon_red_charmander_prefight.sav'
with open(LOAD_STATE_PATH, "rb") as f:
        pyboy.load_state(f)

# Wait for the game to boot up
for _ in range(500):  # Run ~500 frames (~8 seconds)
    pyboy.tick()

# Access memory directly
mem = pyboy.memory

# WRAM0 starts at 0xC000, tile buffer is at 0xC3E0
tilemap_address = 0xC3E0
tilemap_size = 20 * 18  # 360 tiles

tile_bytes = mem[tilemap_address: tilemap_address + tilemap_size]
tile_ids = list(tile_bytes)

# Print the tilemap as a 20x18 grid
print("Visible Tile Map (20x18):")
for y in range(18):
    row = tile_ids[y*20:(y+1)*20]
    print(' '.join(f"{tile:02X}" for tile in row))

# Close emulator
pyboy.stop()
