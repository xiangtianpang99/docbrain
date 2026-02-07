import React from 'react'
import { Settings } from 'lucide-react'
import SessionList from './SessionList'
import FileList from './FileList'

export default function Sidebar({
    sessions, currentSessionId, onSessionSwitch, onSessionCreate, onSessionDelete,
    documents, config, searchQuery, setSearchQuery, onRefreshDocs, isRefreshingDocs, isDocsLoading,
    expandedGroups, onToggleGroup, onPreviewFile, onOpenSettings
}) {
    return (
        <div className="w-64 bg-black/50 border-r border-red-900/20 flex flex-col shrink-0 backdrop-blur-xl">
            {/* Brand Header */}
            <div className="p-4 border-b border-red-900/20 flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-red-600 to-rose-600 rounded-lg flex items-center justify-center font-bold text-white shadow-lg shadow-red-900/20">dB</div>
                <span className="font-semibold text-lg tracking-tight bg-gradient-to-r from-gray-100 to-gray-400 bg-clip-text text-transparent">docBrain</span>
            </div>

            {/* 1. Knowledge Base (Top) */}
            <FileList
                documents={documents}
                config={config}
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                onRefresh={onRefreshDocs}
                isRefreshing={isRefreshingDocs}
                isLoading={isDocsLoading}
                expandedGroups={expandedGroups}
                onToggleGroup={onToggleGroup}
                onPreview={onPreviewFile}
            />

            {/* 2. Chat History (Bottom) */}
            <SessionList
                sessions={sessions}
                currentSessionId={currentSessionId}
                onSwitch={onSessionSwitch}
                onCreate={onSessionCreate}
                onDelete={onSessionDelete}
            />

            {/* Footer Settings */}
            <div className="p-4 border-t border-red-900/20">
                <button className="flex items-center gap-2 text-gray-400 hover:text-white transition w-full px-3 py-2 rounded-lg hover:bg-white/5" onClick={onOpenSettings}>
                    <Settings size={16} />
                    <span className="text-sm">Settings</span>
                </button>
            </div>
        </div>
    )
}
