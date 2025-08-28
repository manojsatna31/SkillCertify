from web_app.logging_config.logger import logger, inject_logger, get_context_logger  # Import logging utilities
import uuid  # Used to generate unique session IDs for each exam attempt
import copy  # Used to deep copy question data to avoid mutating originals
import re
import math
from typing import Dict, List, Optional, Any  # Type hints for better code clarity and safety
from .data_loader import DataLoader  # Import DataLoader to fetch exam set and question data
import time

CHOICE_PREFIX_RE = re.compile(r"^\s*[A-Za-z]\s*[\)\.\:\-]\s*")  # e.g., 'A)', 'B.', 'C:', 'D - '

class ExamManager:
    def __init__(self,tech_id: str, set_id: str):
        # Store identifiers for the technology and exam set
        self.tech_id = tech_id
        self.set_id = set_id
        self.per_page = 20
        self.last_activity = time.time()  # Track last activity time
        self.finished = False  # Mark if exam is finished

        # Load metadata + questions via DataLoader if available
        if DataLoader:
            self.data_loader = DataLoader() # Initialize DataLoader for accessing exam data
        if self.data_loader:
            raw_set = self.data_loader.get_exam_set_by_id(tech_id, set_id,include_questions=True)
            if not raw_set:
                raise ValueError(f"Exam set not found for tech={tech_id} set={set_id}")
            # Store exam set metadata
            self.set_name: str = raw_set.get("name", "")
            self.difficulty: str = raw_set.get("difficulty", "")
            self.time_limit: int = int(raw_set.get("time_limit", "30"))  # Normalize to int
            self.passing_score: int = int( raw_set.get("passing_score","75"))
            # Build sanitized questions array: only fields allowed during exam run
            self.questions: List[Dict] = []
            for q in raw_set.get("questions", []):
                self.questions.append(
                    {
                        "id": q.get("id"),
                        "question_text": q.get("question_text"),
                        "options": q.get("options", []),
                        # DO NOT load: correct_answer_index, explanation
                    }
                )
        else:
            # If no DataLoader, initialize empty (or allow injection)
            self.set_name = ""
            self.difficulty = ""
            self.time_limit = 30
            self.questions = []
            self.passing_score = 75

            # --- Navigation + state ---

        self.answers: Dict[str, Optional[int]] = {}  # Stores answers: question_id -> selected option index

        self.review_indices: List[int] = []  # Sorted list of global indices marked for review

        self.skipped_indices: List[int] = [] # A sorted list of global indices where the user navigated away without answering.

        self.main_current_index: int = 0  # Main mode navigation index (global index in [0 .. N-1])

        self.review_position: int = 0  # Review mode pointer: index into review_indices

        self.mode: str = "main"  # Current mode: "main" or "review"

        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # Stores active exam sessions: session_id -> session data

        self.focus_indices: List[int] = []
        self.focus_position: int = 0
        self.focus_type: str = ""  # "review" or "unanswered"

    # ----------------------------
    # Helpers (internal)
    # ----------------------------
    def _clamp(self, value: int, lo: int, hi: int) -> int:
        """Clamp integer to [lo, hi]."""
        return max(lo, min(value, hi))

    def _current_global_index(self) -> int:
        """
        Compute the *global* question index that should be displayed RIGHT NOW,
        based on the current mode.

        - In MAIN mode, return main_current_index
        - In REVIEW mode, return review_indices[review_position] if available
        """
        if self.mode == "review":
            if not self.focus_indices:
                # If nothing to review, safely show main index instead
                return self.main_current_index
            # Clamp review_position to valid range
            self.focus_position = self._clamp(self.focus_position , 0, len(self.focus_indices) - 1)
            return self.focus_indices[self.focus_position]
        # Main mode
        return self._clamp(self.main_current_index, 0, len(self.questions) - 1)

    def _mark_skipped(self, idx: int) -> None:
        """Mark a given question index as skipped (if not already)."""
        if idx not in self.skipped_indices:
            self.skipped_indices.append(idx)
            self.skipped_indices = sorted(set(self.skipped_indices))

    def _unmark_skipped(self, idx: int) -> None:
        """Remove a given question index from skipped (if present)."""
        if idx in self.skipped_indices:
            self.skipped_indices.remove(idx)


    # ----------------------------
    # Public API consumed by routes
    # ----------------------------
    def get_current_question(self) -> Dict:
        """
        Return a dictionary suitable for the template with all necessary fields
        for rendering the current question and controls.
        """
        total = len(self.questions)
        if total == 0:
            raise ValueError("No questions loaded for this exam set.")

        # Decide which global index to show based on mode
        global_idx = self._current_global_index()
        q = self.questions[global_idx]

        # Determine first/last flags in the CURRENT MODE
        if self.mode == "main":
            is_first = (self.main_current_index <= 0)
            is_last = (self.main_current_index >= total - 1)
        else:
            # REVIEW mode boundaries depend on review_position range
            if not self.focus_indices:
                # If no review items, treat as disabled both sides
                is_first = True
                is_last = True
            else:
                is_first = (self.focus_position  <= 0)
                is_last = (self.focus_position  >= len(self.focus_indices) - 1)

        # Selected answer for this question (if any)
        selected = self.answers.get(q["id"])

        # 🔑 Compute unanswered count
        unanswered_count = sum(
            1 for question in self.questions if self.answers.get(question["id"]) is None
        )


        # Build the data object for template
        data = {
            # meta
            "tech_id": self.tech_id,
            "set_id": self.set_id,
            "set_name": self.set_name,
            "difficulty": self.difficulty,
            "time_limit": self.time_limit,

            # Navigation + Mode
            "mode": self.mode,
            "total_questions": total,
            "current_index": global_idx,  # 0-based global
            "display_index": global_idx + 1,  # 1-based for UI
            "is_first_question": is_first,  # in current mode
            "is_last_question": is_last,  # in current mode

            # Question content
            "question_id": q["id"],
            "question_text": q["question_text"],
            "options": q["options"],
            "selected_answer": selected if selected is not None else None,

            # Review state
            "review_indices": self.review_indices[:],
            "review_count": len(self.review_indices),
            "is_marked_for_review": (global_idx in self.review_indices),

            # Skipped state
            "skipped_indices": self.skipped_indices[:],
            "skipped_count": len(self.skipped_indices),
            "is_skipped": (global_idx in self.skipped_indices),

            # Unanswered
            "unanswered_count": unanswered_count,
        }
        return data

    def save_answer(self, selected_option: Optional[int]) -> None:
        """
        Save the answer for the CURRENTLY SHOWN question in the current mode.
        """
        # Determine which question is currently visible
        global_idx = self._current_global_index()
        qid = self.questions[global_idx]["id"]

        # Normalize and store (allow None to clear)
        if selected_option is None:
            self.answers[qid] = None
        else:
            self.answers[qid] = int(selected_option)
            # If user answered, ensure it's not marked skipped
            self._unmark_skipped(global_idx)

    def toggle_review(self) -> None:
        """
        Mark/unmark the CURRENTLY SHOWN global index for review.
        Maintains review_indices as a sorted list.
        """
        idx = self._current_global_index()

        if idx in self.review_indices:
            # Remove it
            old_pos = self.review_indices.index(idx)
            self.review_indices.remove(idx)

            # If we were in review mode and removed the current item:
            if self.mode == "review":
                # Adjust review_position to a valid nearby slot
                if old_pos >= len(self.review_indices):
                    self.review_position = max(0, len(self.review_indices) - 1)
                else:
                    self.review_position = old_pos
        else:
            # Insert in sorted order
            self.review_indices.append(idx)
            self.review_indices = sorted(set(self.review_indices))
            if self.mode == "review":
                # If we’re in review mode, align review_position to where this idx sits
                self.review_position = self.review_indices.index(idx)

    def go_next(self) -> None:
        """
        Move forward in the current mode’s sequence.
        Before moving, mark current as skipped if unanswered.
        """

        idx = self._current_global_index()
        qid = self.questions[idx]["id"]

        # If unanswered and not already answered, mark as skipped
        if self.answers.get(qid) is None:
            self._mark_skipped(idx)

        total = len(self.questions)
        if self.mode == "main":
            if self.main_current_index < total - 1:
                self.main_current_index += 1
        else:
            # review mode
            if self.focus_indices  and self.focus_position  < len(self.focus_indices ) - 1:
                    self.focus_position  += 1

    def go_prev(self) -> None:
        """
        Move backward in the current mode’s sequence.
        Before moving, mark current as skipped if unanswered.
        """
        idx = self._current_global_index()
        qid = self.questions[idx]["id"]

        if self.answers.get(qid) is None:
            self._mark_skipped(idx)


        if self.mode == "main":
            if self.main_current_index > 0:
                self.main_current_index -= 1
        else:
            if self.focus_indices  and  self.focus_position  > 0:
                    self.focus_position  -= 1

    def switch_to_main(self) -> None:
        """Return to main navigation mode."""
        self.mode = "main"
        # Sync main index to last seen question
        self.main_current_index = self._current_global_index()

    def switch_mode(self, mode: str) -> None:
        """
        Switch between 'main' and 'review', preserving context for each.
        - If switching to review and there are no review items, remain in main.
        """
        if mode == "review":
            if not self.review_indices:
                # Nothing to review -> stay in main
                self.mode = "main"
                return
            # Clamp position and switch
            self.review_position = self._clamp(self.review_position, 0, len(self.review_indices) - 1)
            self.mode = "review"
        elif mode == "main":
            self.mode = "main"

    def jump_to_focus_index(self, target_global_index: int, focus_type: str) -> None:
        """
        Jump to a SPECIFIC global index inside a focus list.
        Focus list can be:
          - review questions
          - unanswered questions
        Activates focus mode automatically.
        Before jumping, mark current as skipped if unanswered.
        """

        # First, if leaving a question unanswered, mark it skipped
        idx = self._current_global_index()
        qid = self.questions[idx]["id"]
        if self.answers.get(qid) is None:
            self._mark_skipped(idx)

        # Build the focus list based on requested type
        if focus_type == "unanswered":
            focus_indices = [
                i for i, q in enumerate(self.questions)
                if self.answers.get(q["id"]) is None
            ]
        else:  # default to review
            focus_indices = self.review_indices[:]

        if not focus_indices:
            return  # nothing to focus on

        # If target is valid, set position
        if target_global_index in focus_indices:
            self.focus_indices = sorted(focus_indices)
            self.focus_position = self.focus_indices.index(target_global_index)
            self.mode = "review"
            self.focus_type = focus_type

    def jump_to_review_index(self, target_global_index: int) -> None:
        """
        Jump to a SPECIFIC global index that is marked for review.
        - Activates review mode automatically (does not affect main index).
        Before jumping, mark current as skipped if unanswered.
        """

        idx = self._current_global_index()
        qid = self.questions[idx]["id"]
        if self.answers.get(qid) is None:
            self._mark_skipped(idx)

        if target_global_index in self.review_indices:
            # Find its position in the review-sequence
            self.review_position = self.review_indices.index(target_global_index)
            self.mode = "review"
    def generate_report(self, page: int = 1, per_page: int = 0) -> Dict:
        """
        Build a complete exam report including summary stats and per-question details.
        This will be passed into the exam_report.html template.
        """
        # -------------------------
        # 1) per_page fallback & validation
        # -------------------------
        # If caller passed per_page==0, fall back to instance default; if that's absent use 10
        per_page = per_page or getattr(self, "per_page", 10) or 10

        # Basic validation: per_page must be positive integer
        if not isinstance(per_page, int) or per_page <= 0:
            raise ValueError("per_page must be a positive integer")

        # -------------------------
        # 2) get full set & map questions by id
        # -------------------------
        full_set = self.data_loader.get_exam_set_by_id(self.tech_id, self.set_id, include_questions=True)
        # question_map allows us to look up full question data by question id
        question_map = {q["id"]: q for q in full_set.get("questions", [])}

        # -------------------------
        # 3) initialize counters & outputs
        # -------------------------
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        skipped_count = len(self.skipped_indices)  # keep original value for reporting
        question_reports = []
        question_navigation_index = []

        # Prepare a normalized set for fast skipped lookup.
        # Usersystems sometimes store skipped as: question IDs, 0-based indices, or 1-based numbers.
        # We build a set for each form so our "is_skipped" check is flexible.
        skipped_raw = getattr(self, "skipped_indices", [])
        skipped_set_ids = set()  # items that are question IDs (if any)
        skipped_set_zero = set()  # 0-based indices
        skipped_set_one = set()  # 1-based indices

        for s in skipped_raw:
            try:
                # If s matches a known question id in the full set map, treat as id
                if s in question_map:
                    skipped_set_ids.add(s)
                else:
                    # try numeric conversions: treat as int index (0- or 1-based)
                    si = int(s)
                    skipped_set_zero.add(si)  # treat as 0-based
                    skipped_set_one.add(si)  # also include in 1-based set (we'll handle below)
                    # also add 1-based equivalent (si+1) to one-set if si looks like 0-based
                    skipped_set_one.add(si + 1)
            except Exception:
                # If conversion fails, ignore — it's not a numeric index nor a question id
                continue

            # -------------------------
            # 4) Build question_reports and navigation entries
            # Use a question-index variable that cannot be shadowed by option loops
            # -------------------------
        for q_idx, q in enumerate(self.questions):  # q_idx is 0-based index in self.questions
            qid = q["id"]
            # Get the full question from the full set map (safeguarded)
            full_q = question_map.get(qid, {})

            correct_answer = full_q.get("correct_answer_index")
            user_answer = self.answers.get(qid)

            # Determine correctness
            is_correct = (user_answer == correct_answer) if user_answer is not None else False
            if is_correct:
                correct_count += 1
            elif user_answer is not None:
                incorrect_count += 1
            if user_answer is None:
                unanswered_count += 1

            # Clean and label options; use a different loop variable name to avoid shadowing
            full_options_raw = full_q.get("options", [])
            full_options = [self._clean_option_text(o) for o in full_options_raw]
            options_with_labels = []
            for opt_idx, opt_text in enumerate(full_options):
                label = chr(65 + opt_idx)  # 'A', 'B', 'C', ...
                options_with_labels.append({
                    "label": label,
                    "text": opt_text,
                    "value": opt_idx
                })

            # Robust 'is_skipped' detection:
            # consider three possibilities:
            #  - skipped list contains question IDs
            #  - skipped list contains 0-based indices
            #  - skipped list contains 1-based indices
            is_skipped = False
            if qid in skipped_set_ids:
                is_skipped = True
            elif q_idx in skipped_set_zero:
                is_skipped = True
            elif (q_idx + 1) in skipped_set_one:
                is_skipped = True

            # Append navigation metadata for this question
            question_navigation_index.append({
                "is_correct": is_correct,
                "is_unanswered": (user_answer is None),
                "is_skipped": is_skipped
            })

            # Build question report entry. Use .get(...) to avoid KeyError if some fields missing.
            question_reports.append({
                "question_text": full_q.get("question_text", ""),
                "options": options_with_labels,
                "user_answer": user_answer,
                "user_answer_label": self._get_label_for_option(full_options, user_answer),
                "correct_answer": correct_answer,
                "correct_answer_label": self._get_label_for_option(full_options, correct_answer),
                "is_correct": is_correct,
                "is_unanswered": (user_answer is None),
                "is_skipped": is_skipped,
                "explanation": full_q.get("explanation")
            })

        # -------------------------
        # 5) Pagination: compute valid page range and slice questions
        # -------------------------
        total_questions = len(question_reports)

        # Quick empty case
        if total_questions == 0:
            return {
                "tech_id": self.tech_id,
                "set_id": self.set_id,
                "set_name": self.set_name,
                "total_questions": 0,
                "passing_score": int(self.passing_score),
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "unanswered_count": unanswered_count,
                "skipped_count": skipped_count,
                "questions": [],
                "question_navigation_index": question_navigation_index,
                "pagination": {
                    "current_page": 1,
                    "per_page": per_page,
                    "total_questions": 0,
                    "total_pages": 0,
                    "start_index": 0,
                    "end_index": 0
                }
            }

        # Correct total_pages calculation (do NOT divide twice)
        # total_pages = math.ceil(total_questions / per_page)
        total_pages = math.ceil(len(question_reports) / per_page)

        # Clamp page to [1, total_pages]
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        # start_idx is 0-based inclusive; end_idx is exclusive for slicing
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_questions)  # exclusive upper bound

        paginated_questions = question_reports[start_idx:end_idx]

        # Add absolute (1-based) index to each paginated question for display purposes
        for i, q in enumerate(paginated_questions):
            q["absolute_index"] = start_idx + i + 1  # 1-based across the entire exam

        logger.info(f"self.skipped_indices={self.skipped_indices}")

        # -------------------------
        # 6) Return full report with clear pagination metadata
        # -------------------------
        return {
            "tech_id": self.tech_id,
            "set_id": self.set_id,
            "set_name": self.set_name,
            "total_questions": total_questions,
            "passing_score": int(self.passing_score),
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "unanswered_count": unanswered_count,
            "skipped_count": skipped_count,
            "questions": paginated_questions,
            "questions_per_page" : int(per_page),
            "question_navigation_index": question_navigation_index,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_questions": total_questions,
                "total_pages": total_pages,
                "start_index": start_idx + 1,  # 1-based absolute index of first item on page
                # "end_index": start_idx + len(paginated_questions)     # inclusive 1-based
                "end_index": min(total_questions, start_idx + len(paginated_questions))  # inclusive 1-based
            }
        }

        # --- helper to normalize option text ------------------------------------

    def _clean_option_text(self, s: str) -> str:
        """
        Remove a leading 'A) ', 'B.', 'C:', 'D -', etc., from an option string,
        so we can safely prepend our own 'A) ' labels without duplication.
        """
        if not isinstance(s, str):
            return s
        # Only strip if it looks like a single-letter multiple-choice prefix
        return CHOICE_PREFIX_RE.sub("", s).strip()

    def _get_label_for_option(self, options: List[str], value: Optional[int]) -> str:
        """
        Map an option index back to 'A) text'. If value is None -> 'Unanswered'.
        Assumes 'options' are already cleaned (no built-in 'A) ' prefixes).
        """
        if value is None:
            return "No answer"
        if not isinstance(value, int) or value < 0 or value >= len(options):
            return "N/A"
        label = chr(65 + value)  # A, B, C, ...
        return f"{label}) {options[value]}"
