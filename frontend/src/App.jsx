import { useState, useEffect, useRef } from 'react'
import { Send, FileText, Database, Settings, Loader2, Globe, File, FileSpreadsheet } from 'lucide-react'
import axios from 'axios'
import clsx from 'clsx'
import FilePreview from './FilePreview'
import ReactMarkdown from 'react-markdown'
import SettingsModal from './SettingsModal'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am docBrain. How can I help you today?' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [documents, setDocuments] = useState([])
  const [docsLoading, setDocsLoading] = useState(true)
  const [previewFile, setPreviewFile] = useState(null)
  const [showSettings, setShowSettings] = useState(false)

  // Startup Check State
  const [isBackendReady, setIsBackendReady] = useState(false)
  const [connectionRetries, setConnectionRetries] = useState(0)

  const messagesEndRef = useRef(null)

  // Configuration - In a real app this should be in .env
  const API_URL = 'http://localhost:8000'
  const API_KEY = 'docbrain_default_key' // Default setup

  // 1. Poll for Backend Health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await axios.get(`${API_URL}/health`)
        setIsBackendReady(true)
      } catch (err) {
        console.log("Backend not ready, retrying...", err)
        setConnectionRetries(prev => prev + 1)
        setTimeout(checkHealth, 1000)
      }
    }
    checkHealth()
  }, [])

  // 2. Fetch Data (Only after backend is ready)
  useEffect(() => {
    if (!isBackendReady) return

    fetchDocuments()

    // Setup interval to refresh status
    const interval = setInterval(fetchDocuments, 30000)
    return () => clearInterval(interval)
  }, [isBackendReady])

  const fetchDocuments = async () => {
    try {
      setDocsLoading(true)
      const response = await axios.get(`${API_URL}/documents`, {
        headers: { 'Authorization': `Bearer ${API_KEY}` }
      })
      if (response.data && response.data.status === 'success') {
        setDocuments(response.data.documents)
      }
    } catch (error) {
      console.error("Failed to fetch documents:", error)
    } finally {
      setDocsLoading(false)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setInput('')
    setIsLoading(true)

    try {
      const response = await axios.post(`${API_URL}/query`, {
        query: userMessage,
        quality_mode: false,
        force_crew: false
      }, {
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.data && response.data.status === 'success') {
        setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }])
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Received unexpected response from server.' }])
      }

    } catch (error) {
      console.error("API Error:", error)
      let errorMsg = "Sorry, I couldn't connect to the server. Please check if the backend is running."
      if (error.response) {
        errorMsg = `Server Error: ${error.response.data.detail || error.response.statusText}`
      }
      setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }])
    } finally {
      setIsLoading(false)
    }
  }

  const getIconForType = (type, path) => {
    if (type === 'webpage') return <Globe size={16} className="text-gray-500 group-hover:text-blue-400 transition-colors" />
    if (path.endsWith('.pdf')) return <FileText size={16} className="text-gray-500 group-hover:text-red-400 transition-colors" />
    if (path.endsWith('.xlsx') || path.endsWith('.xls')) return <FileSpreadsheet size={16} className="text-gray-500 group-hover:text-green-400 transition-colors" />
    return <File size={16} className="text-gray-500 group-hover:text-gray-300 transition-colors" />
  }

  // Loading Screen (Splash)
  if (!isBackendReady) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-neutral-950 text-white gap-4">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-red-900/30 border-t-red-500 rounded-full animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl">🧠</span>
          </div>
        </div>
        <h1 className="text-2xl font-bold tracking-tight">docBrain</h1>
        <div className="text-neutral-500 text-sm animate-pulse flex flex-col items-center gap-1">
          <span>Establishing Neural Link...</span>
          <span className="text-xs text-neutral-600">Attempt {connectionRetries + 1}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full bg-neutral-950 text-gray-100 font-sans overflow-hidden selection:bg-red-500/30">

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal
          onClose={() => setShowSettings(false)}
          apiUrl={API_URL}
          apiKey={API_KEY}
          onConfigUpdate={() => {
            fetchDocuments() // Refresh documents if paths changed
            setShowSettings(false)
          }}
        />
      )}

      {/* File Preview Modal */}
      {previewFile && (
        <FilePreview
          file={previewFile}
          onClose={() => setPreviewFile(null)}
          apiUrl={API_URL}
          apiKey={API_KEY}
        />
      )}

      {/* Sidebar */}
      <div className="w-64 bg-black/50 border-r border-red-900/20 flex flex-col shrink-0 backdrop-blur-xl">
        <div className="p-4 border-b border-red-900/20 flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-red-600 to-rose-600 rounded-lg flex items-center justify-center font-bold text-white shadow-lg shadow-red-900/20">dB</div>
          <span className="font-semibold text-lg tracking-tight bg-gradient-to-r from-gray-100 to-gray-400 bg-clip-text text-transparent">docBrain</span>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <div>
            <div className="text-xs font-semibold text-red-500/80 uppercase mb-3 px-2 tracking-wider flex justify-between items-center">
              <span>Knowledge Base</span>
              <span className="text-[10px] bg-red-900/30 text-red-400 px-1.5 py-0.5 rounded border border-red-500/10">{documents.length}</span>
            </div>
            <div className="space-y-1">
              {docsLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="animate-spin text-red-500/50" size={20} />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-xs text-center text-gray-600 py-4 italic">
                  No documents found.<br />Add files to ./data
                </div>
              ) : (
                documents.map((doc, idx) => (
                  <div
                    key={idx}
                    onClick={() => setPreviewFile(doc)}
                    className="group flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 cursor-pointer text-gray-400 hover:text-white transition border border-transparent hover:border-red-500/10"
                    title={doc.source}
                  >
                    {getIconForType(doc.type, doc.source)}
                    <span className="text-sm truncate">{doc.title || doc.source.split(/[\\/]/).pop()}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-red-900/20">
          <button className="flex items-center gap-2 text-gray-400 hover:text-white transition w-full px-3 py-2 rounded-lg hover:bg-white/5" onClick={() => setShowSettings(true)}>
            <Settings size={16} />
            <span className="text-sm">Settings</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-gradient-to-b from-neutral-950 to-neutral-900">
        {/* Header */}
        <div className="h-16 border-b border-red-900/20 flex items-center px-6 justify-between bg-black/20 backdrop-blur-md z-10 sticky top-0">
          <div className="flex flex-col">
            <span className="font-medium text-gray-200">New Session</span>
            <span className="text-xs text-red-400/80">Standard RAG Mode</span>
          </div>
          <div className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded border border-red-500/20 flex items-center gap-1 shadow-[0_0_10px_rgba(239,68,68,0.1)]">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
            System Ready
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-lg ${msg.role === 'user'
                ? 'bg-gradient-to-br from-red-600 to-rose-700 text-white rounded-br-none border border-red-500/20'
                : 'bg-neutral-800/50 text-gray-200 rounded-bl-none border border-white/5 backdrop-blur-sm'
                }`}>
                <div className="leading-relaxed whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-neutral-800/50 text-gray-200 rounded-2xl rounded-bl-none border border-white/5 px-5 py-3 shadow-sm flex items-center gap-2">
                <Loader2 className="animate-spin text-red-400" size={18} />
                <span className="text-sm text-gray-400">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-red-900/20 bg-neutral-950/80 backdrop-blur-lg">
          <div className="max-w-3xl mx-auto">
            <div className="relative flex items-end group bg-white/5 border border-white/10 rounded-xl shadow-xl transition-all hover:bg-white/10 focus-within:ring-2 focus-within:ring-red-500/30 focus-within:border-red-500/50">
              <textarea
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
                    e.preventDefault();
                    if (!isLoading) handleSend();
                  }
                }}
                placeholder="Ask anything about your documents..."
                disabled={isLoading}
                rows={1}
                className="w-full bg-transparent text-gray-100 py-4 pl-5 pr-12 focus:outline-none placeholder-gray-600 resize-none max-h-[200px] overflow-y-auto"
                style={{ height: 'auto', minHeight: '56px' }}
              />
              <button
                onClick={handleSend}
                className="absolute right-3 bottom-3 p-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 rounded-lg text-white transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-900/30 hover:shadow-red-900/50 transform hover:scale-105 active:scale-95"
                disabled={!input.trim() || isLoading}
              >
                <Send size={18} />
              </button>
            </div>
            <div className="text-center mt-3 flex items-center justify-center gap-4 text-xs text-gray-600">
              <span>Press <b>Enter</b> to send</span>
              <span><b>Shift + Enter</b> for new line</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
