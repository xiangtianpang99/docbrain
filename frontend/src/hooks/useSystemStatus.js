import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_URL, API_KEY } from '../config'

export function useSystemStatus() {
    const [isBackendReady, setIsBackendReady] = useState(false)
    const [connectionRetries, setConnectionRetries] = useState(0)
    const [isIndexing, setIsIndexing] = useState(false)
    const [lastUpdate, setLastUpdate] = useState(0)

    // 1. Initial Health Check
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

    // 2. Poll System Status (Smart Polling)
    useEffect(() => {
        if (!isBackendReady) return

        const interval = setInterval(async () => {
            try {
                const res = await axios.get(`${API_URL}/system/status`, {
                    headers: { 'Authorization': `Bearer ${API_KEY}` }
                })

                const { is_indexing, last_update } = res.data
                setIsIndexing(is_indexing)
                setLastUpdate(last_update)
            } catch (e) {
                // Silent fail
            }
        }, 2000)

        return () => clearInterval(interval)
    }, [isBackendReady])

    return { isBackendReady, connectionRetries, isIndexing, lastUpdate }
}
