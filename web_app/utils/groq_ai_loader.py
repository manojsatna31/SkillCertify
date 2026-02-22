import base64, os
from web_app.logging_config.logger import logger, inject_logger, get_context_logger  # Import logging utilities
import json
from groq import Groq

from dotenv import load_dotenv


def load_system_prompt():
    """Load system prompt from file or environment variable"""
    prompt = ""
    if "SYSTEM_PROMPT_FILE" in os.environ:
        try:
            with open(os.environ["SYSTEM_PROMPT_FILE"], "r", encoding="utf-8") as f:
                prompt = f.read()
        except FileNotFoundError:
            print(f"Warning: SYSTEM_PROMPT_FILE '{os.environ['SYSTEM_PROMPT_FILE']}' not found")
    else:
        prompt = os.getenv("SYSTEM_PROMPT", "")

    return prompt


def clean_json_response(response_text):
    """Clean and extract JSON from AI response"""
    response_clean = response_text.strip()

    # Remove potential markdown code block wrappers
    if response_clean.startswith('```json'):
        response_clean = response_clean[7:]
    elif response_clean.startswith('```'):
        response_clean = response_clean[3:]
    if response_clean.endswith('```'):
        response_clean = response_clean[:-3]

    return response_clean.strip()


def generate_questions( user_content,
                            model="deepseek-r1-distill-llama-70b",
                            system_prompt=None,
                            temperature=0.7,
                            max_tokens=4096,
                            response_format="json_object"):
    """
    Generate a response from Groq AI API

    Args:
        user_content (str): The user's input content
        model (str): The model to use (default: deepseek-r1-distill-llama-70b)
        system_prompt (str): Optional custom system prompt (default: loads from env)
        temperature (float): Creativity temperature (0.0 to 1.0)
        max_tokens (int): Maximum completion tokens
        response_format (str): Response format type

    Returns:
        dict: Parsed JSON response from AI
    """

    # Load environment variables
    load_dotenv()

    # Initialize Groq client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is required")

    client = Groq(api_key=api_key)

    # Use provided system prompt or load from environment
    if system_prompt is None:
        system_prompt = load_system_prompt()

    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_content,
        }
    ]

    logger.info(f'user Prompt::{user_content}')

    # Generate completion
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        stream=False,
        response_format={"type": response_format}
    )

    # Extract and clean response
    ai_response = chat_completion.choices[0].message.content
    ai_response_clean = clean_json_response(ai_response)

    # Parse JSON response
    try:
        generated_data = json.loads(ai_response_clean)
        logger.info(f'Response from Groq::{generated_data}')
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {ai_response}")
        raise

    return generated_data

def generate_groq_response( user_content,is_large_request):
    model = "deepseek-r1-distill-llama-70b"  # Can be overridden by user
    # Adjust max_tokens based on request size
    max_tokens = 8192 if is_large_request else 4096
    return generate_questions(
            user_content=user_content,
            model=model,
            temperature=0.7,
            max_tokens=4096
        )
def main():
    """Example usage of the refactored function"""
    # Example parameters
    user_content = "Generate 1 exam sets for Grade 10 Mathematics with 25 questions per set."
    model = "deepseek-r1-distill-llama-70b"  # Can be overridden by user

    try:
        # Generate response
        result = generate_questions(
            user_content=user_content
        )

        print("Successfully generated data:")
        print(json.dumps(result, indent=2))

        # Here you would save to your database
        # save_to_database(result)

    except Exception as e:
        print(f"Error generating response: {e}")


if __name__ == "__main__":
    main()

########### Old Code
# load_dotenv()
#
# prompt = ""
# if "SYSTEM_PROMPT_FILE" in os.environ:
#     with open(os.environ["SYSTEM_PROMPT_FILE"], "r", encoding="utf-8") as f:
#         prompt = f.read()
# else:
#     prompt = os.getenv("SYSTEM_PROMPT", "")
#
# SYSTEM_PROMPT = prompt
#
# client = Groq(
#     api_key=os.getenv("GROQ_API_KEY"),
# )
# # SYSTEM_PROMPT=base64.b64decode(os.getenv("SYSTEM_PROMPT"))
# chat_completion = client.chat.completions.create(
#     messages=[
#         {
#             "role": "system",
#             "content": SYSTEM_PROMPT
#         },
#         {
#             "role": "user",
#             "content": "Generate 1 exam sets for Grade 10 Mathematics with 5 questions per set.",
#         }
#     ],
#     # model="llama-3.3-70b-versatile",
#     model="deepseek-r1-distill-llama-70b",
#     temperature=0.7,
#     max_completion_tokens=4096,
#     stream=False,
#     response_format={"type": "json_object"}
# )
# # 2. Extract the AI's response
# ai_response = chat_completion.choices[0].message.content
# # 3. The response should already be pure JSON due to response_format.
# # But let's clean it just in case any extra text slips through.
# ai_response_clean = ai_response.strip()
# # Remove potential markdown code block wrappers if they exist
# if ai_response_clean.startswith('```json'):
#     ai_response_clean = ai_response_clean[7:]  # Remove '```json'
# elif ai_response_clean.startswith('```'):
#     ai_response_clean = ai_response_clean[3:]  # Remove '```'
# if ai_response_clean.endswith('```'):
#     ai_response_clean = ai_response_clean[:-3]  # Remove '```' at the end
#
# # 4. Parse the JSON string into a Python dictionary
# generated_data = json.loads(ai_response_clean)
#
#
# # 6. HERE IS WHERE YOU SAVE `generated_data` TO YOUR DATABASE
# # ... (Your logic to create Technology, QuestionSets, Questions) ...
# print(f"Generated data for: {generated_data}")
#
# # 7. Return a success message and the generated data
#
#
# print(chat_completion.choices[0].message.content)
