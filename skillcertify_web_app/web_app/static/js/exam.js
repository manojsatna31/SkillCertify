// This script assumes 'window.EXAM_DATA' and 'window.TOPIC_TITLE' have been defined
// in a <script> tag in the HTML before this file is loaded.

document.addEventListener('DOMContentLoaded', () => {
    // --- DATA INJECTION ---
    const allSetsData = window.EXAM_DATA;
    const topicTitle = window.TOPIC_TITLE;

    // --- GUARD CLAUSE ---
    // If the data isn't present, or if we're not on the exam page, do nothing.
    if (!allSetsData || !document.getElementById('set-selection-screen')) {
        return;
    }

    // --- STATE MANAGEMENT ---
    let selectedSetName = null;
    let selectedQuestions = [];
    let currentQuestionIndex = 0;
    let userAnswers = [];
    let timerInterval;
    let examFinished = false;

    // --- DOM ELEMENTS ---
    const screens = {
        setSelection: document.getElementById('set-selection-screen'),
        examStart: document.getElementById('exam-start-screen'),
        exam: document.getElementById('exam-screen'),
        postExam: document.getElementById('post-exam-screen'),
        report: document.getElementById('report-screen')
    };
    const setSelectionContainer = document.getElementById('set-selection-container');
    const startScreenTitle = document.getElementById('start-screen-title');
    const startScreenDetails = document.getElementById('start-screen-details');
    const startBtn = document.getElementById('start-exam-btn');
    const backToSetsStartBtn = document.getElementById('back-to-sets-start-btn');
    const backToSetsExamBtn = document.getElementById('back-to-sets-exam-btn');
    const headerTitle = document.getElementById('header-title');
    const timerEl = document.getElementById('timer');
    const timerContainer = document.getElementById('timer-container');
    const questionCounterEl = document.getElementById('question-counter');
    const questionTextEl = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const finishExamBtn = document.getElementById('finish-exam-btn');
    const viewSolutionsBtn = document.getElementById('view-solutions-btn');
    const finalMessageEl = document.getElementById('final-message');
    const scoreSummaryEl = document.getElementById('score-summary');
    const reportContainer = document.getElementById('report-container');
    const solutionModal = document.getElementById('solution-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalQuestionTextEl = document.getElementById('modal-question-text');
    const modalOptionsBodyEl = document.getElementById('modal-options-body');
    const modalExplanationEl = document.getElementById('modal-explanation');

    // --- INITIALIZATION ---
    function init() {
        renderSetSelection();
        addEventListeners();
    }

    function addEventListeners() {
        setSelectionContainer.addEventListener('click', handleSetSelection);
        startBtn.addEventListener('click', startExam);
        backToSetsStartBtn.addEventListener('click', goBackToSetSelection);
        backToSetsExamBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to return to the set selection? Your current progress will be lost.')) {
                goBackToSetSelection();
            }
        });
        prevBtn.addEventListener('click', () => navigateQuestion(-1));
        nextBtn.addEventListener('click', () => navigateQuestion(1));
        finishExamBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to finish the exam?')) {
                finishExam();
            }
        });
        optionsContainer.addEventListener('change', handleAnswerSelection);
        viewSolutionsBtn.addEventListener('click', showReport);
        modalCloseBtn.addEventListener('click', closeModal);
        solutionModal.addEventListener('click', (e) => {
            if (e.target === solutionModal) closeModal();
        });
    }

    // --- SCREEN NAVIGATION & STATE RESET ---
    function showScreen(screenName) {
        Object.values(screens).forEach(screen => screen.classList.add('hidden'));
        if (screens[screenName]) {
            screens[screenName].classList.remove('hidden');
        }
    }

    function goBackToSetSelection() {
        resetState();
        showScreen('setSelection');
        headerTitle.textContent = `${topicTitle} Exam`;
        timerContainer.classList.add('invisible');
    }

    function resetState() {
        clearInterval(timerInterval);
        selectedSetName = null;
        selectedQuestions = [];
        currentQuestionIndex = 0;
        userAnswers = [];
        examFinished = false;
        timerEl.textContent = '90:00';
        reportContainer.innerHTML = '';
        scoreSummaryEl.innerHTML = '';
    }

    // --- CORE APP FLOW ---
    function renderSetSelection() {
        setSelectionContainer.innerHTML = '';
        if (Object.keys(allSetsData).length === 0) {
            setSelectionContainer.innerHTML = `<p class="text-center col-span-full text-gray-500">No question sets are available for this topic yet.</p>`;
            return;
        }
        for (const setName in allSetsData) {
            const set = allSetsData[setName];
            const card = document.createElement('button');
            card.className = 'set-choice-btn block w-full text-left p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-xl hover:-translate-y-1 transform transition-all';
            card.dataset.setName = setName;
            card.innerHTML = `
                <h3 class="text-xl font-bold text-blue-600 dark:text-blue-400">${set.title}</h3>
                <p class="mt-2 text-gray-600 dark:text-gray-400">${set.questions.length} questions</p>
            `;
            setSelectionContainer.appendChild(card);
        }
    }

    function handleSetSelection(e) {
        const button = e.target.closest('.set-choice-btn');
        if (!button) return;
        selectedSetName = button.dataset.setName;
        const set = allSetsData[selectedSetName];
        selectedQuestions = set.questions;
        userAnswers = new Array(selectedQuestions.length).fill(null);
        startScreenTitle.textContent = set.title;
        startScreenDetails.textContent = `This set contains ${set.questions.length} questions. You will have 90 minutes to complete it.`;
        headerTitle.textContent = set.title;
        showScreen('examStart');
    }

    function startExam() {
        showScreen('exam');
        timerContainer.classList.remove('invisible');
        finishExamBtn.disabled = false;
        renderQuestion(currentQuestionIndex);
        startTimer(90 * 60);
    }

    function renderQuestion(index) {
        const question = selectedQuestions[index];
        questionCounterEl.textContent = `Question ${index + 1} of ${selectedQuestions.length}`;
        questionTextEl.innerHTML = question.question_text;
        
        optionsContainer.innerHTML = '';
        question.options.forEach((option, i) => {
            const isChecked = userAnswers[index] === i;
            const optionId = `q${index}-option${i}`;
            const optionElement = document.createElement('label');
            optionElement.htmlFor = optionId;
            optionElement.className = `flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all ${isChecked ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30' : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'}`;
            optionElement.innerHTML = `
                <input type="radio" id="${optionId}" name="question-${index}" value="${i}" class="hidden" ${isChecked ? 'checked' : ''}>
                <span class="flex-grow">${option}</span>
                <div class="w-6 h-6 rounded-full border-2 ${isChecked ? 'border-blue-600 bg-blue-600' : 'border-gray-400'} flex items-center justify-center">
                    ${isChecked ? '<svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"></path></svg>' : ''}
                </div>`;
            optionsContainer.appendChild(optionElement);
        });
        updateNavigation();
    }

    function finishExam(isAutoFinish = false) {
        if (examFinished) return;
        examFinished = true;
        clearInterval(timerInterval);
        showScreen('postExam');
        finalMessageEl.textContent = isAutoFinish ? "Time's Up!" : "You have finished the exam!";
    }

    function showReport() {
        showScreen('report');
        let correctCount = 0;
        userAnswers.forEach((answer, index) => {
            if (answer === selectedQuestions[index].correct_answer_index) {
                correctCount++;
            }
        });
        const score = selectedQuestions.length > 0 ? (correctCount / selectedQuestions.length) * 100 : 0;
        const passed = score >= 70;
        scoreSummaryEl.innerHTML = `Your Score: <span class="font-bold ${passed ? 'text-green-500' : 'text-red-500'}">${score.toFixed(1)}%</span> <span class="ml-4 font-bold ${passed ? 'text-green-500' : 'text-red-500'}">(${passed ? 'Pass' : 'Fail'})</span>`;

        reportContainer.innerHTML = '';
        selectedQuestions.forEach((q, i) => {
            const userAnswerIndex = userAnswers[i];
            const isCorrect = userAnswerIndex === q.correct_answer_index;
            const statusText = isCorrect ? 'Correct' : 'Incorrect';
            const statusColor = isCorrect ? 'text-green-500' : 'text-red-500';
            const statusBg = isCorrect ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20';
            const card = document.createElement('div');
            card.className = `p-4 rounded-lg shadow ${statusBg}`;
            card.innerHTML = `
                <div class="flex flex-col md:flex-row md:items-center justify-between">
                    <div class="flex-1 mb-2 md:mb-0">
                        <p class="font-bold text-gray-800 dark:text-gray-200">Q${i + 1}: ${q.question_text.substring(0, 80)}...</p>
                        <p class="text-sm ${statusColor}">Your Answer: <span class="font-semibold">${userAnswerIndex !== null ? q.options[userAnswerIndex] : 'Not Answered'}</span></p>
                    </div>
                    <div class="flex items-center space-x-4">
                        <p class="font-bold text-lg ${statusColor}">${statusText}</p>
                        <button class="btn btn-secondary text-sm !px-3 !py-1" data-question-index="${i}">Explanation</button>
                    </div>
                </div>`;
            reportContainer.appendChild(card);
        });
        reportContainer.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', (e) => showModal(e.currentTarget.dataset.questionIndex));
        });
    }

    // --- HELPER FUNCTIONS ---
    function handleAnswerSelection(e) { if (e.target.type === 'radio') { userAnswers[currentQuestionIndex] = parseInt(e.target.value, 10); renderQuestion(currentQuestionIndex); } }
    function updateNavigation() { prevBtn.disabled = currentQuestionIndex === 0; nextBtn.disabled = currentQuestionIndex === selectedQuestions.length - 1; }
    function navigateQuestion(direction) { const newIndex = currentQuestionIndex + direction; if (newIndex >= 0 && newIndex < selectedQuestions.length) { currentQuestionIndex = newIndex; renderQuestion(currentQuestionIndex); } }
    function startTimer(duration) { let timeLeft = duration; timerInterval = setInterval(() => { timeLeft--; const minutes = Math.floor(timeLeft / 60).toString().padStart(2, '0'); const seconds = (timeLeft % 60).toString().padStart(2, '0'); timerEl.textContent = `${minutes}:${seconds}`; if (timeLeft <= 0) { clearInterval(timerInterval); finishExam(true); } }, 1000); }
    function showModal(index) { const q = selectedQuestions[index]; modalQuestionTextEl.innerHTML = q.question_text; modalExplanationEl.textContent = q.explanation; modalOptionsBodyEl.innerHTML = ''; q.options.forEach((option, i) => { const div = document.createElement('div'); let classes = 'p-3 rounded-md border '; let indicator = ''; if (i === q.correct_answer_index) { classes += 'bg-green-100 dark:bg-green-900/30 border-green-400'; indicator = `<span class="font-bold text-green-600 dark:text-green-400 ml-2">(Correct Answer)</span>`; } else if (i === userAnswers[index]) { classes += 'bg-red-100 dark:bg-red-900/30 border-red-400'; indicator = `<span class="font-bold text-red-600 dark:text-red-400 ml-2">(Your Answer)</span>`; } else { classes += 'border-gray-300 dark:border-gray-600'; } div.className = classes; div.innerHTML = `${option} ${indicator}`; modalOptionsBodyEl.appendChild(div); }); solutionModal.classList.remove('invisible', 'opacity-0'); }
    function closeModal() { solutionModal.classList.add('invisible', 'opacity-0'); }

    // --- START THE APP ---
    init();
});