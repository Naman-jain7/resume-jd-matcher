document.getElementById('match-form').addEventListener('submit', async function (e) {
    e.preventDefault(); // Prevent page reload

    const btn = document.getElementById('analyze-btn');
    const resultsSection = document.getElementById('results');
    const missingList = document.getElementById('missing-skills-list');
    const suggestionsList = document.getElementById('suggestions-list');
    const scoreValue = document.getElementById('score-value');

    // 1. Loading State
    btn.innerText = "Processing Resume...";
    btn.disabled = true;
    btn.style.opacity = "0.7";
    btn.style.cursor = "not-allowed";

    // 2. Prepare Data
    const formData = new FormData(this);

    try {
        const response = await fetch('/api/match', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Analysis failed");
        }

        const data = await response.json();

        // 3. Update UI with Real Data
        scoreValue.innerText = data.match_score;

        missingList.innerHTML = data.missing_skills.length > 0
            ? data.missing_skills.map(s => `<li>⚠️ ${s}</li>`).join('')
            : "<li>✅ No missing key skills found!</li>";

        // Replace the mapping logic in your fetch().then() block
        suggestionsList.innerHTML = data.rewrite_suggestions.map(s => {
            // If 's' is a string, use it directly. If it's an object, try to find the text property.
            const suggestionText = typeof s === 'string' ? s : (s.text || s.suggestion || JSON.stringify(s));
            return `<li>💡 ${suggestionText}</li>`;
        }).join('');

        // 4. Show Results
        resultsSection.style.display = 'flex';

    } catch (error) {
        console.error("Error:", error);
        alert("Error: " + error.message);
    } finally {
        // 5. Reset Button
        btn.innerText = "Analyze & Match";
        btn.disabled = false;
        btn.style.opacity = "1";
        btn.style.cursor = "pointer";
    }
});

// Filename display listener remains the same
document.getElementById('resume').addEventListener('change', function () {
    const fileName = this.files[0] ? this.files[0].name : "No file chosen";
    document.getElementById('file-name').innerText = fileName;
});