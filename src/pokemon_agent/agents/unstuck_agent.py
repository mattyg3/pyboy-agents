# from .init_llm import llm_model_cv
import lmstudio as lms
# with lms.Client() as client:
#     llm_model_cv = client.llm.model("qwen/qwen3-vl-8b@q4_k_m")
# llm_model_cv = lms.llm("qwen/qwen3-vl-8b@q4_k_m")
# llm_model_cv = lms.llm("mistralai/magistral-small-2509") 
llm_model_cv = lms.llm("google/gemma-3-4b")
# from lmstudio import LMStudioClient
# client = LMStudioClient()
# llm_model_cv = client.llm.model("qwen/qwen3-vl-8b@q4_k_m") 
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
import cv2

# ------ Define State ------
class AgentState(TypedDict):
    messages: list[dict[str, Any]]
    screenshot: Any
    map_render: Any
    attempted_goal: str
    unstuck_thoughts: list[dict[str, Any]]
    corrective_action: list[Any]
    prev_corrective_action: list[Any]


def create_unstuck_agent_state(
        messages=[],
        screenshot=None,
        map_render=None,
        attempted_goal=None,
        unstuck_thoughts=[],
        corrective_action=[],
        prev_corrective_action=[],


) -> AgentState:
    return AgentState(
        messages=messages, 
        screenshot=screenshot,
        map_render=map_render,
        attempted_goal=attempted_goal,
        unstuck_thoughts=unstuck_thoughts,
        corrective_action=corrective_action,
        prev_corrective_action=prev_corrective_action,
    )

class UnstuckAgent():
    def __init__(self, pyboy):
        self.pyboy = pyboy

    def unstuck_agent(self, state):
        # frame = self.pyboy.screen.ndarray
        # cv2.imwrite("dev_files/unstuck_agent_test_frame.png", frame)
        # # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # # cv2.imwrite("dev_files/unstuck_agent_test_frame_gray.png", gray)
        # # pyboy_screenshot = cv2.imread("dev_files/unstuck_agent_test_frame.png")
        # pyboy_screenshot = lms.prepare_image("dev_files/unstuck_agent_test_frame.png")
        state["prev_corrective_action"] = state["corrective_action"]

        sys_prompt = f"""
        # Role
        You are playing a Pokemon game and need to give movement instructions to reach the goal.

        # Task
        - Given an image of the "Current Game Screen" and a "Desired Goal", provide the needed movement instructions to get to the desired goal. 
        - **ONLY** provide movement instructions from the "Movement Dictionary". 
        - "Current Full Map Render" has the player current position marked in **RED** and the current goal marked in **BLUE**

        # Movement Dictionary
            - LEFT
            - RIGHT
            - UP
            - DOWN

        # Inputs
            - Current Game Screen: provided as an attachment
            - Current Full Map Render: provided as an attachment (not provided if player is indoors)
            - Desired Goal: {state['attempted_goal']}
            - Previous Unsuccessful Answer: {state['prev_corrective_action']}

        # Output
        **ONLY** a string of ordered movement instructions like this: "LEFT; LEFT; LEFT; UP;"



        """
        #         # Output Format
        # "ANSWER: LEFT; LEFT; LEFT; UP"
        print("RUNNING UNSTUCK_AGENT")
        # response = llm_model_cv.respond(sys_prompt)
        chat = lms.Chat()
        if state['map_render']:
            chat.add_user_message(sys_prompt, images=[state['screenshot'], state['map_render']])
        else:
            chat.add_user_message(sys_prompt, images=[state['screenshot']])
        result = llm_model_cv.respond(chat)
        result_content = result.content
        # print("COMPLETED UNSTUCK_AGENT")
        # print(f"\n\n\n\nRESULT: {result}\n\n\n\n")
        print(f"UNSTUCK_AGENT RESULT CONTENT: {result_content}")
        # print(f"\n\n\n\nRESULT CONTENT TYPE: {type(result_content)}\n\n\n\n")

        # if "</think>" in result_content:
        #     thinking = result_content.split("</think>", 1)[0].strip()
        #     response = result_content.split("</think>", 1)[1].strip()
        # else:
        #     response = result_content.strip()

        # Convert str to list and convert to format #{'type': 'GO_DOWN'}

        # ```plaintext
        # UP
        # ```
        # response = result_content.split("```", 1)[1].split("\n")[1].replace("```", "").strip()
        # response = result_content.split("OUTPUT:", 1)[1].split("\"")[0].strip()
        # print(f"RESPONSE: {response}")

        response = result_content

        response_list = [f"GO_{x.upper().strip()}" for x in response.split(';') if x.strip()]
        response_list = [{'type': x} for x in response_list]
        
        state["messages"].append({"role":"unstuck", "content": response_list})
        state["corrective_action"] = response_list
        state["unstuck_thoughts"].append({"content": result})

        return state
    
    def compile_workflow(self, state: AgentState):
        # ------ Define Nodes ------
        def unstuck_node(state: AgentState):
            return self.unstuck_agent(state)
        # ------ Define Workflow ------
        workflow = StateGraph(state_schema=AgentState)
        workflow.add_node("start", unstuck_node)
        workflow.set_entry_point("start")
        workflow.add_edge("start", END)
        # ------ Compile Workflow ------
        self.app = workflow.compile()