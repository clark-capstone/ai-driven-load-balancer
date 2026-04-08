import React from 'react'
import { motion } from 'framer-motion'

const formatTime = value => {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString()
}

const LogFeed = ({ history }) => (
  <div className="flex h-[760px] flex-col overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/70 shadow-[0_24px_80px_rgba(15,23,42,0.35)] backdrop-blur">
    <div className="border-b border-white/10 p-5">
      <h3 className="text-lg font-black tracking-[0.18em] text-white">Live Routing History</h3>
      <p className="mt-2 text-sm text-slate-400">
        Every polling cycle records both server states and the final chosen server.
      </p>
    </div>

    <div className="flex-1 space-y-3 overflow-y-auto p-4 font-mono text-xs">
      {history.length === 0 && (
        <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 px-4 py-10 text-center text-slate-500">
          Waiting for the first live routing cycle.
        </div>
      )}

      {history.map(entry => (
        <motion.div
          key={entry.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-3xl border p-4 ${entry.status === 'ROUTED' ? 'border-emerald-400/20 bg-emerald-400/6' : 'border-rose-400/30 bg-rose-400/8'}`}
        >
          <div className="mb-2 flex items-center justify-between gap-3">
            <span className={`text-[11px] font-black uppercase tracking-[0.28em] ${entry.status === 'ROUTED' ? 'text-emerald-300' : 'text-rose-300'}`}>
              {entry.status}
            </span>
            <span className="text-slate-500">{formatTime(entry.timestamp)}</span>
          </div>

          <div className="text-slate-100">Chosen server: {entry.chosenServer}</div>
          <div className="mt-2 text-slate-400">{entry.decision}</div>

          <div className="mt-4 space-y-2">
            {entry.servers.map(server => (
              <div key={`${entry.id}-${server.name}`} className="rounded-2xl bg-white/5 px-3 py-2 text-slate-300">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-black uppercase tracking-[0.2em]">{server.name}</span>
                  <span>{server.active ? 'active' : 'inactive'}</span>
                </div>
                <div className="mt-1 flex items-center justify-between gap-3 text-[11px] text-slate-400">
                  <span>CPU: {typeof server.cpuUsage === 'number' ? `${server.cpuUsage.toFixed(1)}%` : 'n/a'}</span>
                  <span>Memory: {typeof server.memoryUsage === 'number' ? `${server.memoryUsage.toFixed(1)}%` : 'n/a'}</span>
                </div>
                {server.error && <div className="mt-1 text-[11px] text-rose-300">{server.error}</div>}
              </div>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  </div>
)

export default LogFeed
