"""
Agentic RAG System with Tool-Based Reasoning
Implements an intelligent agent that can reason about queries and use multiple tools
"""

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any, Optional
import json
import os
import re
from pathlib import Path

# Import existing components
from vector import retriever, get_vector_store
from table_operations import table_ops


class AgenticRAG:
    """Agentic RAG system with multiple tools and reasoning capabilities"""

    def __init__(self, model_name: str = "phi3:latest"):
        self.model = OllamaLLM(model=model_name)
        self.vector_store = get_vector_store()
        self.max_iterations = 5

    def _vector_search(self, query: str, accessible_filenames: Optional[set] = None) -> str:
        """Search through documents using semantic similarity"""
        try:
            docs = retriever.invoke(query)

            # Filter by access control if needed
            if accessible_filenames:
                docs = [
                    doc for doc in docs
                    if hasattr(doc, 'metadata') and
                    'source' in doc.metadata and
                    os.path.basename(doc.metadata['source']) in accessible_filenames
                ]

            if not docs:
                return "No relevant documents found."

            # Format results with metadata
            results = []
            for i, doc in enumerate(docs[:5], 1):
                source = os.path.basename(doc.metadata.get('source', 'Unknown'))
                content = doc.page_content[:400] + "..." if len(doc.page_content) > 400 else doc.page_content
                results.append(f"[Document {i} - {source}]\n{content}")

            return "\n\n".join(results)
        except Exception as e:
            return f"Error during vector search: {str(e)}"

    def _get_document_details(self, query: str, accessible_filenames: Optional[set] = None) -> str:
        """Get detailed information from specific documents"""
        try:
            docs = retriever.invoke(query)

            # Filter by access control if needed
            if accessible_filenames:
                docs = [
                    doc for doc in docs
                    if hasattr(doc, 'metadata') and
                    'source' in doc.metadata and
                    os.path.basename(doc.metadata['source']) in accessible_filenames
                ]

            if not docs:
                return "No documents found for detailed retrieval."

            results = []
            for i, doc in enumerate(docs[:3], 1):
                source = os.path.basename(doc.metadata.get('source', 'Unknown'))
                results.append(f"[Source: {source}]\n{doc.page_content}")

            return "\n\n---\n\n".join(results)
        except Exception as e:
            return f"Error retrieving document details: {str(e)}"

    def _table_query(self, query: str) -> str:
        """Query structured data from CSV tables"""
        try:
            if not table_ops.tables:
                return "No CSV tables available for querying."

            result = table_ops.query_tables(query)
            return result
        except Exception as e:
            return f"Error querying tables: {str(e)}"

    def _list_documents(self, accessible_filenames: Optional[set] = None) -> str:
        """List all available documents"""
        try:
            all_docs = self.vector_store.get()
            if not all_docs or 'metadatas' not in all_docs:
                return "No documents available."

            # Extract unique sources
            sources = set()
            for metadata in all_docs['metadatas']:
                if 'source' in metadata:
                    filename = os.path.basename(metadata['source'])
                    # Filter by access control if needed
                    if accessible_filenames is None or filename in accessible_filenames:
                        sources.add(filename)

            if not sources:
                return "No documents found."

            doc_list = "\n".join([f"- {doc}" for doc in sorted(sources)])
            return f"Available documents:\n{doc_list}"
        except Exception as e:
            return f"Error listing documents: {str(e)}"

    def _synthesize_multiple_docs(self, query: str, accessible_filenames: Optional[set] = None) -> str:
        """Synthesize information from multiple documents"""
        try:
            docs = self.vector_store.similarity_search(query, k=10)

            # Filter by access control if needed
            if accessible_filenames:
                docs = [
                    doc for doc in docs
                    if hasattr(doc, 'metadata') and
                    'source' in doc.metadata and
                    os.path.basename(doc.metadata['source']) in accessible_filenames
                ]

            if not docs:
                return "No documents found for synthesis."

            # Group by source
            doc_groups = {}
            for doc in docs:
                source = os.path.basename(doc.metadata.get('source', 'Unknown'))
                if source not in doc_groups:
                    doc_groups[source] = []
                doc_groups[source].append(doc.page_content)

            # Format grouped information
            results = []
            for source, contents in doc_groups.items():
                combined = " ".join(contents[:3])
                results.append(f"From {source}:\n{combined[:600]}...")

            return "\n\n".join(results)
        except Exception as e:
            return f"Error synthesizing information: {str(e)}"

    def _select_tool_and_execute(self, question: str, accessible_filenames: Optional[set] = None) -> Dict[str, Any]:
        """Determine which tool to use based on the question"""

        question_lower = question.lower()

        # Detect query intent
        # 1. Document listing queries
        if any(phrase in question_lower for phrase in ['what documents', 'what files', 'list documents', 'available documents', 'show documents']):
            tool_name = "ListDocuments"
            result = self._list_documents(accessible_filenames)

        # 2. Numerical/statistical queries for CSV
        elif any(phrase in question_lower for phrase in ['average', 'mean', 'sum', 'total', 'count', 'how many rows', 'statistics', 'calculate', 'number of', 'percentage', 'maximum', 'minimum', 'median']):
            tool_name = "TableQuery"
            result = self._table_query(question)

        # 3. Multi-document synthesis queries
        elif any(phrase in question_lower for phrase in ['compare', 'across documents', 'from multiple', 'different documents', 'synthesize', 'all documents', 'comprehensive', 'overall']):
            tool_name = "SynthesizeMultipleDocs"
            result = self._synthesize_multiple_docs(question, accessible_filenames)

        # 4. Detailed information queries
        elif any(phrase in question_lower for phrase in ['detailed', 'in depth', 'comprehensive', 'explain in detail', 'tell me more', 'full information']):
            tool_name = "DocumentDetails"
            result = self._get_document_details(question, accessible_filenames)

        # 5. Default: Vector search for general queries
        else:
            tool_name = "VectorSearch"
            result = self._vector_search(question, accessible_filenames)

        return {
            "tool": tool_name,
            "result": result
        }

    def query(self, question: str, accessible_filenames: Optional[set] = None) -> Dict[str, Any]:
        """
        Query the agentic RAG system

        Args:
            question: User's question
            accessible_filenames: Set of filenames the user has access to (for access control)

        Returns:
            Dict with 'answer', 'sources', 'reasoning_steps', and 'agent_type' keys
        """
        try:
            # Step 1: Select tool and get information
            tool_execution = self._select_tool_and_execute(question, accessible_filenames)
            tool_used = tool_execution["tool"]
            tool_result = tool_execution["result"]

            # Step 2: Extract sources from the tool result
            sources = []
            source_pattern = r'\[(?:Document \d+ - |Source: )([^\]]+)\]'
            matches = re.findall(source_pattern, tool_result)
            sources = list(dict.fromkeys(matches))  # Remove duplicates

            # Filter sources by access control
            if accessible_filenames and sources:
                sources = [s for s in sources if s in accessible_filenames]

            # Step 3: Generate final answer using LLM
            prompt_template = """You are an intelligent assistant. Based on the following information retrieved from documents, answer the user's question in a clear, concise, and helpful manner.

Retrieved Information:
{context}

User Question: {question}

Instructions:
- Provide a direct, informative answer
- Use the information from the retrieved documents
- If the information is insufficient, acknowledge it
- Be concise but thorough
- Cite sources when relevant

Answer:"""

            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.model

            answer = chain.invoke({
                "context": tool_result,
                "question": question
            })

            return {
                "answer": answer,
                "sources": sources,
                "reasoning_steps": 2,  # Tool selection + LLM generation
                "agent_type": "agentic",
                "tool_used": tool_used
            }

        except Exception as e:
            return {
                "answer": f"Error processing query with agentic RAG: {str(e)}",
                "sources": [],
                "reasoning_steps": 0,
                "agent_type": "agentic",
                "tool_used": "None"
            }

    def update_model(self, model_name: str):
        """Update the LLM model being used"""
        self.model = OllamaLLM(model=model_name)


# Global instance
agentic_rag = None

def get_agentic_rag(model_name: str = "phi3:latest") -> AgenticRAG:
    """Get or create the agentic RAG instance"""
    global agentic_rag
    if agentic_rag is None:
        agentic_rag = AgenticRAG(model_name=model_name)
    return agentic_rag


def reinitialize_agentic_rag(model_name: str):
    """Reinitialize the agentic RAG with a new model"""
    global agentic_rag
    agentic_rag = AgenticRAG(model_name=model_name)
    return agentic_rag
