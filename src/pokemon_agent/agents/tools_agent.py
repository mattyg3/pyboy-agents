# ================= ReAct Agent =================
import re
from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


# ---------------------------
# 1. Define Tools
# ---------------------------
import json
# from collections import deque, defaultdict
# from utils.utility_funcs import camel_to_snake
from pokemon_agent.utils.process_map_data import *

    
def get_directions(start: str, end: str):
    """
    Find the navigation path between two map nodes in the Pokémon world.

    This tool loads the prebuilt map graph from disk and computes the path
    between the given start and end map names. The path is determined using
    the underlying MapGraph's pathfinding logic (typically BFS/A*, depending
    on its implementation).

    Parameters
    ----------
    start : str
        The name/label of the starting map (e.g., "PALLET_TOWN", "VIRIDIAN_CITY").
    end : str
        The name/label of the destination map.

    Returns
    -------
    list[str]
        An ordered list of map names representing the path from `start` to `end`.
        The first element is `start`, the last is `end`. Returns `None` if no path
        exists or either map is invalid.

    Notes
    -----
    - This function reads the map graph from
      `src/pokemon_agent/utils/ref_data/maps/map_graph.json`.
    - The function does not validate whether the map names exist; invalid names
      may result in `None` or an exception depending on the MapGraph implementation.
    - Designed for use as a tool in an LLM agent: provide clear, valid map names
      when calling.
    """
    with open("src/pokemon_agent/utils/ref_data/maps/map_graph.json") as f:
        MAP_GRAPH = json.load(f)
    g = MapGraph.from_dict(MAP_GRAPH)

    return g.find_path(start, end)

TOOLS = {
    "get_directions": get_directions,
}


# ---------------------------
# 2. LM Studio LLM (no tool binding needed!)
# ---------------------------

llm = ChatOpenAI(
    api_key="not-needed",
    base_url="http://localhost:1234/v1",
    model="qwen/qwen3-vl-4b",
    temperature=0,
)


# ---------------------------
# 3. Agent State
# ---------------------------

class AgentState(TypedDict):
    messages: List[Any]


# ---------------------------
# 4. LLM Node (ReAct Prompting)
# ---------------------------

REACT_SYSTEM = """
You are a ReAct agent.

You must always follow this reasoning format:

Thought: <your reasoning>
Action: <tool_name>(arg1="...", arg2=123)

After the system provides the Observation, continue the next step:

Thought: <reason again>
Action: <next tool>

When you are ready to answer the user's question, output:

Final Answer: <your answer>

Valid tools:
- get_directions(start: str, end: str): format start and end strings as all caps, snakecase like this 'PALLET_TOWN'

Never output anything except Thought/Action/Observation/Final Answer.
"""


def llm_node(state: AgentState):
    # Insert the ReAct system prompt
    msgs = [SystemMessage(content=REACT_SYSTEM)] + state["messages"]
    response = llm.invoke(msgs)
    return {"messages": state["messages"] + [response]}


# ---------------------------
# 5. Parse "Action: tool(arg=...)" from the LLM
# ---------------------------

ACTION_RE = re.compile(r"Action:\s*([a-zA-Z_]\w*)\((.*)\)")


def parse_action(text: str):
    match = ACTION_RE.search(text)
    if not match:
        return None

    tool_name = match.group(1)
    raw_args = match.group(2).strip()

    # Convert to Python dict safely
    # Example: a=12, b=4   → {"a": 12, "b": 4}
    args = {}
    if raw_args:
        for part in raw_args.split(","):
            key, val = part.split("=")
            key = key.strip()
            val = val.strip().strip("\"'")
            # try cast to number
            if val.replace(".", "", 1).isdigit():
                val = float(val)
            args[key] = val

    return tool_name, args


# ---------------------------
# 6. Router
# ---------------------------

def router(state: AgentState):
    last = state["messages"][-1].content

    if "Final Answer:" in last:
        return "end"

    if "Action:" in last:
        return "tool"

    return "llm"


# ---------------------------
# 7. Tool Node
# ---------------------------

def tool_node(state: AgentState):
    last = state["messages"][-1].content
    parsed = parse_action(last)

    if not parsed:
        # No valid action → go back to LLM
        obs = "Invalid action format."
    else:
        tool_name, args = parsed
        tool_fn = TOOLS.get(tool_name)
        if not tool_fn:
            obs = f"Unknown tool: {tool_name}"
        else:
            try:
                result = tool_fn(**args)
                obs = str(result)
            except Exception as e:
                obs = f"Error: {e}"

    # append observation
    observation_msg = f"Observation: {obs}"
    return {"messages": state["messages"] + [HumanMessage(content=observation_msg)]}


# ---------------------------
# 8. Build the Graph
# ---------------------------

graph = StateGraph(AgentState)

graph.add_node("llm", llm_node)
graph.add_node("tool", tool_node)

graph.set_entry_point("llm")

# graph.add_edge("llm", router)
graph.add_edge("tool", "llm")
# graph.add_conditional_edges("llm", END, lambda s: router(s) == "end")
graph.add_conditional_edges("llm", router, 
                               {
                                "tool":"tool", 
                                "end":END
                                })

tool_app = graph.compile()


def run(tool_app, tool_call):
    state = {
        "messages": [
            HumanMessage(content=tool_call)
        ]
    }
    for event in tool_app.stream(state):
        node, update = next(iter(event.items()))
        # msg = update["messages"][-1]
        msg = update["messages"][-2]
    return msg.content.split('Observation: ')[1]


# ---------------------------
# 9. Run Example
# ---------------------------



if __name__ == "__main__":
    # state = {
    #     "messages": [
    #         HumanMessage(content="Get from Pallet Town to Pewter City")
    #     ]
    # }

    # print("\nRunning pure ReAct agent...\n")

    # for event in tool_app.stream(state):
    #     node, update = next(iter(event.items()))
    #     msg = update["messages"][-1]
    #     print(f"[{node.upper()}] → {msg.content}")

    # print("\nDone.")

    messages = run(tool_app, "Get from Pallet Town to Pewter City")
    print(messages)





