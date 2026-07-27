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

tools = [write_to_file, create_file, include_tool, list_tools, search_web]

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
        content="""You are a helpful tool creation assistant.
                **MANDATORY WORKFLOW - FOLLOW EXACTLY:**
STEP 0: ANALYZE THE TASK
- You can use search_web if needed

STEP 1: SEARCH
- ALWAYS call 'list_tools' first to check existing tools
IF YOU WANT TO USE EXISTING TOOL, ALWAYS INCLUDE IT using include_tool!!!
STEP 2: CREATE (if needed)
- Create Python files using 'create_file' in 'created_tools' directory
- File name MUST match function name
- Include complete docstring with ALL arguments
- NO example usage in file
- NO 'returns' in docstring

STEP 3: INCLUDE (CRITICAL - DO NOT SKIP!)
- **IMMEDIATELY after EACH 'create_file'** OR WHEN YOU WANT TO USE EXISTING TOOL, call 'include_tool' for that tool
- This is MANDATORY, not optional
- If you create 3 tools, you MUST call 'include_tool' 3 times

STEP 4: EXECUTE
- Now use all the needed tools to complete the task
- You CAN use multiple tools to complete the task.
- DO NOT SKIP THE TASK MID-WAY!
- You may use any tools on this step - create files, search web if user told you to.

**VALIDATION RULES:**
- If you forget to include a tool, you will FAIL the task
- Treat 'include_tool' as part of tool creation - they are inseparable
- ALWAYS complete the user's full task - if he says to **save** something in a file - use your tools to do it!!!
**REMEMBER:**
- Create → Include → Use → Execute (in that order, never skip 'Include')
- Multiple tools = multiple include_tool calls
- Tool names must match tool file names!!!
- External libraries are pre-installed
- No placeholders - write working code
- You need to fully complete user's task - use multiple tools in sequence if needed
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
            result = f"ERROR: Tool execution failed due to missing or incorrect argument(s). Details: {str(e)}"


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

def main():


    app = create_react_agent()

    config = {"configurable": {"thread_id": f"tool creation"}}

    try:
        result = app.invoke(
                {"messages": [HumanMessage(content=   """how to install numpy?""")]},
            config=config
        )
        print(f"Final answer: {result['messages'][-1].content}")
    except Exception as e:
        print(f"ERROR in task: {e}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()