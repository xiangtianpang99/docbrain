import { useState, useEffect } from 'react'
import { X, Plus, Trash2, Save, RotateCw, Play, Clock, FolderOpen, Key } from 'lucide-react'
import axios from 'axios'
import clsx from 'clsx'

export default function SettingsModal({ onClose, apiUrl, apiKey, onConfigUpdate }) {
    const [activeTab, setActiveTab] = useState('paths')
    const [config, setConfig] = useState({
        watch_paths: [],
        schedule_interval_minutes: 60,
        enable_watchdog: true,
        enable_scheduler: true,
        api_key: '',
        deepseek_api_key: ''
    })
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [triggering, setTriggering] = useState(false)
    const [newPath, setNewPath] = useState('')

    useEffect(() => {
        fetchConfig()
    }, [])

    const fetchConfig = async () => {
        try {
            const response = await axios.get(`${apiUrl}/config`, {
                headers: { 'Authorization': `Bearer ${apiKey}` }
            })
            setConfig(response.data)
            setLoading(false)
        } catch (error) {
            console.error("Failed to load config", error)
            setLoading(false)
        }
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            await axios.post(`${apiUrl}/config`, config, {
                headers: { 'Authorization': `Bearer ${apiKey}` }
            })
            if (onConfigUpdate) onConfigUpdate()
            // Show checkmark or toast? for now just delay close slightly
            setTimeout(() => setSaving(false), 500)
        } catch (error) {
            console.error("Failed to save config", error)
            setSaving(false)
        }
    }

    const handleTriggerIndex = async () => {
        setTriggering(true)
        try {
            await axios.post(`${apiUrl}/actions/index`, {}, {
                headers: { 'Authorization': `Bearer ${apiKey}` }
            })
            alert("Indexing started in background.")
        } catch (error) {
            alert("Failed to trigger indexing: " + error.message)
        } finally {
            setTriggering(false)
        }
    }

    const addPath = () => {
        if (!newPath.trim()) return
        setConfig(prev => ({
            ...prev,
            watch_paths: [...(prev.watch_paths || []), newPath.trim()]
        }))
        setNewPath('')
    }

    const removePath = (idx) => {
        setConfig(prev => ({
            ...prev,
            watch_paths: prev.watch_paths.filter((_, i) => i !== idx)
        }))
    }

    if (!config) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-neutral-900 border border-white/10 w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col h-[600px]">

                {/* Header */}
                <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/5 rounded-t-2xl shrink-0">
                    <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
                        <RotateCw size={20} className="text-red-500" />
                        Settings & Configuration
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition text-gray-400 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                {/* Tabs & Content */}
                <div className="flex flex-1 overflow-hidden">

                    {/* Sidebar Tabs */}
                    <div className="w-64 border-r border-white/10 p-4 space-y-2 bg-black/20 overflow-y-auto shrink-0 scrollbar-dark">
                        <button
                            onClick={() => setActiveTab('paths')}
                            className={clsx("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition font-medium",
                                activeTab === 'paths' ? "bg-red-500/20 text-red-400" : "text-gray-400 hover:bg-white/5 hover:text-gray-200")}
                        >
                            <FolderOpen size={16} /> Data Sources
                        </button>
                        <button
                            onClick={() => setActiveTab('indexing')}
                            className={clsx("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition font-medium",
                                activeTab === 'indexing' ? "bg-red-500/20 text-red-400" : "text-gray-400 hover:bg-white/5 hover:text-gray-200")}
                        >
                            <Clock size={16} /> Indexing & Schedule
                        </button>
                        <button
                            onClick={() => setActiveTab('api')}
                            className={clsx("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition font-medium",
                                activeTab === 'api' ? "bg-red-500/20 text-red-400" : "text-gray-400 hover:bg-white/5 hover:text-gray-200")}
                        >
                            <Key size={16} /> API Keys
                        </button>
                    </div>

                    {/* Main Panel */}
                    <div className="flex-1 p-6 overflow-y-auto bg-neutral-900 scrollbar-dark">
                        {loading ? (
                            <div className="flex items-center justify-center h-full text-gray-500">Loading configuration...</div>
                        ) : (
                            <>
                                {/* Paths Tab */}
                                {activeTab === 'paths' && (
                                    <div className="space-y-6">
                                        <div>
                                            <h3 className="text-lg font-medium text-gray-200 mb-1">Watch Directories</h3>
                                            <p className="text-sm text-gray-500 mb-4">docBrain will monitor these folders for documents.</p>

                                            <div className="space-y-2 mb-4">
                                                {(config.watch_paths || []).map((path, idx) => (
                                                    <div key={idx} className="flex items-center justify-between p-3 bg-white/5 border border-white/5 rounded-lg group">
                                                        <span className="text-sm font-mono text-gray-300 truncate">{path}</span>
                                                        <button
                                                            onClick={() => removePath(idx)}
                                                            className="text-gray-500 hover:text-red-400 p-1 rounded opacity-0 group-hover:opacity-100 transition"
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </div>
                                                ))}
                                                {(!config.watch_paths || config.watch_paths.length === 0) && (
                                                    <div className="text-center text-gray-600 py-4 border border-dashed border-white/10 rounded-lg text-sm">
                                                        No paths configured. Add one below.
                                                    </div>
                                                )}
                                            </div>

                                            <div className="flex gap-2">
                                                <input
                                                    type="text"
                                                    value={newPath}
                                                    onChange={(e) => setNewPath(e.target.value)}
                                                    placeholder="C:\Users\Name\Documents\Notes"
                                                    className="flex-1 bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500/50"
                                                />
                                                <button
                                                    onClick={addPath}
                                                    className="bg-white/10 hover:bg-white/20 text-white px-3 py-2 rounded-lg transition"
                                                >
                                                    <Plus size={18} />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Indexing Tab */}
                                {activeTab === 'indexing' && (
                                    <div className="space-y-6">
                                        <div>
                                            <h3 className="text-lg font-medium text-gray-200 mb-4">Automation Settings</h3>

                                            <div className="space-y-4">
                                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
                                                    <div>
                                                        <div className="font-medium text-gray-200">Real-time Monitoring</div>
                                                        <div className="text-xs text-gray-500">Watch for file changes and update instantly</div>
                                                    </div>
                                                    <label className="relative inline-flex items-center cursor-pointer">
                                                        <input
                                                            type="checkbox"
                                                            className="sr-only peer"
                                                            checked={config.enable_watchdog}
                                                            onChange={(e) => setConfig({ ...config, enable_watchdog: e.target.checked })}
                                                        />
                                                        <div className="w-11 h-6 bg-neutral-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                                                    </label>
                                                </div>

                                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
                                                    <div>
                                                        <div className="font-medium text-gray-200">Scheduled Re-indexing</div>
                                                        <div className="text-xs text-gray-500">Run a full scan periodically</div>
                                                    </div>
                                                    <label className="relative inline-flex items-center cursor-pointer">
                                                        <input
                                                            type="checkbox"
                                                            className="sr-only peer"
                                                            checked={config.enable_scheduler}
                                                            onChange={(e) => setConfig({ ...config, enable_scheduler: e.target.checked })}
                                                        />
                                                        <div className="w-11 h-6 bg-neutral-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                                                    </label>
                                                </div>

                                                {config.enable_scheduler && (
                                                    <div className="p-4 rounded-xl border border-white/10 bg-black/20">
                                                        <label className="block text-sm font-medium text-gray-400 mb-2">Update Interval (Minutes)</label>
                                                        <input
                                                            type="number"
                                                            min="1"
                                                            value={config.schedule_interval_minutes}
                                                            onChange={(e) => setConfig({ ...config, schedule_interval_minutes: parseInt(e.target.value) || 60 })}
                                                            className="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-red-500/50"
                                                        />
                                                        <div className="text-xs text-gray-500 mt-1">Recommended: 60 minutes</div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <hr className="border-white/10" />

                                        <div>
                                            <h4 className="text-sm font-medium text-gray-400 mb-3">Manual Actions</h4>
                                            <button
                                                onClick={handleTriggerIndex}
                                                disabled={triggering}
                                                className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-200 px-4 py-2 rounded-lg transition disabled:opacity-50"
                                            >
                                                {triggering ? <RotateCw className="animate-spin" size={16} /> : <Play size={16} />}
                                                {triggering ? "Indexing Started..." : "Trigger Full Re-index Now"}
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* API Tab */}
                                {activeTab === 'api' && (
                                    <div className="space-y-6">
                                        <div>
                                            <h3 className="text-lg font-medium text-gray-200 mb-4">Service Keys</h3>

                                            <div className="space-y-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-400 mb-1">docBrain API protection Key</label>
                                                    <input
                                                        type="password"
                                                        value={config.api_key}
                                                        onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                                                        className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500/50"
                                                    />
                                                </div>

                                                <div>
                                                    <label className="block text-sm font-medium text-gray-400 mb-1">DeepSeek / LLM API Key</label>
                                                    <input
                                                        type="password"
                                                        value={config.deepseek_api_key}
                                                        onChange={(e) => setConfig({ ...config, deepseek_api_key: e.target.value })}
                                                        className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500/50"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/10 flex justify-end gap-3 bg-white/5 rounded-b-2xl">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm text-gray-400 hover:text-white transition"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving || loading}
                        className="flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white px-5 py-2 rounded-lg text-sm font-medium shadow-lg shadow-red-900/20 transition disabled:opacity-50"
                    >
                        {saving ? <RotateCw className="animate-spin" size={16} /> : <Save size={16} />}
                        {saving ? 'Saving...' : 'Save Configuration'}
                    </button>
                </div>
            </div>
        </div>
    )
}
