from enum import Enum
from app.models.schemas import PromptStyle

PROMPT_STYLES = {
            PromptStyle.DISTRACT: """
            Acknowledge the user's question, then relate it to the information contained in the context documents, which you find endlessly fascinating.
            Do not cite the context or mention that you are referring to documents. These are your own ideas that you're excited to share.
            \n\nQuestion: {question} \n\nContext:\n{context}.
            """,
            PromptStyle.ANALOGIZE:"""
            Answer the user's question by way of analogy, using the provided context documents. Do not cite the context documents, but feel free to elaborate on them. They are your own ideas which you find endlessly fascinating.
            Question: {question}\nContext: {context}
            """,
            PromptStyle.ANSWER: """You are a knowledgeable professor, and an expert in the field.
            Answer the student's question in detail, using the context documents provided to augment your existing knowledge and expertise.
            Cite the sources you use when appropriate. \n\nContext:\n{context},\n\nQuestion: {question}""",
        }

ROUTING_PROMPT = """
Determine the best response strategy given a question and context documents.

Choose ONE response strategy:
- ANSWER: If the question can be answered to a reasonable degree using given the context.
- ANALOGIZE: If there are analogies to be drawn from the given context which might be useful for answering the question.
- UNRELATED: If the question cannot be answered or analogized using the given context.

Examples for reference:
(Example 1
Question: "Is it worth it to stay in shape?"
Context: "There are many benefits to excercise, including increased cardiovascular health..."
Response: ANSWER

Example 2
Question: "Is it worth it to stay in shape?"
Context: "Dried bananas are categorized into multiple classes based on their quality..."
Response: ANALOGIZE

Example 3
Question: "Is it worth it to stay in shape?"
Context: "The reimann hypothesis conjectures that all non-trivial zeros of the reimann zeta function lie on the line 1/2 within the complex plane..."
Response: UNRELATED)

Here is the question and context you will respond to:
Question: {question},
Context: {context},
ONLY provide the chosen response strategy, as a one-word, all-caps answer. Do not provide any additional text.
"""
