import { useState, useRef } from 'react'
import { API_URL, API_KEY } from './config'

// Hooks
import { useSystemStatus } from './hooks/useSystemStatus'
import { useSessions } from './hooks/useSessions'
import { useKnowledgeBase } from './hooks/useKnowledgeBase'
import { useChat } from './hooks/useChat'

// Components
import SplashScreen from './components/SplashScreen'
import Sidebar from './components/Sidebar'
import ChatInterface from './components/ChatInterface'
import SettingsModal from './SettingsModal'
import FilePreview from './FilePreview'

function App() {
  const messagesEndRef = useRef(null)

  // 1. System Status
  const { isBackendReady, connectionRetries, isIndexing, lastUpdate } = useSystemStatus()

  // 2. Session Management
  const {
    sessions, currentSessionId, setCurrentSessionId,
    createNewSession, deleteSession, loadSessions
  } = useSessions(isBackendReady)

  // 3. Knowledge Base
  const {
    documents, config, docsLoading, isRefreshing,
    fetchDocuments, searchQuery, setSearchQuery,
    expandedGroups, toggleGroup
  } = useKnowledgeBase(isBackendReady, isIndexing, lastUpdate)

  // 4. Chat
  const {
    messages, input, setInput, isLoading, handleSend
  } = useChat(currentSessionId, loadSessions)

  // 5. Modals State
  const [showSettings, setShowSettings] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)


  // --- Render ---

  if (!isBackendReady) {
    return <SplashScreen retryCount={connectionRetries} />
  }

  return (
    <div className="flex h-full bg-neutral-950 text-gray-100 font-sans overflow-hidden selection:bg-red-500/30">

      {/* Modals */}
      {showSettings && (
        <SettingsModal
          onClose={() => setShowSettings(false)}
          apiUrl={API_URL}
          apiKey={API_KEY}
          onConfigUpdate={() => {
            fetchDocuments()
            setShowSettings(false)
          }}
        />
      )}

      {previewFile && (
        <FilePreview
          file={previewFile}
          onClose={() => setPreviewFile(null)}
          apiUrl={API_URL}
          apiKey={API_KEY}
        />
      )}

      {/* Main Layout */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSessionSwitch={setCurrentSessionId}
        onSessionCreate={createNewSession}
        onSessionDelete={deleteSession}

        documents={documents}
        config={config}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onRefreshDocs={fetchDocuments}
        isRefreshingDocs={isRefreshing}
        isDocsLoading={docsLoading}
        expandedGroups={expandedGroups}
        onToggleGroup={toggleGroup}
        onPreviewFile={setPreviewFile}

        onOpenSettings={() => setShowSettings(true)}
      />

      <ChatInterface
        messages={messages}
        isLoading={isLoading}
        input={input}
        setInput={setInput}
        onSend={handleSend}
        messagesEndRef={messagesEndRef}
      />

    </div>
  )
}

export default App
