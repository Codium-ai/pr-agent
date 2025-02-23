<div class="search-section">
    <h1>AI Docs Search</h1>
    <p class="search-description">
        Search through our documentation using AI-powered natural language queries.
    </p>
    <div class="search-container">
        <input 
            type="text" 
            id="searchInput" 
            class="search-input" 
            placeholder="Enter your search term..."
        >
        <button id="searchButton" class="search-button">Search</button>
    </div>
    <div id="spinner" class="spinner-container" style="display: none;">
        <div class="spinner"></div>
    </div>
    <div id="results" class="results-container"></div>
</div>

<style>
Untitled
.search-section {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 1rem 2rem;
}

h1 {
    color: #666;
    font-size: 2.125rem;
    font-weight: normal;
    margin-bottom: 1rem;
}

.search-description {
    color: #666;
    font-size: 1rem;
    line-height: 1.5;
    margin-bottom: 2rem;
    max-width: 800px;
}

.search-container {
    display: flex;
    gap: 1rem;
    max-width: 800px;
    margin: 0;  /* Changed from auto to 0 to align left */
}

.search-input {
    flex: 1;
    padding: 0 0.875rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.9375rem;
    outline: none;
    height: 40px;  /* Explicit height */
}

.search-input:focus {
    border-color: #6c63ff;
}

.search-button {
    padding: 0 1.25rem;
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: background-color 0.2s;
    height: 40px;  /* Match the height of search input */
    display: flex;
    align-items: center;
    justify-content: center;
}

.search-button:hover {
    background-color: #1976D2;
}

.spinner-container {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #2196F3;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.results-container {
    margin-top: 2rem;
    max-width: 800px;
}

.result-item {
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 1rem;
}

.result-title {
    font-size: 1.2rem;
    color: #2196F3;
    margin-bottom: 0.5rem;
}

.result-description {
    color: #666;
}

.error-message {
    color: #dc3545;
    padding: 1rem;
    border: 1px solid #dc3545;
    border-radius: 4px;
    margin-top: 1rem;
}

.markdown-content {
    line-height: 1.6;
    color: var(--md-typeset-color);
    background: var(--md-default-bg-color);
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    position: relative;
    margin-top: 2rem;
}

.markdown-content::before {
    content: '';
    position: absolute;
    top: -8px;
    left: 24px;
    width: 16px;
    height: 16px;
    background: var(--md-default-bg-color);
    border-left: 1px solid var(--md-default-fg-color--lightest);
    border-top: 1px solid var(--md-default-fg-color--lightest);
    transform: rotate(45deg);
}

.markdown-content > *:first-child {
    margin-top: 0;
    padding-top: 0;
}

.markdown-content p {
    margin-bottom: 1rem;
}

.markdown-content p:last-child {
    margin-bottom: 0;
}

.markdown-content code {
    background: var(--md-code-bg-color);
    color: var(--md-code-fg-color);
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 0.9em;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
}

.markdown-content pre {
    background: var(--md-code-bg-color);
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    margin: 1rem 0;
}

.markdown-content pre code {
    background: none;
    padding: 0;
    font-size: 0.9em;
}

[data-md-color-scheme="slate"] .markdown-content {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

</style>

<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>

<script>
window.addEventListener('load', function() {
    function displayResults(responseText) {
        const resultsContainer = document.getElementById('results');
        const spinner = document.getElementById('spinner');
        const searchContainer = document.querySelector('.search-container');
        
        // Hide spinner
        spinner.style.display = 'none';
        
        // Scroll to search bar
        searchContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        try {
            const results = JSON.parse(responseText);

            marked.setOptions({
                breaks: true,
                gfm: true,
                headerIds: false,
                sanitize: false
            });

            const htmlContent = marked.parse(results.message);
            
            resultsContainer.className = 'markdown-content';
            resultsContainer.innerHTML = htmlContent;

            // Scroll after content is rendered
            setTimeout(() => {
                const searchContainer = document.querySelector('.search-container');
                const offset = 55; // Offset from top in pixels
                const elementPosition = searchContainer.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - offset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }, 100);
        } catch (error) {
            console.error('Error parsing results:', error);
            resultsContainer.innerHTML = '<div class="error-message">Error processing results</div>';
        }
    }

    async function performSearch() {
        const searchInput = document.getElementById('searchInput');
        const resultsContainer = document.getElementById('results');
        const spinner = document.getElementById('spinner');
        const searchTerm = searchInput.value.trim();

        if (!searchTerm) {
            resultsContainer.innerHTML = '<div class="error-message">Please enter a search term</div>';
            return;
        }

        // Show spinner, clear results
        spinner.style.display = 'flex';
        resultsContainer.innerHTML = '';

        try { 
            const data = {
                "query": searchTerm
            };

            const options = {
                method: 'POST',
                headers: {
                    'accept': 'text/plain',
                    'content-type': 'application/json',
                },
                body: JSON.stringify(data)
            };

            // const API_ENDPOINT = 'http://0.0.0.0:3000/api/v1/docs_help';
            const API_ENDPOINT = 'https://help.merge.qodo.ai/api/v1/docs_help';

            const response = await fetch(API_ENDPOINT, options);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const responseText = await response.text();
            displayResults(responseText);
        } catch (error) {
            spinner.style.display = 'none';
            resultsContainer.innerHTML = `
                <div class="error-message">
                    An error occurred while searching. Please try again later.
                </div>
            `;
        }
    }

    // Add event listeners
    const searchButton = document.getElementById('searchButton');
    const searchInput = document.getElementById('searchInput');
    
    if (searchButton) {
        searchButton.addEventListener('click', performSearch);
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
});
</script>