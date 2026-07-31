from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Annotated
from core_tools.write_to_file import write_to_file
from core_tools.create_file import create_file
from core_tools.include_tool import include_tool
from core_tools.list_tools import list_tools
from core_tools.search_web import search_web
from core_tools.read_file import read_file
# ==============================================================================
# 1. STATE SCHEMA
# ==============================================================================
# For agents, state typically contains a list of messages.
# The `add_messages` reducer appends new messages to the conversation.

class AgentState(TypedDict):
    """
    State for our ReAct agent.

    - messages: Conversation history (uses add_messages reducer to append)
    """
    messages: Annotated[list, add_messages]


# ==============================================================================
# 2. TOOLS
# ==============================================================================
# Tools are Python functions. The LLM reads their docstrings to understand
# what they do and when to use them.

tools = [write_to_file, create_file, include_tool, list_tools, search_web, read_file]

# ==============================================================================
# 3. NODES
# ==============================================================================

def agent_node(state: AgentState) -> dict:
    """
    The agent decides: call a tool or respond directly?

    This is the "Reasoning" part of ReAct.
    """
    # Initialize LLM with Ollama (better tool calling support than LM Studio)
    llm = ChatOllama(
        model="gemma4",  # Use whatever model you pulled
        temperature=0
    )
    llm_with_tools = llm.bind_tools(tools)

    # Get the conversation history
    messages = state["messages"]

    # Add a system message to guide behavior
    # Explicitly instruct to call ONE tool at a time (local model limitation)
    system_msg = SystemMessage(
        content="""You are a helpful and highly disciplined software development assistant. Your primary goal is to analyze user requests, determine the necessary tools (creation, inclusion, usage), and write functional code to fulfill the request completely.

    ==================================
    ✨ MANDATORY WORKFLOW PROTOCOL - FOLLOW EXACLY ✨
    ==================================
    This protocol dictates your steps for complex tasks:

    STEP 0: ANALYZE THE TASK
    - Use 'search_web' first if the task requires external knowledge (e.g., current library versions, setup instructions).

    STEP 1: INITIAL TOOL CHECK (BEST PRACTICE)
    - To ensure you know all capabilities, ALWAYS begin by calling 'list_tools()' to check the existing tool set.

    STEP 2: CREATE FILES (If needed)
    - If a new tool is required, use 'create_file' in the designated 'created_tools' directory.
    - The file name MUST match the function name of the tool you want to create.
    - Do not try to create one tool twice! Use write_to_file instead.
    - Include the complete and accurate docstring detailing ALL arguments and functionality.
    - IMPORTANT: You can import existing tools into other tools using 'import created_tools/{tool_name}'!
    - IMPORTANT: ALL TOOLS MUST BE CREATED IN CREATED_TOOLS DIRECTORY!!!
    Example: 'created_tools/tool.py' - RIGHT, 'tool.py' - WRONG
    - CRITICAL: USE CORRECT FORMATS WHEN WRITING A TOOL! Example: 
    n: The non-negative integer for which to calculate the factorial. - RIGHT
    n (int): The non-negative integer for which to calculate the factorial. - WRONG!

    STEP 3: INCLUDE TOOL (CRITICAL - DO NOT SKIP!)
    - After SUCCESSFULLY executing a 'create_file', OR when you intend to use any tool (existing or newly created), calling 'include_tool' is **MANDATORY**.
    - You must call 'include_tool' for *every* single piece of functionality you want the system to be aware of. If you create 3 tools, you MUST execute 'include_tool' three times before proceeding.

    STEP 4: EXECUTE THE TASK
    - Now that all necessary tools are available, use them in sequence to complete the task fully.
    - You can and should use multiple tools (creation, web search, execution) to achieve the final result.
    - If some tools fail, you should analyze AND rewrite them to accomplish user's task
    ==================================
    📜 GENERAL OPERATIONAL RULES 📜
    -----------------------------
    1. **Completion:** Always complete the user's full request. If they ask to "save" something, you must use your file writing tools until it is successfully saved.
    2. **Dependencies:** Treat 'include_tool' as an inseparable part of tool creation and usage. Failing to include a tool means failure.
    3. **Execution Order Priority:** The logical sequence remains: Analyze $\rightarrow$ (List Tools) $\rightarrow$ Create $\rightarrow$ Include $\rightarrow$ Use / Execute. Never skip the inclusion step!
    4. **Code Quality:** All generated code must be clean, functional, and ready to run. Do not use placeholders.
    5. **Reading and optimisation:** Use read_file tool to read the tools you use and optimize them if needed.
    """
    )

    # LLM decides what to do next
    response = llm_with_tools.invoke([system_msg] + messages)

    print(f"\n[AGENT] Response type: {response.__class__.__name__}")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"[AGENT] Wants to call: {[tc['name'] for tc in response.tool_calls]}")
    else:
        print(f"[AGENT] Final answer: {response.content[:50]}...")

    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    """
    Execute the tools that the agent requested.

    This is the "Acting" part of ReAct.
    """
    from langchain_core.messages import ToolMessage
    import __main__

    messages = state["messages"]
    last_message = messages[-1]

    # Execute each tool call
    tool_results = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        coerced_args = tool_args

        # Find and execute the tool
        tool_func = None

        # First check in main.tools (which includes dynamically added tools)
        if hasattr(__main__, 'tools'):
            for t in __main__.tools:
                if hasattr(t, '__name__') and t.__name__ == tool_name:
                    tool_func = t
                    break
        try:
            result = tool_func(**coerced_args)
        except TypeError as e:
            print(f"[TOOL ERROR] Could not execute {tool_name}. Missing required arguments or incorrect types. Error: {e}")
            # Return a failure message instead of crashing
            result = f"ERROR: Tool execution failed due to missing or incorrect argument(s). Details: {str(e)}. Try to call the tool in different way or rewrite it"


        print(f"[TOOL] {tool_name}({coerced_args}) = {result}")

        # Create a ToolMessage with the result
        tool_results.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
        )

    return {"messages": tool_results}


# ==============================================================================
# 4. ROUTING LOGIC
# ==============================================================================

def should_continue(state: AgentState) -> str:
    """
    Decides whether to continue (call tools) or end (return answer).

    This creates the loop: agent → tools → agent → tools → ... → end
    """
    last_message = state["messages"][-1]

    # If the LLM made tool calls, execute them
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"

    # Otherwise, we're done
    return "end"


# ==============================================================================
# 5. BUILD THE GRAPH
# ==============================================================================

def create_react_agent():
    """
    Constructs the ReAct agent graph:

    START → agent → (tools → agent)* → END

    The agent decides whether to call tools or finish.
    """
    # Initialize with checkpointing (state persistence)
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # Start with the agent
    graph.add_edge(START, "agent")

    # After tools, always go back to agent (it needs to see the results)
    graph.add_edge("tools", "agent")

    # Agent decides: continue to tools or end
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    # Compile with checkpointing
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# ==============================================================================
# 6. RUN THE AGENT
# ==============================================================================

def run_agent(query):


    app = create_react_agent()

    config = {"configurable": {"thread_id": f"tool creation"}}

    try:
        result = app.invoke(
                {"messages": [HumanMessage(content=   f"{query} + DO NOT FORGET TO LIST TOOLS! INCLUDE ALL THE TOOLS YOU USE!!! If you're not sure the folder you want to write something in exists, create it instead. If some tools fail, you should analyze AND rewrite them to accomplish user's task")]},
            config=config
        )
        print(f"Final answer: {result['messages'][-1].content}")
    except Exception as e:
        print(f"ERROR in task: {e}")
        result = app.invoke(
            {"messages": [HumanMessage(
                content=f"Caught an error {e} while completing {query}. Analyze the problem and finish the task")]},
            config=config
        )
        print(f"Final answer: {result['messages'][-1].content}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    query = input("Enter query: ")
    run_agent(query)