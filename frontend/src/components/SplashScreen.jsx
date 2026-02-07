import React from 'react'

export default function SplashScreen({ retryCount }) {
    return (
        <div className="flex flex-col items-center justify-center h-screen bg-neutral-950 text-white gap-4">
            <div className="relative">
                <div className="w-16 h-16 border-4 border-red-900/30 border-t-red-500 rounded-full animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xl">🧠</span>
                </div>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">docBrain</h1>
            <div className="text-neutral-500 text-sm animate-pulse flex flex-col items-center gap-1">
                <span>Establishing Neural Link...</span>
                <span className="text-xs text-neutral-600">Attempt {retryCount + 1}</span>
            </div>
        </div>
    )
}
