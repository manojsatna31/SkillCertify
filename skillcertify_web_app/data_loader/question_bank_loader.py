import json
import logging
import os

from core_config import Config


def _sanitize_name_for_id(name: str) -> str:
    """Converts a user-friendly name like 'Practice Set 1' into a machine-friendly ID like 'practice_set_1'."""
    return name.lower().replace(' ', '_').replace('-', '_')

def load_question_bank() -> dict:
    """
    Reads the central topics_manifest.json, then loads each topic's JSON file
    and transforms the data into the application's expected Q_BANK format.

    Returns:
        A dictionary representing the entire question bank.
    """
    config = Config()

    master_q_bank = {}
    data = os.environ.get('QB_SOURCE_DIR')
    manifest_file=os.environ.get('QB_MANIFEST_FILE_NAME')
    print(f"os.environ.get('QB_SOURCE_DIR')={data}")
    print(f"os.environ.get('QB_MANIFEST_FILE_NAME')={manifest_file}")
    manifest_path = os.path.join(config.QB_SOURCE_DIR, config.QB_MANIFEST_FILE_NAME)

    if not os.path.exists(manifest_path):
        logging.critical(f"FATAL: The topics manifest file was not found at {manifest_path}. The application cannot load any content.")
        return master_q_bank

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            topic_configs = json.load(f)
    except json.JSONDecodeError:
        logging.critical(f"FATAL: Failed to parse {manifest_path}. Please ensure it is valid JSON.")
        return master_q_bank

    for topic_config in topic_configs:
        topic_id = topic_config.get('topic_id')
        filename = topic_config.get('filename')
        title = topic_config.get('title')
        description = topic_config.get('description')

        if not all([topic_id, filename, title, description]):
            logging.warning(f"Skipping invalid topic config item in manifest: {topic_config}")
            continue

        file_path = os.path.join(config.QB_SOURCE_DIR, filename)

        if not os.path.exists(file_path):
            logging.warning(f"JSON file '{filename}' listed in manifest not found for topic '{topic_id}'. Skipping.")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            transformed_sets = {}
            for exam_set in data.get('exam_sets', []):
                set_name = exam_set.get('name')
                questions = exam_set.get('questions')
                
                if not set_name or questions is None:
                    logging.warning(f"Skipping malformed set in {filename}: Missing 'name' or 'questions'.")
                    continue
                
                set_id = _sanitize_name_for_id(set_name)
                
                transformed_sets[set_id] = {
                    'title': set_name,
                    'questions': questions
                }
            
            master_q_bank[topic_id] = {
                'title': title,
                'description': description,
                'sets': transformed_sets
            }
            logging.info(f"Successfully loaded topic '{title}' from {filename}.")

        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON for topic '{topic_id}' from file: {file_path}. Skipping.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing {file_path}: {e}")

    return master_q_bank

# --- This is the main export ---
# Load the question bank into a global variable when the application starts.
Q_BANK = load_question_bank()