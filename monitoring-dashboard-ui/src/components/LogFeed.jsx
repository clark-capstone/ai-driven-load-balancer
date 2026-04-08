import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, CheckCircle2, XCircle } from 'lucide-react'

const formatTime = value => {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const LogFeed = ({ history }) => (
  <div className="glass-card flex h-[690px] min-h-0 flex-col overflow-hidden xl:h-full">
    <div className="border-b border-white/5 p-6">
      <h3 className="text-sm font-bold tracking-tight text-white">Routing History</h3>
      <p className="mt-1 text-xs text-slate-500">
        Real-time log of load balancer decisions.
      </p>
    </div>

    <div className="log-scroll flex-1 space-y-3 overflow-y-auto p-4">
      <AnimatePresence initial={false}>
        {history.length === 0 ? (
          <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-white/5 bg-white/5 text-xs text-slate-500">
            Awaiting first telemetry...
          </div>
        ) : (
          history.map(entry => (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="group relative rounded-xl border border-white/5 bg-slate-900/30 p-4 transition-colors hover:bg-slate-900/50"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {entry.status === 'ROUTED' ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5 text-rose-500" />
                  )}
                  <span className={`text-[10px] font-black uppercase tracking-widest ${entry.status === 'ROUTED' ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {entry.status}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-[10px] font-medium text-slate-500">
                  <Clock className="h-3 w-3" />
                  {formatTime(entry.timestamp)}
                </div>
              </div>

              <div className="flex items-baseline gap-2">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Target:</span>
                <span className="text-sm font-bold text-slate-200">{entry.chosenServer}</span>
              </div>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">AI:</span>
                <span className={`text-[11px] font-bold ${entry.aiVerdict === 'BLOCKED' ? 'text-rose-300' : entry.aiVerdict === 'UNAVAILABLE' ? 'text-amber-300' : 'text-emerald-300'}`}>
                  {entry.aiVerdict}
                </span>
                <span className="text-[10px] text-slate-500">rate {entry.requestRate}</span>
              </div>
              
              <div className="mt-1 text-xs text-slate-400 leading-relaxed">
                {entry.decision}
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2">
                {entry.servers.map(server => (
                  <div key={`${entry.id}-${server.name}`} className="rounded-lg bg-slate-800/40 px-2 py-1.5 text-center">
                    <div className="truncate text-[9px] font-bold text-slate-400 uppercase">{server.name}</div>
                    <div className={`mt-0.5 text-[10px] font-mono font-bold ${server.active ? 'text-emerald-400/80' : 'text-rose-400/80'}`}>
                      {typeof server.cpuUsage === 'number' ? `${Math.round(server.cpuUsage)}%` : 'OFF'}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))
        )}
      </AnimatePresence>
    </div>
  </div>
)

export default LogFeed
