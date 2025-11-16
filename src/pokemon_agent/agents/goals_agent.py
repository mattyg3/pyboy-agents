from .init_llm import lms, llm_model
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from langchain.tools import StructuredTool
from map_collision_read import *
from progress_tracking import ProgressTracker
from .agent_tools import get_directions


# # ------ Define Tools ------
# tools = [
#         StructuredTool.from_function(
#             func=get_directions,
#             name="get_directions",
#             description="Search a graph object to get directions from point_a to point_b."
#         )]
# llm_w_tools = llm_model.bind_tools(tools)

# ------ Define State ------
class AgentState(TypedDict):
    messages: list[dict[str, Any]]
    goals_thoughts: list[dict[str, Any]]
    next_best_action: str
    dialog_history: str
    # has_preprompt: bool
    tool_call: dict[str, Any]
    directions:str


def create_goal_agent_state(
        messages=[],
        goals_thoughts=[],
        next_best_action=None,
        dialog_history=None,
        # has_preprompt=False,
        tool_call=None,
        directions=None,


) -> AgentState:
    return AgentState(
        messages=messages, 
        goals_thoughts=goals_thoughts,
        next_best_action=next_best_action,
        dialog_history=dialog_history,
        # has_preprompt=has_preprompt,
        tool_call=tool_call,
        directions=directions,
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

        curr_game_state = {
            "Longterm Goal": LONGTERM_GOAL,
            "Dialog History": dialog_history,
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
        Consider the 'Longterm Goal' and 'Dialog History' from the 'Current Game State'

        # Current Game State
        {curr_game_state}

        # Tools
            - get_directions(start, end): a function that returns the directions (map connections) from start to end locations. Use this function if you need to navigate between maps.

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
        # chat = lms.Chat(sys_prompt)

        # # if self.preprompt!='':
        # #     chat.add_user_message(self.preprompt)
        # #     self.preprompt='' #reset to empty strionmg

        # chat.add_user_message(sys_prompt)

        # # print("RIGHT BEFORE LLM_MODEL")
        result = llm_model.respond(sys_prompt)
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
        
        result_content = result.content
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
        state["messages"].append({"role":"goals", "content": response})
        state["next_best_action"] = response
        state["goals_thoughts"].append({"content": thinking})

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
        #         for tool in tools:
        #             if name in tool.name:
        #                 result = tool.invoke(args)

        #                 # Append a ToolMessage with the result
        #                 # state["messages"].append(
        #                 #     ToolMessage(name=name, content=result, tool_call_id=call["id"])
        #                 # )
        #                 state["messages"].append({"role":"tool_call", "content": f'Tool {name}: {result}'})
        #                 state["directions"] = result

        #     return state
        
        # def tool_routing(state: AgentState) -> str:
        #     # last_message = state["messages"][-1]
        #     tool_call = state["tool_call"]
        #     #Max number of search iterations
        #     if state["directions"]:
        #         return "end"
        #     try:
        #         if tool_call.tool_calls:
        #             return "tools"
        #         else:
        #             return "end"
        #     except:
        #         return "end"
        # ------ Define Workflow ------
        workflow = StateGraph(state_schema=AgentState)
        workflow.add_node("start", goals_node)
        # workflow.add_node("tools", run_tools)
        workflow.set_entry_point("start")
        workflow.add_edge("start", END)
        # workflow.add_conditional_edges("start", tool_routing, 
        #                        {
        #                            "tools":"tools", 
        #                            "end":END
        #                            })
        # ------ Compile Workflow ------
        self.app = workflow.compile()