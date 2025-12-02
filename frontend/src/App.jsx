import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim(), top_k: 5 }),
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Failed to get response')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🔍 Web RAG</h1>
        <p>Ask questions based on scraped web content</p>
      </header>

      <div className="search-container">
        <form className="search-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="search-input"
            placeholder="Ask a question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="search-button" disabled={loading || !query.trim()}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Searching and generating answer...</p>
        </div>
      )}

      {result && !loading && (
        <div className="result-container">
          <div className="result-header">
            <span>💡</span>
            <h2>Answer</h2>
          </div>
          
          <div className="answer">{result.answer}</div>

          {result.sources && result.sources.length > 0 && (
            <div className="sources-section">
              <div className="sources-header">📚 Sources</div>
              <div className="sources-list">
                {result.sources.map((source, index) => (
                  <div key={index} className="source-item">
                    <div className="source-icon">{index + 1}</div>
                    <div className="source-content">
                      <div className="source-title">{source.title || 'Untitled'}</div>
                      <a 
                        href={source.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="source-url"
                      >
                        {source.url}
                      </a>
                    </div>
                    <div className="source-similarity">
                      {(source.similarity * 100).toFixed(1)}% match
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!result && !loading && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">🌐</div>
          <h3>Ready to answer your questions</h3>
          <p>Enter a question above to search through scraped web content</p>
        </div>
      )}
    </div>
  )
}

export default App
