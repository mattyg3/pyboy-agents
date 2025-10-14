from utils.utility_funcs import create_macro

# ====== Game Start Macro ======
game_start_macro = create_macro()
game_start_macro.add_step({"type": "PRESS_A"}, 700)
game_start_macro.add_step({"type": "PRESS_B"}, 200) #gets through opening menus

game_start_macro.add_step({"type": "GO_RIGHT"}, 25)
game_start_macro.add_step({"type": "GO_UP"}, 25)
game_start_macro.add_step({"type": "GO_RIGHT"}, 25) #gets out of first room

game_start_macro.add_step({"type": "GO_DOWN"}, 25)
game_start_macro.add_step({"type": "GO_LEFT"}, 25)
game_start_macro.add_step({"type": "GO_DOWN"}, 25) #leaves the house

game_start_macro.add_step({"type": "GO_RIGHT"}, 20)
game_start_macro.add_step({"type": "GO_UP"}, 30)
game_start_macro.add_step({"type": "PRESS_A"}, 300) #meet Prof Oak

game_start_macro.add_step({"type": "PRESS_B"}, 400)
game_start_macro.add_step({"type": "GO_DOWN"}, 5)
game_start_macro.add_step({"type": "GO_RIGHT"}, 5)
game_start_macro.add_step({"type": "GO_UP"}, 5)
game_start_macro.add_step({"type": "PRESS_A"}, 500) #pick Charmander

# game_start_macro.add_step({"type": "GO_LEFT"}, 5)
# game_start_macro.add_step({"type": "GO_DOWN"}, 20)
# game_start_macro.add_step({"type": "PRESS_A"}, 1200) #battle rival (mash A button)

# game_start_macro.add_step({"type": "GO_DOWN"}, 150) #leave building, start adventure

# ###get to wild pokemon
# game_start_macro.add_step({"type": "GO_LEFT"}, 15)
# game_start_macro.add_step({"type": "GO_UP"}, 100)
# game_start_macro.add_step({"type":"GO_RIGHT"}, 10)
# game_start_macro.add_step({"type": "GO_UP"}, 300)


# ====== Start Rival Fight Macro ======
start_fight = create_macro()
start_fight.add_step({"type": "GO_LEFT"}, 2)
start_fight.add_step({"type": "GO_DOWN"}, 15)
start_fight.add_step({"type": "PRESS_A"}, 500)
# start_fight.add_step({"type": "PRESS_A"}, 150) #battle rival (mash A button)
start_fight.add_step({"type": "GO_DOWN"}, 8) #leave building, start adventure
# start_fight.add_step({"type": "GO_LEFT"}, 5)
# start_fight.add_step({"type": "GO_DOWN"}, 20)
# start_fight.add_step({"type": "PRESS_A"}, 1400) #battle rival (mash A button)
# start_fight.add_step({"type": "GO_DOWN"}, 150) #leave building, start adventure

# ====== Get to Wild Pokemon ======
wild_pokemon = create_macro()
wild_pokemon.add_step({"type": "GO_LEFT"}, 5)
wild_pokemon.add_step({"type": "GO_UP"}, 25)
wild_pokemon.add_step({"type":"GO_RIGHT"}, 3)
wild_pokemon.add_step({"type": "GO_UP"}, 100)

# test_macro = create_macro()
# test_macro.add_step({"type": "PRESS_A"}, 700)
# test_macro.add_step({"type": "PRESS_B"}, 200)
# test_macro.add_step({"type": "GO_RIGHT"}, 25)
# # test_macro.compile_macro()

# # print(test_macro.ordered_steps)

# button_action = test_macro.run_macro(frame=450, init_frame=0)
# print(button_action)
# # print(test_macro.ordered_steps)


