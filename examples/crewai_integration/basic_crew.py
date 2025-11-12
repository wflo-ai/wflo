"""
Basic CrewAI example WITHOUT wflo integration.

This shows a content marketing crew with 3 agents:
1. Researcher - Research topics
2. Writer - Write blog posts
3. Editor - Edit and improve content

PROBLEMS with vanilla CrewAI:
- No cost tracking per agent
- No budget limits (one agent could burn entire budget)
- No automatic retries on API failures
- Limited observability of agent interactions
- No rollback if content is bad
- No approval gates before publishing
"""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define agents
researcher = Agent(
    role="Content Researcher",
    goal="Research comprehensive information about given topics",
    backstory="""You are an expert researcher with deep knowledge across
    multiple domains. You excel at finding accurate, relevant information
    and presenting it clearly.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

writer = Agent(
    role="Content Writer",
    goal="Write engaging, well-structured blog posts",
    backstory="""You are a professional content writer with 10+ years
    of experience. You write clear, engaging content that resonates
    with readers.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

editor = Agent(
    role="Content Editor",
    goal="Edit and improve blog posts for quality and readability",
    backstory="""You are a meticulous editor with a keen eye for detail.
    You improve clarity, fix grammar, and ensure content flows well.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Define tasks
def create_content_tasks(topic: str):
    """Create tasks for content creation pipeline."""

    research_task = Task(
        description=f"""Research the topic: {topic}

        Find:
        - Key points and themes
        - Latest trends and developments
        - Interesting statistics or facts
        - Expert opinions

        Provide a comprehensive research summary.""",
        agent=researcher,
        expected_output="Detailed research summary with key points and sources"
    )

    writing_task = Task(
        description=f"""Using the research provided, write a blog post about: {topic}

        The blog post should:
        - Be 800-1000 words
        - Have an engaging introduction
        - Include 3-4 main sections
        - Use clear headings
        - End with a strong conclusion
        - Be written in an engaging, accessible style""",
        agent=writer,
        expected_output="Complete blog post in markdown format",
        context=[research_task]  # Depends on research
    )

    editing_task = Task(
        description="""Edit and improve the blog post.

        Focus on:
        - Grammar and spelling
        - Clarity and flow
        - Sentence structure
        - Overall readability
        - SEO optimization

        Provide the final, polished version.""",
        agent=editor,
        expected_output="Final polished blog post ready for publishing",
        context=[writing_task]  # Depends on writing
    )

    return [research_task, writing_task, editing_task]


# Create crew
def create_content_crew(topic: str):
    """Create content creation crew."""
    tasks = create_content_tasks(topic)

    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=tasks,
        process=Process.sequential,  # Tasks run in order
        verbose=True
    )

    return crew


# Run the crew
def main():
    """Run content creation crew."""

    topic = "The Future of AI Agent Frameworks in 2025"

    print("=" * 60)
    print("RUNNING VANILLA CREWAI (NO WFLO)")
    print("=" * 60)
    print(f"\nTopic: {topic}\n")

    crew = create_content_crew(topic)

    try:
        # Execute crew
        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"\nFinal Blog Post:\n{result[:300]}...")

        # PROBLEMS:
        print("\n" + "=" * 60)
        print("PROBLEMS WITH VANILLA CREWAI")
        print("=" * 60)
        print("⚠️  No cost tracking per agent!")
        print("⚠️  No budget enforcement!")
        print("⚠️  Can't tell which agent used most tokens!")
        print("⚠️  If editor says content is bad, can't rollback!")
        print("⚠️  No approval before 'publishing'!")
        print("⚠️  If API fails, whole crew stops!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("⚠️  No automatic retry!")
        print("⚠️  Lost all work from researcher and writer!")


if __name__ == "__main__":
    main()
