"""LangGraph workflow for evidence-based resume analysis."""

from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


MODEL_NAME = "openai/gpt-oss-20b"


class CandidateSnapshot(BaseModel):
    """Expected fields for the candidate-profile section."""
    profile_summary: str = Field(description="Two-sentence factual candidate summary")
    experience_level: str = Field(description="Entry, junior, mid, senior, lead, or unclear")
    likely_target_role: str = Field(description="Most likely role targeted by this resume")
    core_skills: list[str] = Field(description="Important skills explicitly present")
    strongest_evidence: list[str] = Field(description="Strong resume evidence and achievements")


class ResumeAnalysis(BaseModel):
    """Structured format that the Groq model must return."""
    executive_summary: str = Field(description="Balanced overall resume assessment")
    resume_score: int = Field(ge=0, le=100, description="Resume quality score, not hiring score")
    pros: list[str] = Field(min_length=3, description="Evidence-based strengths")
    cons: list[str] = Field(min_length=3, description="Evidence-based weaknesses or gaps")
    improvement_plan: list[str] = Field(min_length=3, description="Specific prioritized improvements")
    candidate_snapshot: CandidateSnapshot


class ResumeState(TypedDict, total=False):
    """Information passed from one LangGraph node to the next."""
    resume_text: str
    analysis: ResumeAnalysis


ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a rigorous resume-review agent. Analyze only the supplied
resume. Never invent employment, skills, education, metrics, or personal details.

Evaluate clarity, structure, relevance, evidence, quantified impact, skills,
career progression, consistency, and recruiter readability. The pros must cite
specific evidence from the resume. The cons must identify genuine weaknesses,
missing evidence, ambiguity, or presentation problems. Do not criticize a
candidate for protected characteristics or infer them. A resume score measures
document quality only and is not a hiring recommendation.

Write concise, useful feedback. Return at least three pros, three cons, and
three prioritized improvements.""",
        ),
        ("human", "Analyze this resume:\n\n{resume_text}"),
    ]
)


def _analyze_node(state: ResumeState) -> ResumeState:
    """Send the resume to Groq and request a structured response."""
    llm = ChatGroq(model=MODEL_NAME, temperature=0)
    structured_llm = llm.with_structured_output(
        ResumeAnalysis,
        method="json_schema",
    )
    analysis = (ANALYSIS_PROMPT | structured_llm).invoke(
        {"resume_text": state["resume_text"]}
    )
    return {"analysis": analysis}


def _validate_node(state: ResumeState) -> ResumeState:
    """Check that the main feedback sections were produced."""
    analysis = state["analysis"]
    if not analysis.pros or not analysis.cons:
        raise ValueError("The model returned an incomplete resume analysis.")
    return state


def build_resume_graph():
    """Compile the two-stage resume-analysis workflow."""
    graph = StateGraph(ResumeState)
    # Flow: START -> analyze_resume -> validate_analysis -> END.
    graph.add_node("analyze_resume", _analyze_node)
    graph.add_node("validate_analysis", _validate_node)
    graph.add_edge(START, "analyze_resume")
    graph.add_edge("analyze_resume", "validate_analysis")
    graph.add_edge("validate_analysis", END)
    return graph.compile()


resume_graph = build_resume_graph()


def analyze_resume(resume_text: str) -> ResumeAnalysis:
    """Run one resume through the compiled LangGraph workflow."""
    result = resume_graph.invoke({"resume_text": resume_text})
    return result["analysis"]
