import os
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
from core_tools.check_and_manage_dependencies import check_and_manage_dependencies
from support_classes.tool_registry import registry
from dotenv import load_dotenv
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

registry.register_tool(write_to_file)
registry.register_tool(create_file)
registry.register_tool(include_tool)
registry.register_tool(list_tools)
registry.register_tool(search_web)
registry.register_tool(read_file)
registry.register_tool(check_and_manage_dependencies)
# ==============================================================================
# 3. NODES
# ==============================================================================

def agent_node(state: AgentState) -> dict:
    """
    The agent decides: call a tool or respond directly?

    This is the "Reasoning" part of ReAct.
    """
    # Initialize LLM with Ollama (better tool calling support than LM Studio)
    load_dotenv()
    llm = ChatOllama(
        model=os.getenv("MODEL"),  # Use whatever model you pulled
        temperature=os.getenv("TEMPERATURE")
    )
    llm_with_tools = llm.bind_tools(registry.list_tools())

    # Get the conversation history
    messages = state["messages"]

    # Add a system message to guide behavior
    # Explicitly instruct to call ONE tool at a time (local model limitation)
    system_msg = SystemMessage(
        content="""You are a helpful and highly disciplined software development assistant. Your primary goal is to analyze user requests, determine the necessary tools (creation, inclusion, usage), and write functional code to fulfill the request completely.

    ==================================
    ✨ MANDATORY WORKFLOW PROTOCOL - FOLLOW EXACTLY ✨
    ==================================
    This protocol dictates your steps for complex tasks:

    STEP 0: ANALYZE THE TASK
    - Use 'search_web' first if the task requires external knowledge (e.g., current library versions, setup instructions).
    IMPORTANT: When adding a tool with external dependency, ALWAYS call check_and_manage_dependencies. It will install a dependency in case of its unexistence.
    STEP 1: INITIAL TOOL CHECK (BEST PRACTICE)
    - To ensure you know all capabilities, ALWAYS begin by calling 'list_tools()' to check the existing tool set.
    IMPORTANT! Include all the tools you got on this step using 'include_tool' if you need them! This is !!!MANDATORY!!!
    STEP 2: CREATE FILES (If needed)
    - If a new tool is required, use 'create_file' in the designated 'created_tools' directory.
    - The file name MUST match the function name of the tool you want to create. (!!! MANDATORY !!!)
    - Do not try to create one tool twice! Use write_to_file instead.
    - Include the complete and accurate docstring detailing ALL arguments and functionality.
    - IMPORTANT: You can import existing tools into other tools using 'import created_tools/{tool_name}'!
    - IMPORTANT: ALL TOOLS MUST BE CREATED IN CREATED_TOOLS DIRECTORY!!!
    Example: 'created_tools/tool.py' - RIGHT, 'tool.py' - WRONG (!!! MANDATORY !!!)
    - CRITICAL: USE CORRECT FORMATS WHEN WRITING A TOOL! Example: 
    n: The non-negative integer for which to calculate the factorial. - RIGHT
    n (int): The non-negative integer for which to calculate the factorial. - WRONG!

    STEP 3: INCLUDE TOOL (CRITICAL - DO NOT SKIP!)
    - After SUCCESSFULLY executing a 'create_file', OR when you intend to use any tool (existing or newly created), calling 'include_tool' is !!! MANDATORY !!!.
    - You must call 'include_tool' for *every* single piece of functionality you want the system to be aware of. If you create 3 tools, you MUST execute 'include_tool' three times before proceeding. THIS IS !!!MANDATORY!!!

    STEP 4: EXECUTE THE TASK
    - Now that all necessary tools are available, use them in sequence to complete the task fully.
    - You can and should use multiple tools (creation, web search, execution) to achieve the final result.
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
    import concurrent.futures
    messages = state["messages"]
    last_message = messages[-1]

    # Execute each tool call
    tool_results = []
    tasks = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tasks.append((tool_name, tool_args, tool_call))

    def execute_tool(tool_name, tool_args, tool_call):
        coerced_args = tool_args
        tool_func = None
        result = None

        # Find the actual function object
        for t in registry.list_tools():
            if hasattr(t, '__name__') and t.__name__ == tool_name:
                tool_func = t
                break
        try:
            if callable(tool_func):
                result = tool_func(**coerced_args)
            else:
                print(f"[TOOL ERROR] Tool '{tool_name}' function not found or is not callable.")
                return f"ERROR: The requested tool '{tool_name}' could not be executed because it was not defined or properly included in the system's accessible functions. Details: Check tool name and ensure inclusion steps are followed."

        except TypeError as e:
            print(
                f"[TOOL ERROR] Could not execute {tool_name}. Missing required arguments or incorrect types. Error: {e}")
            return f"ERROR: Tool execution failed due to missing or incorrect argument(s). Details: {str(e)}. Try to call the tool in different way or rewrite it"

        except Exception as e:
            print(f"[TOOL CRASH] An unexpected error occurred during execution of {tool_name}. Error: {e}")
            # Catch any other exceptions for robustness
            return f"ERROR: Tool '{tool_name}' crashed due to an unhandled exception. Details: {type(e).__name__}: {str(e)}"

        finally:
            print(f"[TOOL] {tool_name}({coerced_args}) = {result}")

        # Create and return the ToolMessage
        return ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"]
        )

    with concurrent.futures.ThreadPoolExecutor() as executor:

        future_to_task = {executor.submit(execute_tool, name, args, call): (name, args) for name, args, call in
                              tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            try:
                # The result here is the ToolMessage object returned by execute_tool
                result_message = future.result()
                tool_results.append(result_message)
            except Exception as e:
                print(f"[THREAD EXCEPTION] A critical failure occurred while retrieving results: {e}")
                # If the thread itself fails to complete, we handle it gracefully here
                pass

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

    config = {"configurable": {"thread_id": f"tool creation {hash(query)}"}}
    attempt = 0
    try:
        result = app.invoke(
                {"messages": [HumanMessage(content= query)]},
            config=config
        )
        print(f"Final answer: {result['messages'][-1].content}")
    except Exception as e:
        attempt+=1
        print(f"ERROR in task: {e}")
        if attempt <= 3:
            result = app.invoke(
            {"messages": [HumanMessage(
                    content=f"Caught an error {e} while completing {query}. Analyze the problem and finish the task")]},
                config=config
            )
            print(f"Final answer: {result['messages'][-1].content}")
        else:
            print(f"Caught an error {e} while completing {query} and exceeded the amount of retries.")
    print("=" * 60 + "\n")
    return result['messages'][-1].content

if __name__ == "__main__":
    query = input("Enter query: ")
    run_agent(query)