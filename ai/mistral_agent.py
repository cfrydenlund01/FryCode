from __future__ import annotations
from ai.prompts import get_analysis_prompt
from utils.logging import get_logger
from ai.loader import load_model
import torch  # type: ignore
from typing import Any, Dict

logger = get_logger(__name__)


class MistralAgent:
    """
    Manages the locally embedded Mistral 7B Instruct AI model.
    Handles model loading, prompt engineering, and generating investment recommendations.
    """

    def __init__(self):
        """
        Initializes the Mistral 7B model and tokenizer.
        Attempts to load the model from HuggingFace Transformers.
        """
        self.model_info = None

    def _ensure_model(self) -> bool:
        """Lazy-load model using :func:`ai.loader.load_model`.

        Returns True if model is available.
        """
        if self.model_info:
            return True
        try:
            self.model_info = load_model()
            return True
        except Exception as exc:
            logger.error(f"Failed to load model: {exc}")
            self.model_info = None
            return False

    def generate_recommendation(self, analysis_input: dict) -> dict:
        """
        Generates an investment recommendation using the Mistral 7B model
        based on the provided market data and user risk profile.

        Args:
            analysis_input (dict): A dictionary containing:
                - 'ticker' (str): The stock ticker symbol.
                - 'real_time_quote' (dict): Latest market data.
                - 'historical_data' (list): List of historical data points.
                - 'sentiment_data' (dict): News and market sentiment data.
                - 'user_risk_profile' (str): 'Low', 'Medium', or 'High'.

        Returns:
            dict: A structured dictionary containing the recommendation.
                  Returns an empty dictionary or a dictionary with an error message
                  if the model is not loaded or generation fails.
            Example:
            {
                'Ticker': 'AAPL',
                'Confidence': 85,
                'Risk Level': 'Medium',
                'Suggested Action': 'BUY',
                'Expected Time Horizon': 'Swing (weeks)',
                'Reasoning Summary': 'Strong upward momentum, recent breakout above resistance, positive earnings sentiment.'
            }
        """
        if not self._ensure_model():
            return {"Error": "AI model not available."}

        model = self.model_info["model"]
        tokenizer = self.model_info["tokenizer"]

        prompt = get_analysis_prompt(analysis_input)
        logger.debug(f"Prompt fed to Mistral: \n{prompt}")

        try:
            input_ids = tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                return_tensors="pt",
                add_generation_prompt=True,
            )
            if torch.cuda.is_available():
                input_ids = input_ids.to(model.device)

            with torch.no_grad():
                outputs = model.generate(
                    input_ids,
                    max_new_tokens=500,
                    do_sample=True,
                    temperature=0.7,
                    top_k=50,
                    top_p=0.95,
                    eos_token_id=tokenizer.eos_token_id,
                )

            generated_text = tokenizer.decode(
                outputs[0][input_ids.shape[1] :], skip_special_tokens=True
            ).strip()
            logger.debug(f"Raw Mistral output: \n{generated_text}")

            # Parse the structured output from Mistral
            parsed_recommendation = self._parse_mistral_output(generated_text)
            return parsed_recommendation

        except Exception as e:
            logger.error(f"Error during Mistral recommendation generation: {e}")
            return {"Error": f"AI generation failed: {e}"}

    def _parse_mistral_output(self, raw_output: str) -> dict:
        """
        Parses the raw text output from Mistral into a structured dictionary.
        This function is critical and must match the expected output format
        defined in ai/prompts.py.
        """
        recommendation: Dict[str, Any] = {}
        lines = raw_output.split("\n")
        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                key = (
                    key.strip().replace("-", " ").replace(" ", "").title()
                )  # Normalize key names
                key = key.replace("Summary", "Summary")  # Keep "Summary" as-is
                if key == "Confidence":
                    try:
                        recommendation[key] = int(value.strip("% "))
                    except ValueError:
                        recommendation[key] = "N/A"
                else:
                    recommendation[key] = value.strip()

        # Ensure all required keys are present, even if empty, for consistent table display
        required_keys = [
            "Ticker",
            "Confidence",
            "Risk Level",
            "Suggested Action",
            "Expected Time Horizon",
            "Reasoning Summary",
        ]
        for key in required_keys:
            if key not in recommendation:
                recommendation[key] = "N/A"

        return recommendation
