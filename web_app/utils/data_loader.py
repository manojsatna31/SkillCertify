import copy
import json
import logging
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

        # self.manifest_file = Path(self.data_path).resolve().joinpath(config.get('MANIFEST_FILE', 'technologies.json'))
        self.manifest_file = Path(config.get('MANIFEST_FILE', 'technologies.json'))
        if not Path(self.data_path).resolve().joinpath(self.manifest_file).is_file:
            raise FileNotFoundError(
                f"The Manifest file does not exist: {self.manifest_file}"
            )

        # Cache for loaded technologies metadata
        self.loaded_technologies: List[Dict[str, Any]] = (self.load_json(self.manifest_file)).get('technologies', [])
        # Cache for loaded exam set data files (to avoid reloading files repeatedly)
        self.loaded_exam_set: Dict[str, Dict[str, Any]] = {}

# New Methods
    def get_admin_dashboard_data(self):
        technologies = self.get_all_technologies()
        total_techs = len(technologies)
        total_exam_sets = 0
        total_questions = 0
        for tech in technologies:
            datafile_name = tech.get('datafile')
            if not datafile_name:
                continue
            if not Path(self.data_path).resolve().joinpath(datafile_name).is_file:
                logging.info(f"Warning: data file '{datafile_name}' not found. Skipping.")
                continue
            tech_data = self.load_json(datafile_name)
            exam_sets = tech_data.get('exam_sets', [])
            total_exam_sets += len(exam_sets)
            for exam in exam_sets:
                questions = exam.get('questions', [])
                total_questions += len(questions)
        return {
            "technologies":technologies,
            "total_techs": int(total_techs),
            "total_exam_sets": int(total_exam_sets),
            "total_questions": int(total_questions)

        }

    def get_all_technologies(self):
        """Load all technologies from technologies.json"""
        try:
            return (self.load_json(self.manifest_file)).get('technologies', [])
        except FileNotFoundError:
            return []

    def add_technology(self, tech_data):
        """Add a new technology to technologies.json"""
        try:
            data = self.load_json(self.manifest_file)
            # with open('technologies.json', 'r') as f:
            #     data = json.load(f)

            data['technologies'].append(tech_data)

            # Save the changes
            manifest_path = Path(self.data_path).resolve().joinpath(self.manifest_file)

            with open(manifest_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Update cache
            self.loaded_technologies = data.get('technologies', [])

            return True
        except Exception as e:
            print(f"Error adding technology: {e}")
            return False

    def update_technology(self, tech_id, tech_data):
        """Update a technology in technologies.json"""
        try:
            data = self.load_json(self.manifest_file)
            # with open('technologies.json', 'r') as f:
            #     data = json.load(f)
            # Check if technology exists
            tech_exists = False

            for i, tech in enumerate(data['technologies']):
                if tech['id'] == tech_id:
                    data['technologies'][i] = tech_data
                    tech_exists = True
                    break

            # If technology doesn't exist, add it as new
            if not tech_exists:
                data['technologies'].append(tech_data)

            # Save the changes
            manifest_path = Path(self.data_path).resolve().joinpath(self.manifest_file)

            with open(manifest_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Update cache
            self.loaded_technologies = data.get('technologies', [])

            return True
        except Exception as e:
            print(f"Error updating/adding technology: {e}")
            return False

    def delete_technology(self, tech_id):
        """Delete a technology from technologies.json"""
        try:
            data = self.load_json(self.manifest_file)
            # with open('technologies.json', 'r') as f:
            #     data = json.load(f)

            data['technologies'] = [tech for tech in data['technologies'] if tech['id'] != tech_id]

            with open(Path(self.data_path).resolve().joinpath(self.manifest_file), 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error deleting technology: {e}")
            return False

    def get_exam_sets_for_technology(self, tech_id):
        """Get all exam sets for a specific technology"""
        try:
            with open(f'data/{tech_id}.json', 'r') as f:
                tech_data = json.load(f)

            return tech_data.get('exam_sets', [])
        except FileNotFoundError:
            return []

    def add_exam_set(self, tech_id, exam_set_data):
        """Add an exam set to a technology"""
        try:
            with open(f'data/{tech_id}.json', 'r') as f:
                tech_data = json.load(f)

            if 'exam_sets' not in tech_data:
                tech_data['exam_sets'] = []

            tech_data['exam_sets'].append(exam_set_data)

            with open(f'data/{tech_id}.json', 'w') as f:
                json.dump(tech_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error adding exam set: {e}")
            return False

    def update_exam_set(self, tech_id: str, set_id: str, exam_set_data: Dict) -> bool:
        """Update an exam set in a technology"""
        try:
            tech_file = os.path.join(self.data_dir, f"{tech_id}.json")

            # Load existing data
            with open(tech_file, 'r') as f:
                tech_data = json.load(f)

            # Find and update exam set
            for i, exam_set in enumerate(tech_data['exam_sets']):
                if exam_set['id'] == set_id:
                    tech_data['exam_sets'][i] = {**exam_set, **exam_set_data}
                    break

            # Save back to file
            with open(tech_file, 'w') as f:
                json.dump(tech_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error updating exam set: {e}")
            return False

    def delete_exam_set(self, tech_id: str, set_id: str) -> bool:
        """Delete an exam set from a technology"""
        try:
            tech_file = os.path.join(self.data_dir, f"{tech_id}.json")

            # Load existing data
            with open(tech_file, 'r') as f:
                tech_data = json.load(f)

            # Remove exam set
            tech_data['exam_sets'] = [es for es in tech_data['exam_sets'] if es['id'] != set_id]

            # Save back to file
            with open(tech_file, 'w') as f:
                json.dump(tech_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error deleting exam set: {e}")
            return False

    def get_questions_for_exam_set(self, tech_id: str, set_id: str) -> List[Dict]:
        """Get all questions for a specific exam set"""
        try:
            exam_set = self.get_exam_set(tech_id, set_id)
            return exam_set.get('questions', []) if exam_set else []
        except Exception as e:
            print(f"Error getting questions: {e}")
            return []

    def get_question(self, tech_id: str, set_id: str, question_id: str) -> Optional[Dict]:
        """Get a specific question by ID"""
        questions = self.get_questions_for_exam_set(tech_id, set_id)
        for question in questions:
            if question['id'] == question_id:
                return question
        return None

    def add_question(self, tech_id: str, set_id: str, question_data: Dict) -> bool:
        """Add a question to an exam set"""
        try:
            tech_file = os.path.join(self.data_dir, f"{tech_id}.json")

            # Load existing data
            with open(tech_file, 'r') as f:
                tech_data = json.load(f)

            # Find the exam set
            for exam_set in tech_data['exam_sets']:
                if exam_set['id'] == set_id:
                    # Generate ID if not provided
                    if 'id' not in question_data:
                        question_data['id'] = f"{set_id}-q{len(exam_set.get('questions', [])) + 1}"

                    # Initialize questions array if not exists
                    if 'questions' not in exam_set:
                        exam_set['questions'] = []

                    # Add question
                    exam_set['questions'].append(question_data)
                    break

            # Save back to file
            with open(tech_file, 'w') as f:
                json.dump(tech_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error adding question: {e}")
            return False

    def update_question(self, tech_id: str, set_id: str, question_id: str, question_data: Dict) -> bool:
        """Update a question in an exam set"""
        try:
            tech_file = os.path.join(self.data_dir, f"{tech_id}.json")

            # Load existing data
            with open(tech_file, 'r') as f:
                tech_data = json.load(f)

            # Find and update the question
            for exam_set in tech_data['exam_sets']:
                if exam_set['id'] == set_id:
                    for i, question in enumerate(exam_set.get('questions', [])):
                        if question['id'] == question_id:
                            exam_set['questions'][i] = {**question, **question_data}
                            break
                    break

            # Save back to file
            with open(tech_file, 'w') as f:
                json.dump(tech_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error updating question: {e}")
            return False

    def delete_question(self, tech_id: str, set_id: str, question_id: str) -> bool:
        """Delete a question from an exam set"""
        try:
            tech_file = os.path.join(self.data_dir, f"{tech_id}.json")

            # Load existing data
            with open(tech_file, 'r') as f:
                tech_data = json.load(f)

            # Find and remove the question
            for exam_set in tech_data['exam_sets']:
                if exam_set['id'] == set_id:
                    exam_set['questions'] = [q for q in exam_set.get('questions', []) if q['id'] != question_id]
                    break

            # Save back to file
            with open(tech_file, 'w') as f:
                json.dump(tech_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error deleting question: {e}")
            return False

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

    def load_json(self, json_file_name) -> List[Dict[str, Any]]:
        """
        Load and return all technologies from 'technologies.json'.

        Returns:
            list: List of technology dictionaries.
        """
        # technologies_file = self.data_path / 'technologies.json'
        data = self.load_json_file(Path(self.data_path).resolve().joinpath(json_file_name))
        return data

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

    def update_all_technologies(self, technologies_data: List[Dict[str, Any]]) -> bool:
        """
        Save all technologies in one go by updating the manifest file.

        Args:
            technologies_data: Complete list of technology dictionaries to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create the complete structure for the manifest file
            manifest_data = {
                "technologies": technologies_data
            }

            # Build the full path to the manifest file
            manifest_path = Path(self.data_path).resolve().joinpath(self.manifest_file)

            # Ensure the directory exists
            manifest_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the updated data to the manifest file
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)

            # Update the cached technologies
            self.loaded_technologies = technologies_data

            logging.info(f"Successfully updated all technologies in {manifest_path}")
            return True

        except Exception as e:
            logging.error(f"Error updating all technologies: {e}")
            return False

