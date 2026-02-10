import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Settings, PanelLeftClose, PanelLeftOpen, FileText, MessageSquare, Database } from 'lucide-react'
import clsx from 'clsx'
import SessionList from './SessionList'
import FileList from './FileList'

// Helper for Mini Mode Item with Hover Drawer
function MiniModeItem({ icon: Icon, label, isActive, children }) {
    const [isHovered, setIsHovered] = useState(false)
    const [drawerPos, setDrawerPos] = useState(0)
    const itemRef = useRef(null)
    const closeTimeoutRef = useRef(null)

    useEffect(() => {
        if (isHovered && itemRef.current) {
            const rect = itemRef.current.getBoundingClientRect()
            setDrawerPos(rect.top)
        }
    }, [isHovered])

    const handleMouseEnter = () => {
        if (closeTimeoutRef.current) clearTimeout(closeTimeoutRef.current)
        setIsHovered(true)
    }

    const handleMouseLeave = () => {
        closeTimeoutRef.current = setTimeout(() => {
            setIsHovered(false)
        }, 300) // 300ms grace period
    }

    return (
        <div
            className="relative flex justify-center py-4 w-full"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            ref={itemRef}
        >
            <div className={clsx(
                "p-3 rounded-2xl transition-all duration-300 cursor-pointer relative group",
                isActive || isHovered ? "bg-red-600 shadow-lg shadow-red-900/40 text-white" : "text-gray-500 hover:bg-white/10 hover:text-gray-300"
            )}>
                <Icon size={24} strokeWidth={1.5} />

                {/* Active Indicator Dot */}
                {isActive && !isHovered && (
                    <span className="absolute -right-1 -top-1 w-3 h-3 bg-neutral-900 rounded-full flex items-center justify-center">
                        <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    </span>
                )}
            </div>

            {/* Hover Drawer Portal */}
            {isHovered && createPortal(
                <div
                    className="fixed left-20 top-4 bottom-4 w-80 bg-neutral-900/95 backdrop-blur-2xl border border-white/5 rounded-2xl shadow-2xl z-[9990] flex flex-col overflow-hidden animate-in slide-in-from-left-6 fade-in duration-300"
                    style={{
                        boxShadow: '0 0 50px -12px rgba(0, 0, 0, 0.75)'
                    }}
                    onMouseEnter={handleMouseEnter}
                    onMouseLeave={handleMouseLeave}
                >
                    {/* Decorative Connectors */}
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-transparent via-red-500/20 to-transparent opacity-50" />

                    <div className="p-5 border-b border-white/5 bg-white/5 flex items-center justify-between shrink-0">
                        <span className="font-semibold text-gray-100 flex items-center gap-2.5 text-lg tracking-tight">
                            <Icon size={20} className="text-red-500" /> {label}
                        </span>
                        <div className="flex gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500/40" />
                            <span className="w-1.5 h-1.5 rounded-full bg-white/20" />
                            <span className="w-1.5 h-1.5 rounded-full bg-white/20" />
                        </div>
                    </div>
                    <div className="flex-1 overflow-hidden flex flex-col relative bg-neutral-900/50">
                        {children}
                    </div>
                </div>,
                document.body
            )}
        </div>
    )
}

// Brand Logo Component
function BrandLogo({ collapsed }) {
    return (
        <div className={clsx("flex items-center gap-3 overflow-hidden transition-all duration-300", collapsed ? " justify-center w-full" : "")}>
            <div className="relative shrink-0 w-10 h-10 flex items-center justify-center group/logo">
                {/* Luminous Synapse Sphere Logo */}
                <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-2xl shadow-rose-500/30 transition-transform duration-500 group-hover/logo:scale-105">
                    <defs>
                        <linearGradient id="sphere-gradient" x1="5" y1="5" x2="35" y2="35" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stopColor="#f43f5e" /> {/* Rose 500 */}
                            <stop offset="50%" stopColor="#e11d48" /> {/* Rose 600 */}
                            <stop offset="100%" stopColor="#881337" /> {/* Rose 900 */}
                        </linearGradient>
                        <radialGradient id="core-glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(20 20) rotate(90) scale(12)">
                            <stop offset="0%" stopColor="#fff" stopOpacity="0.8" />
                            <stop offset="50%" stopColor="#fda4af" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#e11d48" stopOpacity="0" />
                        </radialGradient>
                        <linearGradient id="shine-overlay" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stopColor="white" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
                        </linearGradient>
                    </defs>

                    {/* Main Sphere Body */}
                    <circle cx="20" cy="20" r="16" fill="url(#sphere-gradient)" />

                    {/* Internal Neural Flow (Curved organic lines) */}
                    <path d="M20 10C20 10 24 14 24 20C24 26 20 30 20 30" stroke="white" strokeWidth="1.5" strokeOpacity="0.4" strokeLinecap="round" fill="none" />
                    <path d="M20 10C20 10 16 14 16 20C16 26 20 30 20 30" stroke="white" strokeWidth="1.5" strokeOpacity="0.4" strokeLinecap="round" fill="none" />
                    <path d="M10 20C10 20 14 16 20 16C26 16 30 20 30 20" stroke="white" strokeWidth="1.5" strokeOpacity="0.4" strokeLinecap="round" fill="none" />
                    <path d="M10 20C10 20 14 24 20 24C26 24 30 20 30 20" stroke="white" strokeWidth="1.5" strokeOpacity="0.4" strokeLinecap="round" fill="none" />

                    {/* Central Glowing Core */}
                    <circle cx="20" cy="20" r="3.5" fill="white" className="animate-pulse drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]" />

                    {/* Soft Core Glow Spread */}
                    <circle cx="20" cy="20" r="12" fill="url(#core-glow)" style={{ mixBlendMode: 'plus-lighter' }} />

                    {/* Glossy Reflection */}
                    <circle cx="20" cy="20" r="16" fill="url(#shine-overlay)" className="opacity-90" style={{ mixBlendMode: 'overlay' }} />
                </svg>
            </div>

            {!collapsed && (
                <div className="flex flex-col opacity-100 transition-opacity duration-300">
                    <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-rose-100 to-gray-300 bg-clip-text text-transparent" style={{ fontFamily: 'system-ui, sans-serif' }}>
                        DocBrain
                    </span>
                    <span className="text-[10px] uppercase tracking-[0.25em] text-rose-500 font-bold">
                        Intelligence
                    </span>
                </div>
            )}
        </div>
    )
}

export default function Sidebar({
    isOpen, onToggle,
    sessions, currentSessionId, onSessionSwitch, onSessionCreate, onSessionDelete,
    documents, config, searchQuery, setSearchQuery, onRefreshDocs, isRefreshingDocs, isDocsLoading,
    expandedGroups, onToggleGroup, onPreviewFile, onOpenSettings
}) {
    return (
        <div
            className={clsx(
                "bg-black/40 border-r border-white/5 flex flex-col shrink-0 backdrop-blur-xl transition-[width] duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1.0)] z-20",
                isOpen ? "w-72" : "w-20"
            )}
        >
            {/* 1. Header Area */}
            {isOpen ? (
                <div className="p-4 border-b border-white/5 flex items-center justify-between shrink-0 h-20">
                    <BrandLogo collapsed={false} />
                    <button onClick={onToggle} className="text-gray-500 hover:text-white transition p-2 hover:bg-white/10 rounded-lg" title="Collapse Sidebar">
                        <PanelLeftClose size={18} />
                    </button>
                </div>
            ) : (
                <div className="flex flex-col items-center gap-4 pt-4 border-b border-white/5 pb-4 shrink-0">
                    <BrandLogo collapsed={true} />
                    <button
                        onClick={onToggle}
                        className="p-2 text-gray-500 hover:text-white transition hover:bg-white/10 rounded-lg"
                        title="Expand Sidebar"
                    >
                        <PanelLeftOpen size={20} />
                    </button>
                </div>
            )}

            {/* 2. Content Area */}
            {isOpen ? (
                <>
                    {/* Expanded: Knowledge Base (Top 35%) */}
                    <div className="flex flex-col min-h-0 border-b border-white/5 transition-all duration-300" style={{ flex: '35 1 0%' }}>
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
                    </div>

                    {/* Expanded: Chat History (Bottom 65%) */}
                    <div className="flex flex-col min-h-0 transition-all duration-300" style={{ flex: '65 1 0%' }}>
                        <SessionList
                            sessions={sessions}
                            currentSessionId={currentSessionId}
                            onSwitch={onSessionSwitch}
                            onCreate={onSessionCreate}
                            onDelete={onSessionDelete}
                        />
                    </div>

                    {/* Expanded Footer */}
                    <div className="p-4 border-t border-white/5 bg-black/20">
                        <button
                            onClick={onOpenSettings}
                            className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-400 hover:text-gray-100 hover:bg-white/5 rounded-xl transition group border border-transparent hover:border-white/5"
                        >
                            <Settings size={18} className="group-hover:rotate-45 transition-transform duration-500 text-gray-500 group-hover:text-red-400" />
                            <span className="font-medium">Settings</span>
                        </button>
                    </div>
                </>
            ) : (
                /* Collapsed: Icon Strip */
                <div className="flex-1 flex flex-col gap-2 pt-2 items-center">

                    {/* Files Icon */}
                    <MiniModeItem icon={Database} label="Knowledge Base">
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
                    </MiniModeItem>

                    {/* Chats Icon */}
                    <MiniModeItem icon={MessageSquare} label="Chats">
                        <SessionList
                            sessions={sessions}
                            currentSessionId={currentSessionId}
                            onSwitch={onSessionSwitch}
                            onCreate={onSessionCreate}
                            onDelete={onSessionDelete}
                        />
                    </MiniModeItem>

                    <div className="flex-1" />

                    {/* Settings Icon */}
                    <div className="pb-4">
                        <button
                            onClick={onOpenSettings}
                            className="p-3 text-gray-500 hover:text-white transition hover:bg-white/10 rounded-xl"
                            title="Settings"
                        >
                            <Settings size={20} />
                        </button>
                    </div>
                </div>
            )}

        </div>
    )
}
