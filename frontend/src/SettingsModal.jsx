import { useState, useEffect } from 'react'
import { X, Plus, Trash2, Save, RotateCw, Play, Clock, FolderOpen, Key, Cpu, CheckCircle, AlertCircle } from 'lucide-react'
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
    const [testStatus, setTestStatus] = useState(null) // null | 'testing' | 'success' | 'error'
    const [testMessage, setTestMessage] = useState('')

    useEffect(() => {
        fetchConfig()
    }, [])

    const fetchConfig = async () => {
        try {
            const response = await axios.get(`${apiUrl}/config`, {
                headers: { 'Authorization': `Bearer ${apiKey}` }
            })
            // Ensure llm_providers structure exists locally even if API didn't return it fully populated yet
            const loadedConfig = response.data
            if (!loadedConfig.llm_providers) {
                loadedConfig.llm_providers = {
                    deepseek: { api_key: '', base_url: 'https://api.deepseek.com', model: 'deepseek-chat' },
                    openai: { api_key: '', base_url: 'https://api.openai.com/v1', model: 'gpt-4' },
                    ollama: { api_key: 'ollama', base_url: 'http://localhost:11434', model: 'llama3' },
                    custom: { api_key: '', base_url: '', model: '' }
                }
            }
            // Sync active provider
            if (!loadedConfig.active_provider) loadedConfig.active_provider = 'deepseek'

            setConfig(loadedConfig)
            setLoading(false)
        } catch (error) {
            console.error("Failed to load config", error)
            setLoading(false)
        }
    }

    const handleProviderChange = (provider) => {
        setConfig(prev => ({ ...prev, active_provider: provider }))
        setTestStatus(null)
    }

    const updateProviderConfig = (field, value) => {
        const provider = config.active_provider
        setConfig(prev => ({
            ...prev,
            llm_providers: {
                ...prev.llm_providers,
                [provider]: {
                    ...prev.llm_providers[provider],
                    [field]: value
                }
            }
        }))
    }

    const handleTestConnection = async () => {
        const provider = config.active_provider
        const providerConfig = config.llm_providers[provider]

        setTestStatus('testing')
        setTestMessage('Connecting...')

        try {
            const payload = {
                provider: provider,
                api_key: providerConfig.api_key,
                base_url: providerConfig.base_url,
                model: providerConfig.model
            }

            const response = await axios.post(`${apiUrl}/actions/test_llm`, payload, {
                headers: { 'Authorization': `Bearer ${apiKey}` }
            })

            if (response.data.status === 'success') {
                setTestStatus('success')
                setTestMessage(`Success! Latency: ${response.data.latency_ms}ms. Reply: "${response.data.reply}"`)
            } else {
                setTestStatus('error')
                setTestMessage(response.data.message || 'Unknown error')
            }
        } catch (error) {
            setTestStatus('error')
            setTestMessage(error.response?.data?.detail || error.message)
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
                            onClick={() => setActiveTab('models')}
                            className={clsx("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition font-medium",
                                activeTab === 'models' ? "bg-red-500/20 text-red-400" : "text-gray-400 hover:bg-white/5 hover:text-gray-200")}
                        >
                            <Cpu size={16} /> AI Models
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
                            <Key size={16} /> docBrain Protection
                        </button>
                    </div>

                    {/* Main Panel */}
                    <div className="flex-1 p-6 overflow-y-auto bg-neutral-900 scrollbar-dark">
                        {loading ? (
                            <div className="flex items-center justify-center h-full text-gray-500">Loading configuration...</div>
                        ) : (
                            <>
                                {/* Models Tab */}
                                {activeTab === 'models' && config.llm_providers && (
                                    <div className="space-y-6">
                                        <div>
                                            <h3 className="text-lg font-medium text-gray-200 mb-4">LLM Provider Settings</h3>

                                            {/* Provider Selector */}
                                            <div className="mb-6">
                                                <label className="block text-sm font-medium text-gray-400 mb-2">Active Provider</label>
                                                <div className="grid grid-cols-4 gap-2">
                                                    {['deepseek', 'openai', 'ollama', 'custom'].map((p) => (
                                                        <button
                                                            key={p}
                                                            onClick={() => handleProviderChange(p)}
                                                            className={clsx(
                                                                "px-2 py-3 rounded-xl border text-sm font-medium capitalize transition-all",
                                                                config.active_provider === p
                                                                    ? "bg-red-600 border-red-500 text-white shadow-lg shadow-red-900/20"
                                                                    : "bg-white/5 border-white/10 text-gray-400 hover:bg-white/10 hover:text-gray-200"
                                                            )}
                                                        >
                                                            {p}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Config Form */}
                                            <div className="p-5 bg-white/5 border border-white/10 rounded-xl space-y-4">
                                                <div className="flex items-center justify-between mb-2">
                                                    <h4 className="text-sm font-medium text-gray-200 capitalize flex items-center gap-2">
                                                        <Cpu size={14} className="text-red-400" />
                                                        {config.active_provider} Configuration
                                                    </h4>
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    <div className="md:col-span-2">
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">API Key</label>
                                                        <div className="relative">
                                                            <input
                                                                type="password"
                                                                value={config.llm_providers[config.active_provider]?.api_key || ''}
                                                                onChange={(e) => updateProviderConfig('api_key', e.target.value)}
                                                                placeholder={config.active_provider === 'ollama' ? 'Optional for Ollama' : 'sk-...'}
                                                                className="w-full bg-black/20 border border-white/10 rounded-lg pl-3 pr-10 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500/50"
                                                            />
                                                            <Key size={14} className="absolute right-3 top-2.5 text-gray-600" />
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">Base URL</label>
                                                        <input
                                                            type="text"
                                                            value={config.llm_providers[config.active_provider]?.base_url || ''}
                                                            onChange={(e) => updateProviderConfig('base_url', e.target.value)}
                                                            placeholder="https://api..."
                                                            className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500/50 font-mono"
                                                        />
                                                    </div>

                                                    <div>
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">Model Name</label>
                                                        <input
                                                            type="text"
                                                            value={config.llm_providers[config.active_provider]?.model || ''}
                                                            onChange={(e) => updateProviderConfig('model', e.target.value)}
                                                            placeholder="e.g. gpt-4"
                                                            className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500/50 font-mono"
                                                        />
                                                    </div>
                                                </div>

                                                {/* Test Connection Area */}
                                                <div className="pt-4 mt-4 border-t border-white/10 flex items-center justify-between">
                                                    <div className="flex-1 mr-4">
                                                        {testStatus && (
                                                            <div className={clsx("text-xs flex items-center gap-1.5",
                                                                testStatus === 'success' ? "text-green-400" :
                                                                    testStatus === 'error' ? "text-red-400" : "text-gray-400"
                                                            )}>
                                                                {testStatus === 'success' && <CheckCircle size={14} />}
                                                                {testStatus === 'error' && <AlertCircle size={14} />}
                                                                {testStatus === 'testing' && <RotateCw size={14} className="animate-spin" />}
                                                                <span className="truncate max-w-[300px]">{testMessage}</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                    <button
                                                        onClick={handleTestConnection}
                                                        disabled={testStatus === 'testing'}
                                                        className="px-3 py-1.5 bg-white/10 hover:bg-white/15 text-xs font-medium text-gray-300 rounded-lg transition disabled:opacity-50"
                                                    >
                                                        Test Connection
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
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

                                {/* Protection Tab (Renamed from API) */}
                                {activeTab === 'api' && (
                                    <div className="space-y-6">
                                        <div>
                                            <h3 className="text-lg font-medium text-gray-200 mb-4">Access Control</h3>

                                            <div className="space-y-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-400 mb-1">docBrain API Protection Key</label>
                                                    <input
                                                        type="password"
                                                        value={config.api_key}
                                                        onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                                                        className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500/50"
                                                    />
                                                    <p className="text-xs text-gray-500 mt-2">
                                                        This key protects your docBrain local server from unauthorized requests by browser extensions or other external tools.
                                                    </p>
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
