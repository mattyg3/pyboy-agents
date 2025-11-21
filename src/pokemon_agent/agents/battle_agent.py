from .init_llm import llm_model
# import lmstudio as lms
from pokemon_agent.plugins.perception import PokemonPerceptionAgent, BattleFlag
from pokemon_agent.plugins.skills import SkillExecutor
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END

# ------ Define State ------
class AgentState(TypedDict):
    messages: list[dict[str, Any]]
    battle_thoughts: list[dict[str, Any]]
    battle_move: str
    prev_turn: int

def create_battle_agent_state(
        messages=[],
        battle_thoughts=[],
        battle_move=None,
        prev_turn=-1,
) -> AgentState:
    return AgentState(
        messages=messages, 
        battle_thoughts=battle_thoughts,
        battle_move=battle_move,
        prev_turn=prev_turn,
    )


class BattleAgent:
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.perception = PokemonPerceptionAgent(self.pyboy)
        self.battle_flag = BattleFlag(self.pyboy)
        self.skills = SkillExecutor(self.pyboy)

    def battle_agent(self, state):
        battle_info = self.battle_flag.read_memory_state()
        game_state = self.perception.get_game_state()

        if state["prev_turn"] != battle_info["battle_turn"] and game_state.get("menu_state"):
            state["prev_turn"] = battle_info["battle_turn"]
            
            game_state = self.perception.get_game_state()
            cleaned_game_state = {"player":game_state["player"]["pokemon"], "opponent":game_state["opponent"], "battle":{"turn":game_state["battle"]["turn"], "player_turn":game_state["battle"]["player_turn"]}}
            # print(f"\nCLEANED GAME STATE\n{cleaned_game_state}\n")
            sys_prompt = f"""
            # Role
            You are a Pokemon battle decision agent

            # Task
            Given 'Battle Details', select the next best action from the 'Possible Moves Dictionary'

            # Possible Moves Dictionary
            - "move_1"
            - "move_2"
            - "move_3"
            - "move_4"
            - "run"

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
            # print("FINISHED_LLM")

        else:
            self.skills.execute({"type": "PRESS_A"})
            # print("PRESS_A: skipping llm")
            for _ in range(400):  # wait 200 frames
                self.pyboy.tick()
            state["battle_move"]=None

        return state




    
    def compile_workflow(self, state: AgentState):
        # ------ Define Nodes ------
        def start_node(state: AgentState):
            for _ in range(60):  # wait 60 frames screen to load
                self.pyboy.tick()
            while True: # get through any opening dialog
                game_state = self.perception.get_game_state()
                if game_state.get("menu_state"):
                    return state
                else:
                    self.skills.execute({"type": "PRESS_A"})
                    # print("PRESS_A: skip to battle menu")
                    for _ in range(5):  # wait 5 frames
                        self.pyboy.tick()
            
        def routing_node(state: AgentState):
            battle_flag = BattleFlag(self.pyboy)
            battle_info = battle_flag.read_memory_state()
            if battle_info["battle_type"] != 0:
                # print(f"BATTLE TYPE: {battle_info["battle_type"]}")
                # print("ROUTING -> BATTLE")
                return "battle"
            else:
                # print("ROUTING -> END")
                return "end"
            
        def battle_action_node(state: AgentState):
            """
            # Possible Moves Dictionary
            - "move_1"
            - "move_2"
            - "move_3"
            - "move_4"
            - "run"
            """
            if state["battle_move"] == "move_1":
                #Press Fight
                self.skills.execute({"type": "PRESS_A"})
                # print("PRESS_A: Select 'Fight' Option")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press First Move
                self.skills.execute({"type": "PRESS_A"})
                # print("PRESS_A: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
            elif state["battle_move"] == "move_2": 
                #Press Fight
                self.skills.execute({"type": "PRESS_A"})
                # print("PRESS_A: Select 'Fight' Option")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Down
                self.skills.execute({"type": "GO_DOWN"})
                # print("GO_DOWN: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Second Move
                self.skills.execute({"type": "PRESS_A"})
                # print("PRESS_A: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
            elif state["battle_move"] == "move_3": 
                #Press Fight
                self.skills.execute({"type": "PRESS_A"})
                # print("PRESS_A: Select 'Fight' Option")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Down
                self.skills.execute({"type": "GO_DOWN"})
                # print("GO_DOWN: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Down
                self.skills.execute({"type": "GO_DOWN"})
                # print("GO_DOWN: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Third Move
                self.skills.execute({"type": "PRESS_A"})
                # print("PRESS_A: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
            elif state["battle_move"] == "move_4": 
                #Press Fight
                self.skills.execute({"type": "PRESS_A"})
                # print("PRESS_A: Select 'Fight' Option")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Down
                self.skills.execute({"type": "GO_DOWN"})
                # print("GO_DOWN: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Down
                self.skills.execute({"type": "GO_DOWN"})
                # print("GO_DOWN: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Down
                self.skills.execute({"type": "GO_DOWN"})
                # print("GO_DOWN: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
                #Press Fourth Move
                self.skills.execute({"type": "PRESS_A"})
                # print("PRESS_A: Select First Move")
                for _ in range(5):  # wait 5 frames
                    self.pyboy.tick()
            return state

        def battle_node(state: AgentState):
            return self.battle_agent(state)
        def routing(state: AgentState):
            #run routing_node
            return state
    
        # ------ Define Workflow ------
        workflow = StateGraph(state_schema=AgentState)
        workflow.add_node("start", start_node)
        workflow.add_node("routing", routing)
        workflow.add_node("battle", battle_node)
        workflow.add_node("battle_action", battle_action_node)

        workflow.set_entry_point("start")
        workflow.add_edge("start", "routing")
        workflow.add_conditional_edges("routing", routing_node, 
                                    {
                                        "battle":"battle", 
                                        "end":END
                                        })
        workflow.add_edge("battle", "battle_action")
        workflow.add_edge("battle_action", "routing")
        # ------ Compile Workflow ------
        self.app = workflow.compile()





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