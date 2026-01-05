from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from typing import Optional

class TestGenerationState(BaseModel):
    requirement: Optional[str] = None
    browser: Optional[str] = None
    playwright_script: Optional[str] = None
    execution_result: Optional[str] = None
    analysis: Optional[str] = None
    test_stats: Optional[dict] = None
    test_stats_report: Optional[str] = None

def build_graph():
    from agents.playwright_script_generator import generate_playwright_script
    from agents.script_executor import execute_script
    from agents.script_debugger import debug_script
    from agents.stats_aggregator import aggregate_stats

    builder = StateGraph(state_schema=TestGenerationState)

    builder.add_node("script", RunnableLambda(generate_playwright_script))
    builder.add_node("execute", RunnableLambda(execute_script))
    builder.add_node("debug", RunnableLambda(debug_script))
    builder.add_node("reexecute", RunnableLambda(execute_script))
    builder.add_node("stats_aggregator", RunnableLambda(aggregate_stats))
    builder.add_node("done", lambda state: state)

    builder.set_entry_point("script")
    builder.add_edge("script", "execute")

    def needs_debugging(state):
        return state.execution_result and "[FAIL]" in state.execution_result

    builder.add_conditional_edges(
        "execute",
        needs_debugging,
        {
            True: "debug",
            False: "stats_aggregator"
        }
    )

    builder.add_edge("debug", "reexecute")
    builder.add_edge("reexecute", "stats_aggregator")
    builder.add_edge("stats_aggregator", "done")

    builder.set_finish_point("done")

    return builder.compile()
