from .init_llm import lms, llm_model
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langchain.tools import tool
from langchain.schema import SystemMessage, HumanMessage

from pokemon_agent.map_collision_read import *
from pokemon_agent.progress_tracking import ProgressTracker
from pokemon_agent.agents.tools_agent import get_directions
from pokemon_agent.path_finder import astar_next_step
# from pokemon_agent.agents.tools_agent import tool_app, run, TOOLS


# llm = ChatOpenAI(
#     api_key="not-needed",
#     base_url="http://localhost:1234/v1",
#     model="qwen/qwen3-4b-thinking-2507",   # or your loaded model
#     temperature=0,
# )

# # ------ Define Tools ------
# TOOLS = [
#         StructuredTool.from_function(
#             func=get_directions,
#             name="get_directions",
#             description="Search a graph object to get directions from point_a to point_b."
#         )]
# llm = llm.bind_tools(TOOLS)


# ------ Define State ------
class AgentState(TypedDict):
    messages: list[dict[str, Any]]
    goals_thoughts: list[dict[str, Any]]
    next_best_action: str
    dialog_history: str
    # has_preprompt: bool
    # tool_call: dict[str, Any]
    # tool_call:str
    # directions:str
    game_state: dict[str, Any]
    scratch_pad: str


def create_goal_agent_state(
        messages=[],
        goals_thoughts=[],
        next_best_action=None,
        dialog_history=None,
        # has_preprompt=False,
        # tool_call=None,
        # directions=None,
        game_state=None,
        scratch_pad='Previous Move Decisions (Oldest to Most Recent):\n',
        


) -> AgentState:
    return AgentState(
        messages=messages, 
        goals_thoughts=goals_thoughts,
        next_best_action=next_best_action,
        dialog_history=dialog_history,
        # has_preprompt=has_preprompt,
        # tool_call=tool_call,
        # directions=directions,
        game_state=game_state,
        scratch_pad=scratch_pad,
    )


class GoalsAgent:
    def __init__(self, pyboy): #, preprompt=''
        self.pyboy = pyboy
        # self.preprompt = preprompt
        self.progress = ProgressTracker(pyboy)

    def goals_agent(self, state):
        LONGTERM_GOAL, dialog_history = self.progress.check_progress()
        map_id = get_current_map(self.pyboy)
        map_label = get_map_label(map_id)
        map_connections = get_all_map_connections(map_id)
        map_filename = get_map_filename(map_id)
        map_doorways = get_warp_tiles(map_filename)
        map_npcs = get_npc_coords(map_filename)

        map_id, px, py, direction = get_player_position(self.pyboy)
        walk_matrix, map_width, map_height, warp_tiles = read_map(self.pyboy)

        start = (px,py)
        available_connections = []
        for loc in map_connections:
            coords = loc["connection_coords"]
            # connection_label = loc["target_label"]
            for coord in coords:
                a_star = astar_next_step(walk_matrix, start, (coord[0], coord[1]))
                if a_star:
                    available_connections.append(loc)
                    break
                else:
                    pass

        available_doorways = []
        for loc in map_doorways:
            coord = loc["xy_coord"]
            a_star = astar_next_step(walk_matrix, start, (coord[0], coord[1]))
            if a_star:
                available_doorways.append(loc)
            else:
                pass


        curr_game_state = {
            "Longterm Goal": LONGTERM_GOAL,
            "Dialog History": dialog_history,
            "Current Map": map_label,
            "Map Connections": available_connections,
            "Map Doorways": available_doorways,
            "Map NPCs": map_npcs,
        }

        state["game_state"] = curr_game_state

        

        sys_prompt = f"""
        # Role
        You are playing a Pokemon game and need to decide what action to take next

        # Task
        Given 'Current Game State', select the next best action. In 'Current Game State' there are lists different types of actions that can be made:
            - 'Map Connections': Lists all of possible maps connected to the current map. **IF** this is empty, you **cannot** use ['NORTH', 'SOUTH', 'EAST', or 'WEST]
            - 'Map Doorways': Lists all possible doorways in the current map
            - 'Map NPCs': Lists all possible NPCs to interact with in current map

        # General Map Connection Information
            - Use get_directions tool_call if you need to check directions from point_a to point_b
            - When traveling NORTH, you will likely need to use the labeled SOUTH entrance for the target map
            - '*_GATE' maps are access points to main maps. Example: 'VIRIDIAN_FOREST_SOUTH_GATE' is the southern entrance to 'VIRIDIAN_FOREST'. To enter 'VIRIDIAN_FOREST', you must fully pass through the 'VIRIDIAN_FOREST_SOUTH_GATE'. To exit the otherside of 'VIRIDIAN_FOREST', you must pass through the other gate 'VIRIDIAN_FOREST_NORTH_GATE'.

        # Stategy
        Consider the 'Longterm Goal' and 'Dialog History' from the 'Current Game State', also consider 'Scratch Pad' for previous moves. Use available tool to determine which map connections and doorways to use.

        # Current Game State
        {state["game_state"]}

        # Example Responses
            - "Move to 'NORTH'"
                - 'Map Connections' Example: Uses the 'direction' of the desired connection as the response key value
            - "Enter 'BLUES_HOUSE'"
                - 'Map Doorways' Example: Uses the 'destination' of the desired doorway as the response key value
            - "Talk to 'OAK'"
                - 'Map NPCs' Example: Uses the 'name' of the desired NPC as the response key value

        # Output Restrictions
        **MUST** select an action from the provided options in 'Current Game State'
                
        # Output Format
        **IF** calling a tool, output should be exactly: 'TOOL_CALL: get_directions from POINT_A to POINT_B'
        **ELSE** the next best action formatted exactly like the 'Example Responses' provided. 


        # Scratch Pad
        {state["scratch_pad"]}
        """
        # - Pallet Town -> Route 1 -> Viridian City -> Route 2 (south) -> Viridian South Gate -> Viridian Forest -> Viridian North Gate -> Route 2 (north) -> Pewter City -> Route 3 -> Mt. Moon -> Route 4 -> Cerulean City
        # chat = lms.Chat(sys_prompt)

        # # if self.preprompt!='':
        # #     chat.add_user_message(self.preprompt)
        # #     self.preprompt='' #reset to empty strionmg

        # chat.add_user_message(sys_prompt)

        # # print("RIGHT BEFORE LLM_MODEL")




        # response = llm.invoke(sys_prompt)
        # result = response.model_dump()
        # result_content = result["content"]

        # state["messages"].append({"role":"researcher", "content": f'Research: {response.model_dump()}'})
        # if not isinstance(response, AIMessage) or not getattr(response, "tool_calls", None):
        #     pass
        # else:
        #     state["research_queries"].append(str(response.tool_calls[0].get("args").get("query")))
        # state["tool_call"] = response
        result = llm_model.respond(sys_prompt)
        result_content = result.content





        # def _raise_exc_in_client(
        #     exc: lms.LMStudioPredictionError, request: lms.ToolCallRequest | None
        # ):
        #     raise exc

        # result = llm_model.act(
        #     chat,
        #     [get_directions],
        #     handle_invalid_tool_request=_raise_exc_in_client,
        #     on_message=chat.append,
        #     # on_message=print,
        #     # on_prediction_fragment=print,
        # )

        # print(f"ACT_RESULT: {result}")
        # print(f"ACT_RESULT__dict__: {result.__dict__}")
        # print(f"CHAT_HISTORY: {chat._messages}")
        
        
        # ai_response = 
        # print(type(chat._messages[-1].content[0].text))
        # response = llm_w_tools.invoke(sys_prompt)
        # result_content = response.model_dump()
        # result_content = chat._messages[-1].content[0].text

        

        if "</think>" in result_content:
            thinking = result_content.split("</think>", 1)[0].strip()
            response = result_content.split("</think>", 1)[1].strip()
        else:
            response = result_content.strip()
        # print(f"RESPONSE: {response}")
        # if 'TOOL_CALL:' in response.upper():
        #     state["next_best_action"] = 'TOOL_CALL'
        #     state["tool_call"] = response
        # else:
        #     state["next_best_action"] = response
        #     state["tool_call"] = None
        state["next_best_action"] = response
        state["messages"].append({"role":"goals", "content": response})
        state["goals_thoughts"].append({"content": thinking})
        new_sp = (
        state["scratch_pad"]
        + "\n"
        + str({'current_map':map_label, 'llm_decision':response})
    )
        state["scratch_pad"] = new_sp

        return state
    

    def compile_workflow(self, state: AgentState):
        # ------ Define Nodes ------
        def goals_node(state: AgentState):
            return self.goals_agent(state)
        # def run_tools(state: AgentState):
        #     """
        #     Custom replacement for ToolNode:
        #     - Look for tool calls in the last AIMessage
        #     - Execute them and append ToolMessage outputs
        #     """
        #     state["directions"] = None
        #     tool_call = state["tool_call"]
        #     # last_message = state["messages"][-1]
        #     if not isinstance(tool_call, AIMessage) or not getattr(tool_call, "tool_calls", None):
        #         # No tool calls, nothing to do
        #         return state  

        #     for call in tool_call.tool_calls:
        #         name = call["name"]
        #         args = call.get("args", {})
        #         for tool in TOOLS:
        #             if name in tool.name:
        #                 result = tool.invoke(args)

        #                 # Append a ToolMessage with the result
        #                 # state["messages"].append(
        #                 #     ToolMessage(name=name, content=result, tool_call_id=call["id"])
        #                 # )
        #                 state["messages"].append({"role":"tool_call", "content": f'Tool {name}: {result}'})
        #                 state["directions"] = result

        #     return state
        # def run_tools_agent(state: AgentState):
        #     state["directions"] = run(tool_app, state["tool_call"])
        #     return state
        
        # def tool_routing(state: AgentState) -> str:
        #     # last_message = state["messages"][-1]
        #     tool_call = state["tool_call"]
        #     #Max number of search iterations
        #     # if state["directions"]:
        #     #     return "end"
        #     try:
        #         if tool_call:
        #             return "tools"
        #         else:
        #             return "end"
        #     except:
        #         return "end"
        # ------ Define Workflow ------
        workflow = StateGraph(state_schema=AgentState)
        workflow.add_node("llm", goals_node)
        # workflow.add_node("tools", run_tools_agent)
        workflow.set_entry_point("llm")
        workflow.add_edge("llm", END)
        # workflow.add_conditional_edges("llm", tool_routing, 
        #                        {
        #                            "tools":"tools", 
        #                            "end":END
        #                            })
        # workflow.add_edge("tools", "llm")
        # ------ Compile Workflow ------
        self.app = workflow.compile()