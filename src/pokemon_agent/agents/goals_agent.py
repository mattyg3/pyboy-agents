from .init_llm import llm_model
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from map_collision_read import *
from progress_tracking import ProgressTracker

# ------ Define State ------
class AgentState(TypedDict):
    messages: list[dict[str, Any]]
    goals_thoughts: list[dict[str, Any]]
    next_best_action: str


def create_goal_agent_state(
        messages=[],
        goals_thoughts=[],
        next_best_action=None,


) -> AgentState:
    return AgentState(
        messages=messages, 
        goals_thoughts=goals_thoughts,
        next_best_action=next_best_action,
    )


class GoalsAgent:
    def __init__(self, pyboy):
        self.pyboy = pyboy
        self.progress = ProgressTracker(pyboy)

    def goals_agent(self, state):
        LONGTERM_GOAL = self.progress.check_progress()
        map_id = get_current_map(self.pyboy)
        map_label = get_map_label(map_id)
        map_connections = get_all_map_connections(map_id)
        map_filename = get_map_filename(map_id)
        map_doorways = get_warp_tiles(map_filename)
        map_npcs = get_npc_coords(map_filename)

        curr_game_state = {
            "Longterm Goal": LONGTERM_GOAL,
            "Current Map": map_label,
            "Map Connections": map_connections,
            "Map Doorways": map_doorways,
            "Map NPCs": map_npcs,
        }

        sys_prompt = f"""
        # Role
        You are playing a Pokemon game and need to decide what action to take next

        # Task
        Given 'Current Game State', select the next best action. In 'Current Game State' there are lists different types of actions that can be made:
            - 'Map Connections': Lists all of possible maps connected to the current map
            - 'Map Doorways': Lists all possible doorways in the current map
            - 'Map NPCs': Lists all possible NPCs to interact with in current map

        # General Map Connection Information
        Pallet Town -> Route 1 -> Viridian City -> Route 2 -> Viridian Forest -> Pewter City -> Route 3 -> Mt. Moon -> Route 4 -> Cerulean City

        # Stategy
        Consider the 'Longterm Goal' from the 'Current Game State'

        # Current Game State
        {curr_game_state}

        # Example Responses
            - "Move to 'NORTH'"
                - 'Map Connections' Example: Uses the 'direction' of the desired connection as the response key value
            - "Enter 'BLUES_HOUSE'"
                - 'Map Doorways' Example: Uses the 'destination' of the desired doorway as the response key value
            - "Talk to 'OAK'"
                - 'Map NPCs' Example: Uses the 'name' of the desired NPC as the response key value

        # Output Format
        **ONLY** the next best action formatted exactly like the examples provided. 

        """
        result = llm_model.respond(sys_prompt)
        result_content = result.content

        if "</think>" in result_content:
            thinking = result_content.split("</think>", 1)[0].strip()
            response = result_content.split("</think>", 1)[1].strip()
        else:
            response = result_content.strip()
        
        state["messages"].append({"role":"goals", "content": response})
        state["next_best_action"] = response
        state["goals_thoughts"].append({"content": thinking})

        return state
    

    def compile_workflow(self, state: AgentState):
        # ------ Define Nodes ------
        def goals_node(state: AgentState):
            return self.goals_agent(state)
        # ------ Define Workflow ------
        workflow = StateGraph(state_schema=AgentState)
        workflow.add_node("start", goals_node)
        workflow.set_entry_point("start")
        workflow.add_edge("start", END)
        # ------ Compile Workflow ------
        self.app = workflow.compile()