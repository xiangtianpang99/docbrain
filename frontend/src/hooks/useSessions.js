import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_URL, API_KEY } from '../config'

export function useSessions(isBackendReady) {
    const [currentSessionId, setCurrentSessionId] = useState(null)
    const [sessions, setSessions] = useState([])
    const [isSessionsLoading, setIsSessionsLoading] = useState(false)

    useEffect(() => {
        if (isBackendReady) {
            loadSessions()
        }
    }, [isBackendReady])

    const loadSessions = async () => {
        try {
            setIsSessionsLoading(true)
            const res = await axios.get(`${API_URL}/sessions`, {
                headers: { 'Authorization': `Bearer ${API_KEY}` }
            })
            if (res.data.sessions) {
                setSessions(res.data.sessions)
                // Auto-select logic if needed, but we'll leave that to the consumer or explicit user action usually
                // For now, replicating original behavior: auto-select most recent if none selected
                if (!currentSessionId && res.data.sessions.length > 0) {
                    // We won't automatically switch session ID here to avoid side-effects during render,
                    // but we could expose a "ready" state or handle it in a cleanup.
                    // For simplicity, let's just update the list.
                    // Original code did switchSession(res.data.sessions[0].id)
                    setCurrentSessionId(prev => prev || res.data.sessions[0].id)
                } else if (!currentSessionId && res.data.sessions.length === 0) {
                    // We can expose a method to create new session if needed
                }
            }
        } catch (e) {
            console.error("Failed to load sessions", e)
        } finally {
            setIsSessionsLoading(false)
        }
    }

    const createNewSession = async () => {
        try {
            const res = await axios.post(`${API_URL}/sessions`, {}, {
                headers: { 'Authorization': `Bearer ${API_KEY}` }
            })
            const newSession = { id: res.data.session_id, title: res.data.title, created_at: new Date().toISOString() }
            setSessions(prev => [newSession, ...prev])
            setCurrentSessionId(newSession.id)
            return newSession.id
        } catch (e) {
            console.error("Failed to create session", e)
        }
    }

    const deleteSession = async (sessionId) => {
        try {
            await axios.delete(`${API_URL}/sessions/${sessionId}`, {
                headers: { 'Authorization': `Bearer ${API_KEY}` }
            })
            setSessions(prev => prev.filter(s => s.id !== sessionId))
            if (currentSessionId === sessionId) {
                setCurrentSessionId(null)
            }
        } catch (e) {
            console.error("Failed to delete session", e)
        }
    }

    return {
        sessions,
        currentSessionId,
        setCurrentSessionId,
        createNewSession,
        deleteSession,
        loadSessions,
        isSessionsLoading
    }
}
