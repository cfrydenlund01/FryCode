import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from ai.prompts import get_analysis_prompt
from utils.logging import get_logger

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
        self.model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self):
        """
        Loads the Mistral 7B Instruct model and its tokenizer.
        Prioritizes GPU if available.
        """
        try:
            logger.info(f"Loading Mistral 7B model: {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16, # Use bfloat16 for efficiency if supported
                device_map="auto" # Automatically maps to available devices (GPU/CPU)
            )
            self.model.eval() # Set model to evaluation mode
            logger.info("Mistral 7B model loaded successfully.")
        except ImportError:
            logger.error("PyTorch or Transformers library not installed correctly. Please check requirements.txt.")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load Mistral 7B model: {e}")
            logger.info("Attempting to load with CPU fallback (this might be slow)...")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="cpu" # Force CPU
                )
                self.model.eval()
                logger.info("Mistral 7B model loaded successfully on CPU.")
            except Exception as e_cpu:
                logger.critical(f"Failed to load Mistral 7B model on CPU as well: {e_cpu}")
                self.model = None
                self.tokenizer = None
                logger.error("Mistral 7B model is not available. AI features will be disabled.")


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
        if not self.model or not self.tokenizer:
            logger.error("Mistral model not loaded. Cannot generate recommendations.")
            return {"Error": "AI model not available."}

        prompt = get_analysis_prompt(analysis_input)
        logger.debug(f"Prompt fed to Mistral: \n{prompt}")

        try:
            # Tokenize the prompt
            input_ids = self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}], return_tensors="pt", add_generation_prompt=True)
            if torch.cuda.is_available():
                input_ids = input_ids.to(self.model.device)

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    max_new_tokens=500, # Increased tokens for detailed reasoning
                    do_sample=True,
                    temperature=0.7,
                    top_k=50,
                    top_p=0.95,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # Decode the response, skipping the input prompt part
            generated_text = self.tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True).strip()
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
        recommendation = {}
        lines = raw_output.split('\n')
        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                key = key.strip().replace('-', ' ').replace(' ', '').title() # Normalize key names
                key = key.replace("Summary", "Summary") # Keep "Summary" as-is
                if key == "Confidence":
                    try:
                        recommendation[key] = int(value.strip('% '))
                    except ValueError:
                        recommendation[key] = "N/A"
                else:
                    recommendation[key] = value.strip()
        
        # Ensure all required keys are present, even if empty, for consistent table display
        required_keys = [
            'Ticker', 'Confidence', 'Risk Level', 'Suggested Action',
            'Expected Time Horizon', 'Reasoning Summary'
        ]
        for key in required_keys:
            if key not in recommendation:
                recommendation[key] = "N/A"
        
        return recommendation