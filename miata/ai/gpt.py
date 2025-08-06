import re
import random

from openai import OpenAI


class GptModel:

    CONTEXT = """
        You are assistant that search facts in the internet and provide short generated text (i.e. fact).

        You must not return any additional text or explanations outside of the generated text.
        You must not return any other format than text.
        You must summarize and return no more than 2 sentences of text.
    """

    PROMPT_TEMPLATES = [
        "Search for information about the Mazda MX-5 Miata's engine specifications and provide one technical fact.",
        "Find details about Mazda MX-5 Miata racing history or motorsports achievements and share an interesting fact.",
        "Look up information about Mazda MX-5 Miata's cultural impact or appearances in movies/games and provide a fact.",
        "Search for facts about Mazda MX-5 Miata's different generations (NA, NB, NC, ND) and their unique features.",
        "Find information about Mazda MX-5 Miata's design philosophy, weight distribution, or handling characteristics.",
        "Look up Mazda MX-5 Miata's production numbers, sales records, or market performance in different countries.",
        "Search for facts about Mazda MX-5 Miata's development team, designers, or creation story.",
        "Find information about Mazda MX-5 Miata's special editions, limited models, or unique variants.",
        "Look up facts about Mazda MX-5 Miata's influence on other car manufacturers or the sports car market.",
        "Search for information about Mazda MX-5 Miata's awards, recognition, or automotive industry achievements.",
        "Find facts about the Mazda MX-5 Miata's maintenance costs, reliability, or ownership experience.",
        "Search for information about famous Mazda MX-5 Miata owners, celebrities, or notable drivers.",
        "Look up details about Mazda MX-5 Miata tuning, modifications, or aftermarket support.",
        "Find facts about the Mazda MX-5 Miata's safety features, crash test ratings, or safety innovations.",
        "Search for information about Mazda MX-5 Miata's fuel economy, environmental impact, or efficiency.",
        "Look up facts about Mazda MX-5 Miata's pricing history, market value, or depreciation trends.",
        "Find details about Mazda MX-5 Miata's international variants, regional differences, or global markets.",
        "Search for information about Mazda MX-5 Miata's anniversary models, commemorative editions, or milestones.",
        "Look up facts about the Mazda MX-5 Miata's competitors, rivals, or similar sports cars.",
        "Find information about Mazda MX-5 Miata's technology features, infotainment, or modern innovations.",
        "Search for details about Mazda MX-5 Miata's manufacturing process, factory locations, or production techniques.",
        "Look up facts about the Mazda MX-5 Miata's fanbase, communities, or enthusiast culture.",
        "Find information about Mazda MX-5 Miata's evolution over time, changes between model years, or updates.",
        "Search for facts about the Mazda MX-5 Miata's convertible top mechanism, hardtop variants, or roof options.",
        "Look up details about Mazda MX-5 Miata's interior design, cabin space, or ergonomics.",
    ]

    def __init__(self, model: str = None, temperature: float = 1.5, api_key: str = ""):
        self.model_name = default_gpt_model if model is None else model
        self.temperature = temperature
        self.api_key = api_key
        self.tools = [{"type": "web_search_preview"}]

        if self.api_key is None or len(self.api_key) == 0:
            raise ValueError("OPENAI_API_KEY cannot be empty.")

        self.client = OpenAI(api_key=self.api_key)

    def evaluate(self):
        
        prompt = random.choice(self.PROMPT_TEMPLATES)
        
        response = self.client.responses.create(
            model=self.model_name,
            tools=self.tools,
            instructions=self.CONTEXT.strip(),
            input=prompt
        )

        output = response.output_text.strip()
        return output