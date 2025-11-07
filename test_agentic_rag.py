"""
Test script for Agentic RAG system
"""

from agentic_rag import get_agentic_rag
import sys

def test_agentic_rag():
    """Test the agentic RAG system with various question types"""

    print("=" * 70)
    print("Testing Agentic RAG System")
    print("=" * 70)

    try:
        print("\n1. Initializing Agentic RAG...")
        agent = get_agentic_rag(model_name="phi3:latest")
        print("   ✓ Agentic RAG initialized successfully")

        # Test cases with different query types
        test_questions = [
            {
                "question": "What documents do you have?",
                "expected_tool": "ListDocuments",
                "description": "Document listing query"
            },
            {
                "question": "Tell me about meal planning",
                "expected_tool": "VectorSearch",
                "description": "General semantic search query"
            },
            {
                "question": "What is the average value in the GPU benchmarks?",
                "expected_tool": "TableQuery",
                "description": "Numerical/statistical query for CSV data"
            },
            {
                "question": "Summarize the information from multiple documents about projects",
                "expected_tool": "SynthesizeMultipleDocs",
                "description": "Multi-document synthesis query"
            }
        ]

        print("\n2. Running test queries...")
        print("-" * 70)

        for i, test in enumerate(test_questions, 1):
            print(f"\n   Test {i}: {test['description']}")
            print(f"   Question: \"{test['question']}\"")
            print(f"   Expected Tool: {test['expected_tool']}")
            print()

            try:
                result = agent.query(test['question'])

                print(f"   Answer Preview: {result['answer'][:200]}...")
                print(f"   Sources: {result['sources']}")
                print(f"   Reasoning Steps: {result['reasoning_steps']}")
                print(f"   ✓ Query completed successfully")

            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                continue

            print()

        print("-" * 70)
        print("\n" + "=" * 70)
        print("✓ Agentic RAG Testing Complete!")
        print("=" * 70)

        print("\n" + "Key Features of Agentic RAG:")
        print("-" * 70)
        print("1. Multiple Tools:")
        print("   • VectorSearch - Semantic similarity search")
        print("   • DocumentDetails - Detailed content retrieval")
        print("   • TableQuery - CSV/numerical data queries")
        print("   • ListDocuments - Show available documents")
        print("   • SynthesizeMultipleDocs - Multi-document analysis")
        print()
        print("2. ReAct Pattern:")
        print("   • Thinks about which tool to use")
        print("   • Takes actions with appropriate tools")
        print("   • Observes results and reasons about them")
        print("   • Provides final synthesized answer")
        print()
        print("3. Advantages over Simple RAG:")
        print("   • Can handle complex multi-step queries")
        print("   • Chooses appropriate tools for different question types")
        print("   • Better at numerical/statistical queries")
        print("   • Can synthesize information from multiple sources")
        print("   • Provides reasoning transparency")
        print("-" * 70)

    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def interactive_test():
    """Interactive testing mode"""
    print("=" * 70)
    print("Agentic RAG - Interactive Test Mode")
    print("=" * 70)
    print("Type 'quit' or 'exit' to stop")
    print()

    agent = get_agentic_rag(model_name="phi3:latest")

    while True:
        print("-" * 70)
        question = input("\nAsk a question: ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            print("\nExiting interactive mode...")
            break

        if not question:
            continue

        try:
            print("\n🤖 Agent is thinking and working...\n")
            result = agent.query(question)

            print("\n" + "=" * 70)
            print("ANSWER:")
            print("-" * 70)
            print(result['answer'])
            print()
            print(f"Sources: {', '.join(result['sources']) if result['sources'] else 'None'}")
            print(f"Reasoning Steps: {result['reasoning_steps']}")
            print("=" * 70)

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_test()
    else:
        test_agentic_rag()
