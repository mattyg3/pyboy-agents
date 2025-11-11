from .init_llm import llm_model
# import lmstudio as lms
from perception import PokemonPerceptionAgent, BattleFlag
from skills import SkillExecutor
# game_state = {
#                 "player": mem_state["player"],
#                 "opponent": mem_state["opponent"],
#                 "battle": {
#                     "battle_type": mem_state.get("battle").get("battle_type"),
#                     "turn": mem_state.get("battle").get("turn"),
#                     "player_turn": player_turn
#                 },
#                 "menu_state": menu_state,
#                 "dialog_text": dialog_text,
#                 "dialog_history": TextCleaner(self.dialog_history),
#             }
def battle_agent(state, pyboy):
    perception = PokemonPerceptionAgent(pyboy)
    battle_flag = BattleFlag(pyboy)
    skills = SkillExecutor(pyboy)
    battle_info = battle_flag.read_memory_state()
    game_state = perception.get_game_state()
    # mem_state = perception.read_memory_state()

    # if mem_state["opponent"]["hp"] <= 0:
         
    # if game_state.get("menu_state"):
    # print(battle_info["battle_turn"])
    if state["prev_turn"] != battle_info["battle_turn"] and game_state.get("menu_state"):
        state["prev_turn"] = battle_info["battle_turn"]
        
        game_state = perception.get_game_state()
        cleaned_game_state = {"player":game_state["player"]["pokemon"], "opponent":game_state["opponent"], "battle":game_state["battle"]}
        print(f"\nCLEANED GAME STATE\n{cleaned_game_state}")
        sys_prompt = f"""
        # Role
        You are a Pokemon battle decision agent

        # Task
        Given 'Battle Details', select the next best action from the 'Possible Moves Dictionary'

        # Possible Moves Dictionary
        - "Move #1"
        - "Move #2"
        - "Move #3"
        - "Move #4"
        - "Run"

        # Stategy
        Be aggressive in your decision making

        # Battle Details
        {cleaned_game_state}

        # Output Format
        **ONLY** one of the options from 'Possible Moves Dictionary'
        """
        # with lms.Client() as client:
        #     llm_model = client.llm.model("qwen/qwen3-4b-thinking-2507@q4_k_m")
        #     result = llm_model.respond(sys_prompt)
        #     result_content = result.content

        result = llm_model.respond(sys_prompt)
        result_content = result.content

        if "</think>" in result_content:
            thinking = result_content.split("</think>", 1)[0].strip()
            response = result_content.split("</think>", 1)[1].strip()
        else:
            response = result_content.strip()
        
        state["messages"].append({"role":"battle", "content": response})
        state["battle_move"] = response
        state["battle_thoughts"].append({"content": thinking})
        print("FINISHED_LLM")

    else:
        skills.execute({"type": "PRESS_A"})
        print("PRESS_A: skipping llm")
        for _ in range(200):  # wait 200 frames
            pyboy.tick()
        print("SKIPPED_LLM")
        state["battle_move"]=None


    return state

# def main():
    # state={}
    # state["messages"]=[]
    # state["battle_thoughts"]=[]
    # # state["battle_details"] = "move #2 is the strongest move against this opponent"
    # state_new = battle_agent(state)
    # print(state_new)
    # print(response)
    # print(thinking)

# if __name__ == "__main__":
#     main()