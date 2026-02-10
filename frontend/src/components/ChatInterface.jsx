import React from 'react'
import { Send, Loader2, PanelLeftOpen } from 'lucide-react'

export default function ChatInterface({ sidebarOpen, onToggleSidebar, messages, isLoading, input, setInput, onSend, messagesEndRef, sessionTitle }) {
    return (
        <div className="flex-1 flex flex-col min-w-0 bg-gradient-to-b from-neutral-950 to-neutral-900">
            {/* Header */}
            <div className="h-16 border-b border-red-900/20 flex items-center px-6 justify-between bg-black/20 backdrop-blur-md z-10 sticky top-0">
                <div className="flex items-center gap-4">
                    <div className="flex flex-col">
                        <span className="font-medium text-gray-200">{sessionTitle || "Chat Session"}</span>
                        <span className="text-xs text-red-400/80">Standard RAG Mode</span>
                    </div>
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
                                    if (!isLoading) onSend();
                                }
                            }}
                            placeholder="Ask anything about your documents..."
                            disabled={isLoading}
                            rows={1}
                            className="w-full bg-transparent text-gray-100 py-4 pl-5 pr-12 focus:outline-none placeholder-gray-600 resize-none max-h-[200px] overflow-y-auto"
                            style={{ height: 'auto', minHeight: '56px' }}
                        />
                        <button
                            onClick={onSend}
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
    )
}
