import gradio as gr
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from typing import TypedDict
import re
import os

from dotenv import load_dotenv
load_dotenv()

# Define State
class State(TypedDict):
    essay: str
    relevance_score: float
    grammar_score: float
    structure_score: float
    depth_score: float
    final_score: float

# Define Node Functions
def extract_score(content: str) -> float:
    match_ = re.search(r"Score:\s*(\d+(\.\d+)?)", content)
    if match_:
        return float(match_.group(1))
    raise ValueError(f"Could not extract score from: {content}")

def check_relevance(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Analyze the relevance of the following essay to the given topic. "
        "Provide a relevance score between 0 and 1. "
        "Your response should start with 'Score: ' followed by numeric score, "
        "then provide your explanation.\n\nEssay: {essay}"
    )
    result = llm.invoke(prompt.format(essay=state["essay"]))
    try:
        state["relevance_score"] = extract_score(result.content)
    except ValueError as e:
        print(f"Error in check relevance: {e}")
        state["relevance_score"] = 0.0
    return state

def check_grammar(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Analyze the grammar and language of the following essay. "
        "Provide a grammar score between 0 and 1. "
        "Your response should start with 'Score: ' followed by numeric score, "
        "then provide your explanation.\n\nEssay: {essay}"
    )
    result = llm.invoke(prompt.format(essay=state["essay"]))
    try:
        state["grammar_score"] = extract_score(result.content)
    except ValueError as e:
        print(f"Error in check grammar: {e}")
        state["grammar_score"] = 0.0
    return state

def analyze_structure(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Analyze the structure of the following essay. "
        "Provide a structure score between 0 and 1. "
        "Your response should start with 'Score: ' followed by numeric score, "
        "then provide your explanation.\n\nEssay: {essay}"
    )
    result = llm.invoke(prompt.format(essay=state["essay"]))
    try:
        state["structure_score"] = extract_score(result.content)
    except ValueError as e:
        print(f"Error in structure_score: {e}")
        state["structure_score"] = 0.0
    return state

def evaluate_depth(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Analyze the depth of analysis in the following essay. "
        "Provide a depth score between 0 and 1. "
        "Your response should start with 'Score: ' followed by numeric score, "
        "then provide your explanation.\n\nEssay: {essay}"
    )
    result = llm.invoke(prompt.format(essay=state["essay"]))
    try:
        state["depth_score"] = extract_score(result.content)
    except ValueError as e:
        print(f"Error in depth_score: {e}")
        state["depth_score"] = 0.0
    return state

def calculate_final_score(state: State) -> State:
    state["final_score"] = (
        state["relevance_score"] * 0.3 +
        state["grammar_score"] * 0.2 +
        state["structure_score"] * 0.2 +
        state["depth_score"] * 0.3
    )
    return state

# Initialize LLM
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    temperature=0,
    groq_api_key=groq_api_key,
    model_name="llama-3.3-70b-versatile"
)

# Build Workflow
workflow = StateGraph(State)
workflow.add_node("check_relevance", check_relevance)
workflow.add_node("check_grammar", check_grammar)
workflow.add_node("analyze_structure", analyze_structure)
workflow.add_node("evaluate_depth", evaluate_depth)
workflow.add_node("calculate_final_score", calculate_final_score)

workflow.add_conditional_edges(
    "check_relevance",
    lambda x: "check_grammar" if x["relevance_score"] > 0.5 else "calculate_final_score"
)

workflow.add_conditional_edges(
    "check_grammar",
    lambda x: "analyze_structure" if x["grammar_score"] > 0.5 else "calculate_final_score"
)

workflow.add_conditional_edges(
    "analyze_structure",
    lambda x: "evaluate_depth" if x["structure_score"] > 0.5 else "calculate_final_score"
)

workflow.add_conditional_edges(
    "evaluate_depth",
    lambda x: "calculate_final_score"
)

workflow.set_entry_point("check_relevance")
workflow.add_edge("calculate_final_score", END)



app = workflow.compile()

# Define Gradio Interface
def grade_essay_interface(essay: str):
    initial_state = State(
        essay=essay,
        relevance_score=0.0,
        grammar_score=0.0,
        structure_score=0.0,
        depth_score=0.0,
        final_score=0.0
    )
    result = app.invoke(initial_state)
    return (
        f"Final Score: {result['final_score']:.2f}",
        f"Relevance Score: {result['relevance_score']:.2f}",
        f"Grammar Score: {result['grammar_score']:.2f}",
        f"Structure Score: {result['structure_score']:.2f}",
        f"Depth Score: {result['depth_score']:.2f}"
    )


demo = gr.Interface(
    fn=grade_essay_interface,
    inputs=gr.Textbox(lines=10, placeholder="Paste your essay here..."),
    outputs=[
        gr.Textbox(label="Final Score"),
        gr.Textbox(label="Relevance Score"),
        gr.Textbox(label="Grammar Score"),
        gr.Textbox(label="Structure Score"),
        gr.Textbox(label="Depth Score")
    ],
    title="Essay Grading System",
    description="Grade essays based on relevance, grammar, structure, and depth using AI-powered analysis."
)

demo.launch()
