import gradio as gr
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from typing import TypedDict, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define State
class State(TypedDict):
    text: str
    classification: str
    entities: List[str]
    summary: str

# Define Node Functions
def classification_node(state: State):
    """Classify the text into categories."""
    prompt = PromptTemplate(
        input_variables=["text"],
        template="Classify the following text into one of the categories: News, Blog, Research, or Other. \n\nText:{text}\n\nCategory:"
    )
    message = HumanMessage(content=prompt.format(text=state["text"]))
    classification = llm.invoke([message]).content.strip()
    return {"classification": classification}

def entity_extraction_node(state: State):
    """Extract entities from the text."""
    prompt = PromptTemplate(
        input_variables=["text"],
        template="Extract all the entities (Person, Organization, Location) from the following text. Provide the result as a comma-separated list. \n\nText:{text}\n\nEntities:"
    )
    message = HumanMessage(content=prompt.format(text=state["text"]))
    entities = llm.invoke([message]).content.strip().split(", ")
    return {"entities": entities}

def summarization_node(state: State):
    """Summarize the text."""
    prompt = PromptTemplate(
        input_variables=["text"],
        template="Summarize the following text in one short sentence. \n\nText:{text}\n\nSummary:"
    )
    message = HumanMessage(content=prompt.format(text=state["text"]))
    summary = llm.invoke([message]).content.strip()
    return {"summary": summary}

# Initialize LLM
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    temperature=0,
    groq_api_key=groq_api_key,
    model_name="gemma2-9b-it"
)

# Build Workflow
workflow = StateGraph(State)
workflow.add_node("classification_node", classification_node)
workflow.add_node("entity_extraction_node", entity_extraction_node)
workflow.add_node("summarization_node", summarization_node)
workflow.set_entry_point("classification_node")
workflow.add_edge("classification_node", "entity_extraction_node")
workflow.add_edge("entity_extraction_node", "summarization_node")
workflow.add_edge("summarization_node", END)
app = workflow.compile()

# Define Gradio Interface
def process_text(input_text):
    state_input = {"text": input_text}
    result = app.invoke(state_input)
    return result["classification"], ", ".join(result["entities"]), result["summary"]

demo = gr.Interface(
    fn=process_text,
    inputs=gr.Textbox(lines=5, placeholder="Enter text here..."),
    outputs=[
        gr.Textbox(label="Classification"),
        gr.Textbox(label="Entities"),
        gr.Textbox(label="Summary")
    ],
    title="Text Analysis with LangGraph",
    description="Experience the power of AI with our Text Analysis tool! Classify text, extract key entities, and generate concise summaries effortlessly. Perfect for researchers, writers, and AI enthusiasts alike."
)

demo.launch()
