import React from 'react'
import clsx from 'clsx'
import { RotateCw, Search, Loader2, Folder, ChevronRight, FileText, FileSpreadsheet, Presentation, FileCode, Globe, FileImage, FileQuestion } from 'lucide-react'

// --- Icon Helper ---
const getFileIcon = (filename, source) => {
    const ext = filename.split('.').pop().toLowerCase()

    // Check for webpage
    if (source && (source.startsWith('http') || source.startsWith('https'))) {
        return <Globe size={16} className="text-cyan-400 group-hover:brightness-125 transition-all" />
    }

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

    const conf = iconMap[ext] || { icon: FileQuestion, color: 'text-gray-500' }
    const IconComp = conf.icon
    return <IconComp size={16} className={`${conf.color} group-hover:brightness-125 transition-all`} />
}

export default function FileList({
    documents,
    config,
    searchQuery,
    setSearchQuery,
    onRefresh,
    isRefreshing,
    isLoading,
    expandedGroups,
    onToggleGroup,
    onPreview
}) {

    // Helper to group documents
    const getGroupedDocuments = () => {
        if (!config || !documents) return {}

        const groups = {}
        const watchPaths = config.watch_paths || []

        watchPaths.forEach(path => {
            groups[path] = []
        })
        groups['Others'] = []

        documents.forEach(doc => {
            const fname = doc.title || doc.source.split(/[\\/]/).pop()
            if (searchQuery && !fname.toLowerCase().includes(searchQuery.toLowerCase())) {
                return
            }

            let matched = false
            for (const wp of watchPaths) {
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

    const groupedDocs = getGroupedDocuments()

    return (
        <div className="flex-1 flex flex-col min-h-0">
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                <div>
                    <div className="text-xs font-semibold text-red-500/80 uppercase mb-3 px-2 tracking-wider flex justify-between items-center">
                        <div className="flex items-center gap-2">
                            <span>Knowledge Base</span>
                            <span className="text-[10px] bg-red-900/30 text-red-400 px-1.5 py-0.5 rounded border border-red-500/10">{documents.length}</span>
                        </div>
                        <button
                            onClick={onRefresh}
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
                        {isLoading ? (
                            <div className="flex justify-center py-4">
                                <Loader2 className="animate-spin text-red-500/50" size={20} />
                            </div>
                        ) : documents.length === 0 ? (
                            <div className="text-xs text-center text-gray-600 py-4 italic">
                                No documents found.<br />Add files to watched folders.
                            </div>
                        ) : (
                            Object.entries(groupedDocs).map(([groupName, groupDocs]) => {
                                if (groupDocs.length === 0) return null
                                const displayName = groupName === 'Others' ? 'Uncategorized' : groupName.split(/[\\/]/).filter(Boolean).pop() || groupName

                                return (
                                    <div key={groupName} className="space-y-1">
                                        <div
                                            onClick={() => onToggleGroup(groupName)}
                                            className="flex items-center gap-2 px-2 py-1 text-xs font-medium text-gray-500 hover:text-gray-300 cursor-pointer select-none transition-colors"
                                        >
                                            <div className={clsx("transition-transform duration-200", expandedGroups[groupName] ? "rotate-90" : "")}>
                                                <ChevronRight size={12} />
                                            </div>
                                            <Folder size={12} className="text-red-500/60" />
                                            <span className="truncate" title={groupName}>{displayName}</span>
                                            <span className="ml-auto text-[10px] bg-white/5 px-1 rounded">{groupDocs.length}</span>
                                        </div>

                                        <div className={clsx("overflow-hidden transition-all duration-300 ease-in-out", expandedGroups[groupName] ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0")}>
                                            <div className="pl-3 space-y-0.5 border-l border-white/5 ml-2.5 py-1">
                                                {groupDocs.map((doc, idx) => (
                                                    <div
                                                        key={`${groupName}-${idx}`}
                                                        onClick={() => onPreview(doc)}
                                                        className="group flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer text-gray-400 hover:text-white transition"
                                                        title={doc.source}
                                                    >
                                                        <div className="shrink-0 scale-75 opacity-70 group-hover:opacity-100 transition">
                                                            {getFileIcon(doc.title || doc.source, doc.source)}
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
        </div>
    )
}
