import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import clsx from 'clsx'
import { Trash2, Check, X } from 'lucide-react'

export default function SessionList({ sessions, currentSessionId, onSwitch, onCreate, onDelete }) {
    const [deleteConfirmId, setDeleteConfirmId] = useState(null)
    const [popupPos, setPopupPos] = useState({ top: 0, left: 0 })

    const handleDeleteClick = (e, sessionId) => {
        e.stopPropagation()
        const rect = e.currentTarget.getBoundingClientRect()
        // Position to the right of the button, slightly up to center vertically
        setPopupPos({ top: rect.top - 10, left: rect.right + 10 })
        setDeleteConfirmId(sessionId)
    }

    // Close popup on interaction elsewhere
    React.useEffect(() => {
        const close = () => setDeleteConfirmId(null)
        if (deleteConfirmId) {
            window.addEventListener('click', close)
            return () => window.removeEventListener('click', close)
        }
    }, [deleteConfirmId])

    return (
        <div className="flex-1 flex flex-col min-h-0 border-b border-red-900/20">
            {/* Header */}
            <div className="px-4 py-3 flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Chats</span>
                <button
                    onClick={onCreate}
                    className="text-red-400 hover:text-red-300 transition text-xs flex items-center gap-1 bg-red-500/10 px-2 py-1 rounded border border-red-500/10"
                >
                    + New
                </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto px-2 space-y-1 pb-2">
                {sessions.map(session => (
                    <div
                        key={session.id}
                        onClick={() => {
                            if (deleteConfirmId !== session.id) onSwitch(session.id)
                        }}
                        className={clsx("group relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-all",
                            currentSessionId === session.id ? "bg-red-900/20 text-white" : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
                        )}
                    >
                        <span className="truncate flex-1 pr-6">{session.title}</span>

                        <button
                            onClick={(e) => handleDeleteClick(e, session.id)}
                            className={clsx("absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded transition",
                                deleteConfirmId === session.id ? "text-red-400 bg-red-500/10 opacity-100" : "text-gray-500 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100"
                            )}
                            title="Delete Chat"
                        >
                            <Trash2 size={12} />
                        </button>
                    </div>
                ))}
            </div>

            {/* Fixed Confirmation Popup via Portal */}
            {deleteConfirmId && createPortal(
                <div
                    className="fixed z-[9999] bg-neutral-900 border border-red-500/30 rounded-lg shadow-2xl p-3 flex flex-col gap-3 min-w-[160px] animate-in fade-in zoom-in-95 duration-200"
                    style={{ top: popupPos.top, left: popupPos.left }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <span className="text-xs text-gray-300 font-medium whitespace-nowrap">是否删除聊天记录？</span>
                    <div className="flex items-center justify-end gap-2">
                        <button
                            onClick={() => setDeleteConfirmId(null)}
                            className="px-2 py-1 text-xs text-gray-400 hover:text-white hover:bg-white/10 rounded transition"
                        >
                            取消
                        </button>
                        <button
                            onClick={() => {
                                onDelete(deleteConfirmId)
                                setDeleteConfirmId(null)
                            }}
                            className="px-2 py-1 text-xs bg-red-600 hover:bg-red-500 text-white rounded transition shadow-lg shadow-red-900/20"
                        >
                            确定
                        </button>
                    </div>
                </div>,
                document.body
            )}
        </div>
    )
}
