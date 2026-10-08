import json
import logging
import uuid

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ai_agent.assistant.tools import get_gemini_tools

logger = logging.getLogger(__name__)

class AssistantAgent:
    def __init__(self, model_id: str = "gemini-3.5-flash-lite", api_key: str | None = None):
        self.model_id = model_id
        
        # Initialize Langchain Chat Model
        self.llm = ChatGoogleGenerativeAI(
            model=model_id,
            api_key=api_key,
            temperature=0.0
        )
        
        self.tools = get_gemini_tools()

        system_instruction = (
            "You are a Supply Chain Intelligence Assistant. "
            "Your domain is strictly restricted to supply-chain operations, shipments, route statistics, and predicting shipment delays. "
            "For off-domain requests, briefly refuse and explain your supported domain. "
            "You must not fabricate any shipment facts or route statistics. All factual claims about shipments or routes must be grounded in the tool results you receive. "
            "When you provide information derived from a tool, you MUST include visible attribution in your response. For example: `Source: get_route_stats` or `Source: query_shipments` or `Source: predict_delay`. "
            "IMPORTANT: Tools like get_route_stats and query_shipments require exact 5-letter UN/LOCODE port codes (e.g. CNSHA for Shanghai). If a user provides a city name, you MUST use the search_ports tool first to find the correct port_code before querying shipments or routes."
        )

        self.agent_executor = create_agent(
            model=self.llm, 
            tools=self.tools,
            system_prompt=system_instruction
        )

    def query(self, user_message: str, session_id: str | None = None) -> str:
        """Process a user query using Langchain AgentExecutor."""
        session_id = session_id or str(uuid.uuid4())
        
        log_entry = {
            "session_id": session_id,
            "user_prompt": user_message,
            "tool_calls": [],
        }

        try:
            result = self.agent_executor.invoke({"messages": [HumanMessage(content=user_message)]})
            
            # Log intermediate steps (tool calls)
            for message in result.get("messages", []):
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        log_entry["tool_calls"].append({
                            "tool_name": tool_call.get("name"),
                            "tool_arguments": tool_call.get("args", {})
                        })
                
            final_content = result["messages"][-1].content
            if isinstance(final_content, list):
                final_answer = " ".join([c.get("text", "") for c in final_content if c.get("type") == "text"])
            else:
                final_answer = final_content
        except Exception as e:
            logger.error(f"Error executing agent: {e}")
            final_answer = f"Error: {e}"

        log_entry["final_answer"] = final_answer
        logger.info(json.dumps(log_entry))

        return final_answer
