document.getElementById('analyze-btn').addEventListener('click', function() {
    // Logic to show loading state
    this.innerText = "Analyzing...";
    
    // Simulate API call delay
    setTimeout(() => {
        document.getElementById('results').style.display = 'block';
        this.innerText = "Analyze & Match";

        // Mock Data - In production, you'd fetch() your FastAPI endpoint
        const mockMissing = ["Kubernetes", "Redis", "System Design"];
        const mockSuggestions = [
            "Quantify your impact in the Python section (e.g., 'reduced latency by 20%').",
            "Add a project related to Vector Databases to match the JD requirements."
        ];

        const missingList = document.getElementById('missing-skills-list');
        const suggestionsList = document.getElementById('suggestions-list');
        
        missingList.innerHTML = mockMissing.map(s => `<li>⚠️ ${s}</li>`).join('');
        suggestionsList.innerHTML = mockSuggestions.map(s => `<li>💡 ${s}</li>`).join('');
        
        document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
    }, 1500);
});

// Update filename display on upload
document.getElementById('resume').addEventListener('change', function() {
    const fileName = this.files[0] ? this.files[0].name : "No file chosen";
    document.getElementById('file-name').innerText = fileName;
});