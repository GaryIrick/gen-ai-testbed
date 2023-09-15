# gen-ai-testbed

This is a quick and dirty set of Streamlit apps to compare/contrast how we do LLM work with
these packages:

- `openai`
- `langchain`
- `semantic-kernel`

Each app knows how to do three things:

- Use the Heroes of the Storm stats API to return heroes win rates.
- Look up hotel information from the sample dataset provided by Microsoft and stored in
  Azure Cognitive Search.
- Answer general knowledge questions if the answer isn't found from the other two.
