# Agentic RAG System Guide

## Overview

The system has been upgraded from a **Simple RAG** to an **Agentic RAG** architecture, providing intelligent reasoning and tool selection capabilities.

## What is Agentic RAG?

Agentic RAG is an advanced RAG system where an AI agent can:
- **Reason** about the best approach to answer a question
- **Select appropriate tools** based on the query type
- **Take multiple steps** to gather information
- **Synthesize** information from multiple sources

### Simple RAG vs Agentic RAG

| Feature | Simple RAG | Agentic RAG |
|---------|------------|-------------|
| **Query Processing** | Direct retrieval → LLM | Agent reasoning → Tool selection → LLM |
| **Tool Selection** | Fixed pipeline | Dynamic tool choice |
| **Multi-step Reasoning** | ❌ No | ✅ Yes |
| **Numerical Queries** | Limited | ✅ Excel with TableQuery tool |
| **Complex Questions** | May fail | ✅ Breaks down into steps |
| **Transparency** | Limited | ✅ Shows reasoning steps |

## Architecture

```
User Query
    ↓
Agentic RAG System
    ↓
ReAct Agent (Reasoning + Acting)
    ↓
Tool Selection:
    • VectorSearch          - Semantic similarity search
    • DocumentDetails       - Detailed content retrieval
    • TableQuery           - CSV/numerical queries
    • ListDocuments        - Show available documents
    • SynthesizeMultipleDocs - Multi-doc analysis
    ↓
Observation & Reasoning
    ↓
Final Answer
```

## Available Tools

### 1. VectorSearch
**Purpose**: Search for relevant information using semantic similarity

**Best For**:
- General questions
- Finding relevant passages
- Concept-based queries

**Example**:
```
Q: "What is meal planning?"
Tool: VectorSearch
```

### 2. DocumentDetails
**Purpose**: Get detailed, complete content from documents

**Best For**:
- In-depth information needs
- Following up on initial searches
- Comprehensive answers

**Example**:
```
Q: "Give me detailed information about the internship project"
Tool: DocumentDetails
```

### 3. TableQuery
**Purpose**: Query numerical/structured data from CSV files

**Best For**:
- Statistical questions
- Calculations
- Data analysis queries
- "How many", "What's the average", "Show me data" questions

**Example**:
```
Q: "What is the average GPU benchmark score?"
Tool: TableQuery
```

### 4. ListDocuments
**Purpose**: Show all available documents in the knowledge base

**Best For**:
- "What documents do you have?"
- Document discovery
- Knowledge base overview

**Example**:
```
Q: "What files are available?"
Tool: ListDocuments
```

### 5. SynthesizeMultipleDocs
**Purpose**: Gather and synthesize information from multiple documents

**Best For**:
- Complex questions needing multiple sources
- Cross-referencing information
- Comprehensive research queries

**Example**:
```
Q: "Compare the approaches in different project reports"
Tool: SynthesizeMultipleDocs
```

## ReAct Pattern

The system uses the **ReAct (Reasoning + Acting)** pattern:

1. **Thought**: Agent thinks about the question and plans
2. **Action**: Selects and uses an appropriate tool
3. **Observation**: Observes the tool's result
4. **Thought**: Reasons about the observation
5. **Action**: May use another tool if needed
6. **Final Answer**: Synthesizes all information into an answer

### Example Reasoning Chain:

```
Question: "What's the average score in GPU benchmarks?"

Thought: This is a numerical question about CSV data
Action: TableQuery
Action Input: "average score in GPU benchmarks"
Observation: [CSV data results]

Thought: I now have the data, let me formulate the answer
Final Answer: "The average GPU benchmark score is 85.4..."
```

## API Usage

### Endpoint: `/api/ask`

**Request Body**:
```json
{
  "question": "Your question here",
  "profile_id": "user123",
  "chat_id": "chat456",
  "use_agentic_rag": true  // true for agentic, false for simple RAG
}
```

**Response**:
```json
{
  "answer": "The answer to your question...",
  "sources": ["document1.pdf", "data.csv"],
  "reasoning_steps": 3,
  "rag_type": "agentic"
}
```

### Switching Between RAG Modes

**Agentic RAG** (default):
```python
request = {
    "question": "What is meal planning?",
    "profile_id": "user123",
    "use_agentic_rag": True  # or omit (defaults to True)
}
```

**Simple RAG**:
```python
request = {
    "question": "What is meal planning?",
    "profile_id": "user123",
    "use_agentic_rag": False
}
```

## Testing

### Automated Tests
```bash
python test_agentic_rag.py
```

### Interactive Mode
```bash
python test_agentic_rag.py --interactive
```

## Integration with Existing Features

### Access Control
Agentic RAG respects the hierarchical access control:
- Filters documents based on user access level
- Only retrieves accessible documents
- Maintains security in multi-document synthesis

### Chat History
- All agentic RAG responses are saved to chat history
- Reasoning steps are tracked
- Sources are properly attributed

## Performance Considerations

### When to Use Agentic RAG
✅ **Use Agentic RAG for**:
- Complex questions
- Numerical/statistical queries
- Multi-document analysis
- When reasoning transparency is needed

### When to Use Simple RAG
✅ **Use Simple RAG for**:
- Very simple factual questions
- When speed is critical
- When token usage needs to be minimized

## Configuration

### Model Configuration
The agentic RAG uses the same model configuration as the rest of the system:

```python
# In app.py or model_config.json
{
  "llm_model": "phi3:latest",
  "embedding_model": "bge-m3:latest"
}
```

### Updating the Model
When you change the LLM model through the admin panel, the agentic RAG system automatically uses the new model.

## Advantages

1. **Intelligence**: Agent reasons about the best approach
2. **Flexibility**: Can handle diverse query types
3. **Accuracy**: Better at numerical and complex queries
4. **Transparency**: Shows reasoning process
5. **Robustness**: Can recover from initial failures
6. **Extensibility**: Easy to add new tools

## Limitations

1. **Speed**: Slightly slower than simple RAG (due to reasoning)
2. **Token Usage**: Uses more tokens for reasoning steps
3. **Complexity**: More moving parts = more potential points of failure
4. **Model Dependency**: Requires capable LLM for good reasoning

## Best Practices

1. **For Users**:
   - Be specific in questions
   - Ask follow-up questions if needed
   - Check reasoning steps for transparency

2. **For Developers**:
   - Add new tools as needed
   - Monitor reasoning quality
   - Tune max_iterations based on query complexity
   - Log tool usage for insights

## Troubleshooting

### Agent Not Using Right Tool
**Problem**: Agent selects wrong tool for query

**Solution**:
- Improve tool descriptions
- Make query more specific
- Check tool availability

### Slow Response Times
**Problem**: Queries taking too long

**Solution**:
- Reduce max_iterations (default: 5)
- Use simple RAG for simple queries
- Optimize tool implementations

### Parsing Errors
**Problem**: Agent output parsing fails

**Solution**:
- System handles parsing errors gracefully
- Check LLM model capability
- Review agent prompts

## Future Enhancements

Potential improvements:
- [ ] Memory/conversation context
- [ ] Web search tool integration
- [ ] Image/multimodal document handling
- [ ] Custom tool creation via UI
- [ ] Query intent classification
- [ ] Performance optimization
- [ ] Caching frequent queries

---

## Quick Start Example

```python
from agentic_rag import get_agentic_rag

# Initialize agent
agent = get_agentic_rag(model_name="phi3:latest")

# Ask a question
result = agent.query("What's the average in the GPU benchmarks?")

# Print results
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")
print(f"Reasoning Steps: {result['reasoning_steps']}")
```

---

**System Version**: Agentic RAG v1.0
**Last Updated**: 2025
