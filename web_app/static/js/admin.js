document.addEventListener('DOMContentLoaded', function() {
    // Initialize HTMX configuration
    htmx.config.useTemplateFragments = true;

    // Handle HTMX afterSwap event to update active tab
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        // Update active tab based on current URL
        const currentPath = window.location.pathname;
        const navTabs = document.querySelectorAll('.nav-tab');

        navTabs.forEach(tab => {
            tab.classList.remove('active');
            const tabPath = tab.getAttribute('hx-get');
            if (tabPath && currentPath.includes(tabPath.split('/').pop())) {
                tab.classList.add('active');
            }
        });
    });

    // Handle HTMX beforeRequest event to show loading state
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        const target = evt.detail.target;
        if (target.id === 'admin-content') {
            target.innerHTML = `
                <div class="flex justify-center items-center h-64">
                    <div class="text-center">
                        <i class="fas fa-spinner fa-spin text-4xl text-blue-500 mb-4"></i>
                        <p class="text-gray-600">Loading content...</p>
                    </div>
                </div>
            `;
        }
    });
});

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}
/**
 * Opens the edit modal and populates it with technology data
 * @param {string} techId - The ID of the technology to edit
 */
async function openEditModal(techId) {
    try {
        // Fetch technology data from the server
        const response = await fetch(`/admin/api/technologies?id=${techId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        let techData
        try {
            techData = await response.json();
        }catch (error) {
            console.error('Error parsing JSON:', error);
            // Try to read the response as text and log it
            const text = await response.text();
            console.log('Response text:', text);
            throw error;
        }


        // Handle different response formats
        let technology;

        if (Array.isArray(techData)) {
            // Backend returned all technologies, find the one we need
            technology = techData.find(tech => tech.id === techId);
        } else if (techData.error) {
            // Backend returned an error
            throw new Error(techData.error);
        } else {
            // Backend returned a single technology
            technology = techData;
        }

        // Find the specific technology by ID
        // const technology = Array.isArray(techData) ? techData.find(tech => tech.id === techId) : techData;

        if (technology) {
            // Populate the edit form with the technology data
            document.getElementById('edit-tech-id').value = technology.id;
            document.getElementById('edit-tech-name').value = technology.name || '';
            document.getElementById('edit-tech-description').value = technology.description || '';
            document.getElementById('edit-tech-icon').value = technology.icon || '';
            document.getElementById('edit-tech-data-file').value = technology.data_file || '';
            document.getElementById('edit-tech-active').checked = technology.active || false;
            document.getElementById('edit-display-tech-icon').value = technology.icon;

            // Open the modal
            openModal('edit-tech-modal');
        } else {
            showToast('Technology not found', 'error');
        }
    } catch (error) {
        console.error('Error fetching technology data:', error);
        showToast('Error loading technology data', 'error');
    }
}

function showConfirm(action, itemId) {
    const modal = document.getElementById('confirm-modal');
    const message = document.getElementById('confirm-message');
    const confirmBtn = document.getElementById('confirm-action-btn');

    switch(action) {
        case 'delete-tech':
            message.textContent = 'Are you sure you want to delete this technology? This action cannot be undone.';
            confirmBtn.onclick = function() {
                deleteItem('technology', itemId);
                closeModal('confirm-modal');
            };
            break;
        case 'delete-exam-set':
            message.textContent = 'Are you sure you want to delete this exam set? This action cannot be undone.';
            confirmBtn.onclick = function() {
                deleteItem('exam-set', itemId);
                closeModal('confirm-modal');
            };
            break;
        case 'delete-question':
            message.textContent = 'Are you sure you want to delete this question? This action cannot be undone.';
            confirmBtn.onclick = function() {
                deleteItem('question', itemId);
                closeModal('confirm-modal');
            };
            break;
    }

    openModal('confirm-modal');
}

// API functions
async function deleteItem(type, id) {
    try {
        const response = await fetch(`/admin/api/${type}s?id=${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.status === 'success') {
            showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully!`, 'success');
            // Refresh the current view
            htmx.trigger(`#admin-${type}s`, 'refresh');
        } else {
            showToast(`Error deleting ${type}`, 'error');
        }
    } catch (error) {
        console.error(`Error deleting ${type}:`, error);
        showToast(`Error deleting ${type}`, 'error');
    }
}

async function generateQuestions() {
    const technology = document.getElementById('ai-technology').value;
    const examSet = document.getElementById('ai-exam-set').value;
    const prompt = document.getElementById('ai-prompt').value;
    const count = document.getElementById('ai-question-count').value;
    const difficulty = document.getElementById('ai-difficulty').value;

    // Show loading state
    const outputElement = document.getElementById('ai-output');
    outputElement.innerHTML = '<pre>{\n  "status": "processing",\n  "message": "Generating questions..."\n}</pre>';

    try {
        const response = await fetch('/admin/api/generate-questions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                technology,
                exam_set: examSet,
                prompt,
                count,
                difficulty
            })
        });

        const result = await response.json();

        // Format the JSON with syntax highlighting
        const formattedJson = JSON.stringify(result, null, 4);
        const highlightedJson = formattedJson
            .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?)/g, function(match) {
                let cls = 'json-string';
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                } else if (/[0-9]+/.test(match)) {
                    cls = 'json-number';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });

        outputElement.innerHTML = '<pre>' + highlightedJson + '</pre>';

        // Enable buttons
        document.getElementById('copy-json-btn').disabled = false;
        document.getElementById('save-json-btn').disabled = false;

        showToast('Questions generated successfully!', 'success');
    } catch (error) {
        console.error('Error generating questions:', error);
        outputElement.innerHTML = '<pre>{\n  "error": "Failed to generate questions"\n}</pre>';
        showToast('Failed to generate questions', 'error');
    }
}

function copyToClipboard() {
    const outputElement = document.getElementById('ai-output');
    const text = outputElement.textContent;

    navigator.clipboard.writeText(text).then(() => {
        showToast('JSON copied to clipboard!', 'success');
    }).catch(err => {
        showToast('Failed to copy JSON', 'error');
    });
}

async function saveGeneratedQuestions() {
    const outputElement = document.getElementById('ai-output');
    const questions = JSON.parse(outputElement.textContent);

    try {
        const response = await fetch('/admin/api/save-generated-questions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(questions)
        });

        const result = await response.json();

        if (result.status === 'success') {
            showToast('Questions saved to exam set!', 'success');
        } else {
            showToast('Error saving questions', 'error');
        }
    } catch (error) {
        console.error('Error saving questions:', error);
        showToast('Error saving questions', 'error');
    }
}

function showToast(message, type) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}