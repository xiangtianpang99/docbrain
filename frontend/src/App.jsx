import { useState, useEffect, useRef } from 'react'
import { Send, FileText, Database, Settings, Loader2, Globe, File, FileSpreadsheet, RotateCw, Search, ChevronDown, ChevronRight, Folder, FileCode, FileImage, Presentation, FileQuestion } from 'lucide-react'
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
  const [searchQuery, setSearchQuery] = useState('') // New search state

  // Startup Check State
  const [isBackendReady, setIsBackendReady] = useState(false)
  const [connectionRetries, setConnectionRetries] = useState(0)
  const [config, setConfig] = useState(null) // Store full config
  const [expandedGroups, setExpandedGroups] = useState({}) // Track folder expansion
  const [isRefreshing, setIsRefreshing] = useState(false) // For refresh animation
  const [wasIndexing, setWasIndexing] = useState(false) // Track previous indexing state for trigger
  const [lastFetchTime, setLastFetchTime] = useState(0) // Timestamp of last successful fetch

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

  // 2. Initial Fetch
  useEffect(() => {
    if (isBackendReady) {
      fetchDocuments()
    }
  }, [isBackendReady])

  // 2. Smart Polling (Timestamp Based)
  // 通过比较服务器的最后更新时间与本地的最后获取时间，来决定是否刷新。
  // 这完美解决了“瞬时任务”在两次轮询间隙完成导致状态捕捉不到的问题。
  useEffect(() => {
    if (!isBackendReady) return

    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_URL}/system/status`, {
          headers: { 'Authorization': `Bearer ${API_KEY}` }
        })

        const { is_indexing, last_update } = res.data

        // 1. 更新UI加载状态
        if (is_indexing) {
          setIsRefreshing(true)
        } else {
          setIsRefreshing(false)
        }

        // 2. 核心同步逻辑: 时间戳比对
        // 如果服务器有了更新 (last_update > lastFetchTime)，且当前空闲，则拉取新数据
        // 注意：加一个由 isRefreshing 导致的缓冲，避免在变为 idle 的瞬间重复触发
        if (!is_indexing && last_update > lastFetchTime) {
          console.log(`New data detected! Server: ${last_update} > Local: ${lastFetchTime}`)
          fetchDocuments()
        }

      } catch (e) {
        // Silent fail
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [isBackendReady, lastFetchTime])


  const fetchDocuments = async () => {
    try {
      if (documents.length === 0) setDocsLoading(true)
      setIsRefreshing(true)

      // 3. Fetch Data
      const docsPromise = axios.get(`${API_URL}/documents`, {
        headers: { 'Authorization': `Bearer ${API_KEY}` }
      })

      const configPromise = axios.get(`${API_URL}/config`, {
        headers: { 'Authorization': `Bearer ${API_KEY}` }
      })

      const [docsRes, configRes] = await Promise.all([docsPromise, configPromise])

      if (docsRes.data && docsRes.data.status === 'success') {
        setDocuments(docsRes.data.documents)
        // Update local fetch timestamp
        setLastFetchTime(Date.now() / 1000)
      }
      if (configRes.data) {
        setConfig(configRes.data)
        // Default to collapsed for a cleaner look
        // logic removed
      }
    } catch (error) {
      console.error("Failed to fetch data:", error)
    } finally {
      setDocsLoading(false)
      setIsRefreshing(false)
    }
  }

  // Helper for File Icons
  const getFileIcon = (filename, source) => {
    const ext = filename.split('.').pop().toLowerCase()

    // Icon mapping
    const iconMap = {
      'pdf': { icon: FileText, color: 'text-red-400' },
      'doc': { icon: FileText, color: 'text-blue-400' },
      'docx': { icon: FileText, color: 'text-blue-400' },
      'xls': { icon: FileSpreadsheet, color: 'text-green-400' },
      'xlsx': { icon: FileSpreadsheet, color: 'text-green-400' },
      'ppt': { icon: Presentation, color: 'text-orange-400' },
      'pptx': { icon: Presentation, color: 'text-orange-400' },
      'md': { icon: FileCode, color: 'text-purple-400' },
      'txt': { icon: FileText, color: 'text-gray-400' },
      'json': { icon: FileCode, color: 'text-yellow-400' },
      'js': { icon: FileCode, color: 'text-yellow-400' },
      'py': { icon: FileCode, color: 'text-blue-300' },
      'html': { icon: Globe, color: 'text-cyan-400' },
      'jpg': { icon: FileImage, color: 'text-pink-400' },
      'png': { icon: FileImage, color: 'text-pink-400' },
      'jpeg': { icon: FileImage, color: 'text-pink-400' }
    }

    // Check for webpage type logic from backend
    if (source && (source.startsWith('http') || source.startsWith('https'))) {
      return <Globe size={16} className="text-cyan-400 group-hover:brightness-125 transition-all" />
    }

    const conf = iconMap[ext] || { icon: FileQuestion, color: 'text-gray-500' }
    const IconComp = conf.icon

    return <IconComp size={16} className={`${conf.color} group-hover:brightness-125 transition-all`} />
  }

  // Helper to group documents by Watch Path
  const getGroupedDocuments = () => {
    if (!config || !documents) return {}

    const groups = {}
    const watchPaths = config.watch_paths || []

    // Initialize groups
    watchPaths.forEach(path => {
      groups[path] = []
    })
    groups['Others'] = [] // For files not in any watch path (e.g. webpage) or legacy

    // Sort documents into groups
    documents.forEach(doc => {
      // Filter by search query first
      const fname = doc.title || doc.source.split(/[\\/]/).pop()
      if (searchQuery && !fname.toLowerCase().includes(searchQuery.toLowerCase())) {
        return
      }

      let matched = false
      // Try to match source to a watch path
      // We look for the longest matching prefix effectively
      // But simple iteration is usually fine for few paths
      for (const wp of watchPaths) {
        // Simple string check, ideally should use proper path logic but this works for simple cases
        // Check if doc source starts with the watch path (normalized slashes a bit)
        const normalizedSource = doc.source.replace(/\\/g, '/')
        const normalizedWP = wp.replace(/\\/g, '/')

        if (normalizedSource.startsWith(normalizedWP) || normalizedSource.includes(normalizedWP)) {
          groups[wp].push(doc)
          matched = true
          break
        }
      }

      if (!matched) {
        groups['Others'].push(doc)
      }
    })

    return groups
  }

  const toggleGroup = (groupName) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupName]: !prev[groupName]
    }))
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

  // No changes here
  const getIconForType = (type, path) => {
    // Legacy wrapper if needed, or replace usages
    const filename = path.split(/[\\/]/).pop()
    return getFileIcon(filename, path)
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
              <div className="flex items-center gap-2">
                <span>Knowledge Base</span>
                <span className="text-[10px] bg-red-900/30 text-red-400 px-1.5 py-0.5 rounded border border-red-500/10">{documents.length}</span>
              </div>
              <button
                onClick={fetchDocuments}
                className="text-gray-500 hover:text-white transition p-1 hover:bg-white/10 rounded"
                title="Refresh File List"
                disabled={isRefreshing}
              >
                <RotateCw size={14} className={clsx(isRefreshing && "animate-spin")} />
              </button>
            </div>

            {/* Search Input */}
            <div className="px-2 mb-3">
              <div className="relative group">
                <Search size={14} className="absolute left-2.5 top-2.5 text-gray-500 group-focus-within:text-red-400 transition-colors" />
                <input
                  type="text"
                  placeholder="Search files..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-black/20 border border-white/5 rounded-lg pl-8 pr-3 py-2 text-xs text-gray-300 focus:outline-none focus:border-red-500/30 transition-all placeholder:text-gray-600"
                />
              </div>
            </div>

            <div className={clsx("space-y-4 transition-opacity duration-500", isRefreshing ? "opacity-60 pointer-events-none" : "opacity-100")}>
              {docsLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="animate-spin text-red-500/50" size={20} />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-xs text-center text-gray-600 py-4 italic">
                  No documents found.<br />Add files to watched folders.
                </div>
              ) : (
                /* Grouped View */
                Object.entries(getGroupedDocuments()).map(([groupName, groupDocs]) => {
                  if (groupDocs.length === 0) return null
                  // Extract folder name for display
                  const displayName = groupName === 'Others' ? 'Uncategorized' : groupName.split(/[\\/]/).filter(Boolean).pop() || groupName

                  return (
                    <div key={groupName} className="space-y-1">
                      {/* Group Header */}
                      <div
                        onClick={() => toggleGroup(groupName)}
                        className="flex items-center gap-2 px-2 py-1 text-xs font-medium text-gray-500 hover:text-gray-300 cursor-pointer select-none transition-colors"
                      >
                        <div className={clsx("transition-transform duration-200", expandedGroups[groupName] ? "rotate-90" : "")}>
                          <ChevronRight size={12} />
                        </div>
                        <Folder size={12} className="text-red-500/60" />
                        <span className="truncate" title={groupName}>{displayName}</span>
                        <span className="ml-auto text-[10px] bg-white/5 px-1 rounded">{groupDocs.length}</span>
                      </div>

                      {/* Group Items - Animated Expansion */}
                      <div className={clsx("overflow-hidden transition-all duration-300 ease-in-out", expandedGroups[groupName] ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0")}>
                        <div className="pl-3 space-y-0.5 border-l border-white/5 ml-2.5 py-1">
                          {groupDocs.map((doc, idx) => (
                            <div
                              key={`${groupName}-${idx}`}
                              onClick={() => setPreviewFile(doc)}
                              className="group flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer text-gray-400 hover:text-white transition"
                              title={doc.source}
                            >
                              <div className="shrink-0 scale-75 opacity-70 group-hover:opacity-100 transition">
                                {getIconForType(doc.type, doc.source)}
                              </div>
                              <span className="text-sm truncate opacity-80 group-hover:opacity-100">{doc.title || doc.source.split(/[\\/]/).pop()}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )
                })
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
