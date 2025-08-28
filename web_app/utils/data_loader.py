import copy
import json
import os
from pathlib import Path
from web_app.config.config_loader import config
from typing import Dict, List, Optional, Any


class DataLoader:

    def __init__(self):
        # --- Initialize Data Loader using Config ---
        self.data_path = Path(config.get('DATA_DIR', 'data')).resolve()
        if not self.data_path.is_dir():
            raise FileNotFoundError(
                f"The specified data directory does not exist: {self.data_path}"
            )

        self.manifest_file = Path(self.data_path).resolve().joinpath(config.get('MANIFEST_FILE', 'technologies.json'))
        if not self.manifest_file.is_file():
            raise FileNotFoundError(
                f"The Manifest file does not exist: {self.manifest_file}"
            )

        # Cache for loaded technologies metadata
        self.loaded_technologies: List[Dict[str, Any]] = self.load_technologies()
        # Cache for loaded exam set data files (to avoid reloading files repeatedly)
        self.loaded_exam_set: Dict[str, Dict[str, Any]] = {}

    def load_json_file(self, file_path: Path) -> Any | None:
        """
        Load a JSON file and return its contents.

        Args:
            file_path (Path): Path to the JSON file.

        Returns:
            dict: Parsed JSON data.
        """
        if not file_path.is_file():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            # Handle the case where the file doesn't exist
            print(f"Error: File not found at {file_path}")
            return None
        except json.JSONDecodeError:
            # Handle the case where the file is not valid JSON
            print(f"Error: Could not decode JSON from {file_path}. Check for syntax errors.")
            return None
        except Exception as e:
            # Catch any other unexpected errors during file processing
            print(f"An unexpected error occurred while loading {file_path}: {e}")
            return None

    def load_technologies(self) -> List[Dict[str, Any]]:
        """
        Load and return all technologies from 'technologies.json'.

        Returns:
            list: List of technology dictionaries.
        """
        # technologies_file = self.data_path / 'technologies.json'
        data = self.load_json_file(self.manifest_file)
        return data.get('technologies', [])

    def get_technologies(self) -> List[Dict[str, Any]]:
        """
        Get the preloaded list of technologies.

        Returns:
            list: List of technology dictionaries.
        """
        return self.loaded_technologies

    def load_exam_set_data(self, datafile_name: str) -> Dict[str, Any]:
        """
        Load and cache exam set data for a given datafile.

        Args:
            datafile_name (str): Name of the datafile (e.g., 'java.json').

        Returns:
            dict: Parsed exam set data.
        """
        # Check if already loaded to avoid re-reading the file
        if datafile_name in self.loaded_exam_set:
            return self.loaded_exam_set[datafile_name]

        datafile_path = self.data_path / datafile_name
        data = self.load_json_file(datafile_path)

        # Cache it
        self.loaded_exam_set[datafile_name] = data
        return data

    def get_exam_catalog_by_technology_id(self, tech_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all exam sets for a given technology ID.

        Args:
            tech_id (str): Technology ID to search.

        Returns:
            list or None: List of exam sets or None if technology not found.
        """
        # Find the technology by ID
        tech = next((t for t in self.loaded_technologies if t['id'] == tech_id), None)
        if not tech:
            return None  # Technology not found

        # Load and return exam sets from its datafile
        tech_data = self.load_exam_set_data(tech['datafile'])
        data = {
            'name':tech_data.get('name', []),
            'description':tech_data.get('description', []),
            'icon':tech_data.get('icon','fas fa-microchip'),
            'exam_sets':tech_data.get('exam_sets', [])
        }

        return data

    def get_exam_set_by_id(
            self, tech_id: str, set_id: str, include_questions: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific exam set by Technology ID and Set ID.

        Args:
            tech_id (str): Technology ID.
            set_id (str): Exam Set ID.
            include_questions (bool): Whether to include questions in response.

        Returns:
            dict or None: Exam set data or None if not found.
        """
        # Fetch all exam sets for the given technology
        exam_catalog = self.get_exam_catalog_by_technology_id(tech_id)
        if not exam_catalog:
            return None

        exam_sets = exam_catalog.get('exam_sets')
        if not exam_sets:
            return None

        # Find the specific exam set by its ID
        exam_set = next((es for es in exam_sets if es['id'] == set_id), None)
        if not exam_set:
            return None

        # If questions should be excluded, return a copy without 'questions' key
        if not include_questions:
            exam_set = copy.deepcopy(exam_set)
            exam_set.pop('questions', None)

        return exam_set





    # def load_data(self, filename: str) -> dict | list | None:
    #     # Construct the full path to the target file
    #     file_path = self.data_path / filename
    #
    #     try:
    #         # Use a 'with' statement for safe file handling (ensures file is closed)
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             # Parse the JSON content and return it
    #             data = json.load(f)
    #             return data
    #     except FileNotFoundError:
    #         # Handle the case where the file doesn't exist
    #         print(f"Error: File not found at {file_path}")
    #         return None
    #     except json.JSONDecodeError:
    #         # Handle the case where the file is not valid JSON
    #         print(f"Error: Could not decode JSON from {file_path}. Check for syntax errors.")
    #         return None
    #     except Exception as e:
    #         # Catch any other unexpected errors during file processing
    #         print(f"An unexpected error occurred while loading {file_path}: {e}")
    #         return None
    #
    # def load_configured_technologies(self):
    #     return self.load_data("technologies.json")

    # def get_configured_technologies(self):
    #     return self.loaded_technologies.get('technologies', [])
    #
    # def load_exam_data(self, file_name: str, sanitize: bool = False):
    #     data = copy.deepcopy(self.load_data(file_name))
    #     if sanitize:
    #         exam_sets = data.get('exam_sets', {})
    #         if isinstance(exam_sets, dict):
    #             for exam_set_key, exam_set_value in exam_sets.items():
    #                 if isinstance(exam_set_value, dict) and 'questions' in exam_set_value:
    #                     exam_set_value.pop('questions', None)
    #         elif isinstance(exam_sets, list):
    #             for exam_set in exam_sets:
    #                 if isinstance(exam_set, dict) and 'questions' in exam_set:
    #                     exam_set.pop('questions', None)
    #     return data
    #
    # def get_exam_sets_by_id(self, id):
    #     try:
    #         exam_set_file = self._find_exam_set_file_by_id(id)
    #         if not exam_set_file:
    #             print(f"No exam set file found for ID: {id}")
    #             return None
    #
    #         exam_data = self.load_exam_data(exam_set_file, sanitize=True)
    #         return exam_data.get('exam_sets', []) if isinstance(exam_data, dict) else []
    #     except Exception as e:
    #         print(f"[ERROR] get_exam_sets_by_id failed: {e}")
    #         return None
    #
    # def get_tech_name_by_id(self, tech_id):
    #     # Implement logic to get technology name by ID
    #     # Example:
    #     tech_data = self.load_configured_technologies()  # Implement this method
    #     return tech_data.get(tech_id, {}).get('name', 'Unknown Technology')
    #
    # def get_question_by_topic(self, topic_id, question_num):
    #     # Implement logic to get specific question
    #     return {
    #         'text': "Which of the following best describes REST API principles?",
    #         'options': [
    #             "To manage frontend routing and navigation.",
    #             "To enable stateless client-server communication.",
    #             "To handle user authentication workflows.",
    #             "To implement real-time socket communication."
    #         ]
    #     }
    #
    # def _find_exam_set_file_by_id(self, tech_id):
    #     """Helper to get the exam set file name for a given technology ID."""
    #     configured_technologies = self.get_configured_technologies()
    #     # configured_technologies = self.loaded_technologies
    #
    #     for tech in configured_technologies:
    #         if str(tech.get("id")) == str(tech_id):
    #             exam_file = tech.get("datafile", "")
    #             print(f"[INFO] Found exam set file: {exam_file}")
    #             return exam_file
    #     return None
    #
    def get_java_exam_sets(self):
        """
        Fetches and processes Java exam sets from a JSON file.

        Args:
            filepath (str): The path to the JSON data file.

        Returns:
            list: A list of dictionary objects, where each dictionary represents a
                  processed Java exam set. Returns an empty list if the file is not
                  found, the data is invalid, or no Java sets are present.
        """
        filepath = self.data_path / "java.json"
        try:
            # 'with open(...)' ensures the file is automatically closed even if errors occur.
            with open(filepath, 'r', encoding='utf-8') as f:
                # json.load() parses the JSON file content into a Python dictionary.
                data = json.load(f)

            # Safely access the Java-specific data using .get() to avoid errors if the key doesn't exist.
            exam_sets = data.get('exam_sets', {})
            return exam_sets

        except FileNotFoundError:
            # Handle the case where the JSON file does not exist.
            print(f"Error: The file at {filepath} was not found.")
            return []
        except json.JSONDecodeError:
            # Handle the case where the file is not valid JSON.
            print(f"Error: Could not decode JSON from the file at {filepath}.")
            return []

    def get_exam_set_by_id_and_name(self, set_id, set_name):
        """
        Retrieves a specific exam set by its ID and name.

        Args:
            set_id (str|int): The unique identifier of the exam set.
            set_name (str): The name of the exam set.

        Returns:
            dict | None: The exam set dictionary if found, otherwise None.
        """
        java_exam_sets = copy.deepcopy(self.get_java_exam_sets())
        if isinstance(java_exam_sets, dict):
            for exam_set_key, exam_set_value in java_exam_sets.items():
                if isinstance(exam_set_value, dict) and 'questions' in exam_set_value:
                    exam_set_value.pop('questions', None)
        elif isinstance(java_exam_sets, list):
            for exam_set in java_exam_sets:
                if isinstance(exam_set, dict) and 'questions' in exam_set:
                    exam_set.pop('questions', None)

        for data in java_exam_sets:
            if str(data.get("id")) == str(set_id) and data.get("name") == set_name:
                return data
        return None
    #
    # # create function to load technologies from a file
    # def load_technologies_from_file(self, file_name):
    #     """
    #     Loads technologies from a specified JSON file.
    #
    #     Args:
    #         file_name (str): The name of the file containing technology data.
    #
    #     Returns:
    #         dict: A dictionary containing the loaded technologies.
    #     """
    #     return self.load_data(file_name) if file_name else {}
    #
    # # create function to load exam sets from a file by technology ID
    # def load_exam_sets_from_file(self, tech_id):
    #     """
    #     Loads exam sets from a file based on the technology ID.
    #
    #     Args:
    #         tech_id (str): The ID of the technology for which to load exam sets.
    #
    #     Returns:
    #         dict: A dictionary containing the loaded exam sets.
    #     """
    #     exam_set_file = self._find_exam_set_file_by_id(tech_id)
    #     return self.load_exam_data(exam_set_file) if exam_set_file else {}
    #
    # # create function to load exam set by tech_id , set_id , set_name
    # def load_exam_set_by_tech_id(self, tech_id, set_id, set_name):
    #     """
    #     Loads a specific exam set by technology ID, set ID, and set name.
    #
    #     Args:
    #         tech_id (str): The ID of the technology.
    #         set_id (str): The ID of the exam set.
    #         set_name (str): The name of the exam set.
    #
    #     Returns:
    #         dict: The loaded exam set if found, otherwise None.
    #     """
    #     exam_sets = self.load_exam_sets_from_file(tech_id)
    #     for exam_set in exam_sets.get('exam_sets', []):
    #         if str(exam_set.get("id")) == str(set_id) and exam_set.get("name") == set_name:
    #             return exam_set
    #     return None

# -------------------- Example Usage --------------------
if __name__ == '__main__':
    # Initialize DataLoader (config will provide DATA_DIR)
    data_loader = DataLoader()

    # 1. Get All Technologies
    print("\n=== All Technologies ===")
    print(json.dumps(data_loader.get_technologies(), indent=2))

    # 2. Get Exam Sets for a Technology ID
    tech_id = 'tech-java'
    print(f"\n=== Exam Sets for Technology ID '{tech_id}' ===")
    exam_sets = data_loader.get_exam_catalog_by_technology_id(tech_id)
    print(json.dumps(exam_sets, indent=2))

    # 3. Get Specific Exam Set (With Questions)
    set_id = 'tech-java-set1'
    print(f"\n=== Exam Set '{set_id}' with Questions ===")
    exam_set_with_questions = data_loader.get_exam_set_by_id(tech_id, set_id, include_questions=True)
    print(json.dumps(exam_set_with_questions, indent=2))

    # 4. Get Specific Exam Set (Without Questions)
    print(f"\n=== Exam Set '{set_id}' without Questions ===")
    exam_set_without_questions = data_loader.get_exam_set_by_id(tech_id, set_id, include_questions=False)
    print(json.dumps(exam_set_without_questions, indent=2))
