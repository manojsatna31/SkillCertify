<p align="center">
  <img src="https://raw.githubusercontent.com/Manoj-1996-m/SkillCertify/main/q_bank_app/static/icons/svg/logo.svg" alt="SkillCertify Logo" width="140">
</p>

<h3 align="center">Master Your Tech Skills. Ace Your Certifications.</h3>

<p align="center">
  <!-- Badges -->
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python Version"></a>
  <a href="https://jinja.palletsprojects.com/"><img src="https://img.shields.io/badge/built%20with-Jinja2-orange.svg" alt="Built with Jinja2"></a>
  <a href="https://github.com/your-username/certiforge/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/status-active-brightgreen.svg" alt="Status"></a>  
</p>

**SkillCertify** is more than just a quiz platform; it's a comprehensive training ground designed to bridge the gap between theoretical knowledge and certified expertise. Built with a clean, modern, and highly performant tech stack, it provides a seamless and realistic exam simulation environment to help developers and practitioners achieve their career goals.

---

### 🚀 Beyond Certification: Your Interview Prep Powerhouse

Technical interviews aren't just about knowing the answer; they're about demonstrating deep understanding under pressure. SkillCertify is the perfect tool to sharpen your edge.

*   **Solidify Core Concepts:** By tackling a wide range of questions, you reinforce foundational knowledge and uncover areas for improvement.
*   **Practice Under Pressure:** The timed environment simulates the stress of a real interview, training you to think clearly and perform when it counts.
*   **Articulate Complex Topics:** Reviewing detailed explanations helps you master the "why" behind the "what," enabling you to articulate your reasoning with confidence—a key trait that interviewers look for.

---

### 🎥 Live Demo in Action

A quick walkthrough of the user experience, from selecting a topic to reviewing the final report.

<p align="center">
  <img src="https://raw.githubusercontent.com/Manoj-1996-m/SkillCertify/main/demo.gif" alt="SkillCertify Live Demo GIF" width="800">
</p>

---

### ✨ Key Features

*   🎨 **Adaptive Light/Dark Theme:** A beautiful, persistent theme toggle for optimal user comfort, day or night.
*   🗂️ **Effortless Content Management:** The entire platform is driven by a JSON manifest. Add new exam topics, question sets, and icons with **zero code changes**, making the platform incredibly easy to maintain and expand.
*   ⏱️ **Realistic Timed Exams:** A 90-minute countdown timer and progress bar create an authentic, high-stakes practice environment.
*   ⚡ **Blazing-Fast SPA Interface:** The exam interface operates as a Single-Page Application, ensuring a smooth, uninterrupted experience with no page reloads between questions.
*   📊 **Insightful Performance Reports:** After each exam, users receive an instant score, a clear pass/fail status, and a detailed question-by-question report with correct answers and explanations presented in a clean, accessible modal.
*   📱 **Fully Responsive Design:** A flawless and intuitive experience across desktop, tablet, and mobile devices.
*   🧩 **Professional & Scalable Backend:** Built with modern Flask best practices (Blueprints, Application Factory) for a clean, maintainable, and scalable foundation.

---

### 🛠️ Technology Stack

*   **Backend:** 🐍 Python, Flask
*   **Frontend:** 🌐 HTML5, Tailwind CSS, Vanilla JavaScript
*   **Templating:** ✨ Jinja2
*   **Data Format:** 📄 JSON

---

### ⚙️ Local Setup & Installation

Follow these steps to get SkillCertify running on your local machine.

#### 1. Prerequisites

*   Python 3.8+
*   `pip` and `venv` (standard with modern Python installations)

#### 2. Clone the Repository

```bash
git clone https://github.com/your-username/SkillCertify.git
cd SkillCertify
```

#### 3. Set Up the Virtual Environment

Using a virtual environment is crucial for managing project dependencies cleanly.

*   **On macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
*   **On Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

#### 4. Install Dependencies

Install all required Python packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

#### 5. Configure the Environment

Create a `.env` file in the project's root directory. This file stores your application's secret key.

```bash
# For macOS/Linux:
cp .env.example .env

# For Windows:
copy .env.example .env
```
> **Security Note:** The `.env` file contains the `SECRET_KEY`. While a default is provided, you should generate a new, secure key for any production-like environment.

#### 6. Run the Application

Use the Flask Command-Line Interface to run the development server.

```bash
flask run
```

The application will now be running at `http://127.0.0.1:5000`.

---

### 📝 How to Add New Exams

The platform's content is 100% data-driven. Here’s how to add a new exam topic:

**1. Create the Question File:**
*   Add a new `.json` file to the `data/` directory (e.g., `data/python_basics.json`).
*   Structure it with an `"exam_sets"` array, following the format of the existing files.

**2. Add the Topic Icon:**
*   Create or find a suitable `.svg` icon for your new topic.
*   Place it inside the `q_bank_app/static/icons/svg/` directory (e.g., `python.svg`).

**3. Update the Central Manifest:**
*   Open the main manifest file: `data/topics_manifest.json`.
*   Add a new JSON object to the array that describes your new topic.

> **Example: Adding a Python topic to `topics_manifest.json`**
> ```json
> {
>   "topic_id": "python",
>   "filename": "python_basics.json",
>   "title": "Python Basics",
>   "description": "Test your knowledge of Python fundamentals.",
>   "svgfilename": "python.svg"
> }
> ```

**4. Restart the Server:**
*   Restart your Flask server. The new topic will appear on the home page automatically.

---

### 🏗️ Project Architecture

The project follows a standard Flask application structure for scalability and separation of concerns.

```
SkillCertify/
├── data/
│   ├── topics_manifest.json  # <-- Central index of all topics
│   └── ...                   # <-- Question data files
├── q_bank_app/
│   ├── __init__.py           # Application factory (create_app)
│   ├── routes.py             # App routes (Blueprint)
│   ├── static/
│   │   ├── css/main.css      # Custom Tailwind styles
│   │   ├── js/exam.js        # Frontend exam logic
│   │   └── icons/svg/        # SVG icons for topic cards
│   └── templates/
│       ├── base.html         # Master layout template
│       ├── components/       # Reusable template partials
│       └── pages/            # Main page templates
├── .env                      # Local environment variables
├── config.py                 # Configuration loader
├── question_bank.py          # Dynamic data loader
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── README.md                 # This file
```

---

### 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
