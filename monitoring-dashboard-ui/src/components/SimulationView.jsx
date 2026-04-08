import React from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, Boxes, Cpu, Server } from 'lucide-react'

const toneForServer = (server, chosenServerId) => {
  if (!server.enabled) return 'border-slate-500/30 bg-slate-400/8 text-slate-400'
  if (!server.active) return 'border-rose-400/30 bg-rose-400/8 text-rose-200'
  if (server.id === chosenServerId) return 'border-emerald-300/50 bg-emerald-400/12 text-emerald-100'
  return 'border-white/10 bg-white/5 text-slate-100'
}

const targetPosition = {
  'server-1': { left: '82%', top: '22%' },
  'server-2': { left: '82%', top: '50%' },
  'server-3': { left: '82%', top: '78%' },
}

const SimulationView = ({ servers, chosenServerId, cpuThreshold, requests }) => (
  <div className="relative flex min-h-[540px] flex-col justify-between overflow-hidden rounded-[24px] border border-white/10 bg-[linear-gradient(145deg,_rgba(15,23,42,0.96),_rgba(15,23,42,0.68))] p-6 sm:p-8">
    <div className="grid gap-6 lg:grid-cols-[0.8fr_0.8fr_1.4fr]">
      <div className="flex items-center justify-center">
        <div className="w-full rounded-[28px] border border-cyan-300/25 bg-cyan-400/8 p-6 text-center">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-[24px] border border-cyan-300/30 bg-cyan-400/12">
            <Boxes className="h-10 w-10 text-cyan-200" />
          </div>
          <div className="text-sm font-black uppercase tracking-[0.24em] text-cyan-100">Request</div>
          <div className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-400">Single request block</div>
        </div>
      </div>

      <div className="flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="rounded-[28px] border-2 border-indigo-400/45 bg-indigo-500/12 p-6 shadow-[0_0_60px_rgba(99,102,241,0.2)]">
            <Cpu className="h-12 w-12 text-indigo-200" />
          </div>
          <div className="rounded-full bg-indigo-300/90 px-3 py-1 text-[10px] font-black uppercase tracking-[0.28em] text-slate-950">
            Threshold {cpuThreshold}%
          </div>
          <div className="text-center text-sm font-black uppercase tracking-[0.22em] text-white">Selection Engine</div>
        </div>
      </div>

      <div className="grid gap-3">
        {servers.map(server => (
          <div
            key={server.id}
            className={`rounded-[24px] border p-4 transition ${toneForServer(server, chosenServerId)}`}
          >
            <div className="mb-3 flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-black uppercase tracking-[0.22em]">{server.name}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.22em] text-slate-400">{server.region}</div>
                <div className="mt-2 font-mono text-[11px] text-slate-400">{server.baseUrl}</div>
              </div>
              <div className={`rounded-2xl border p-2.5 ${!server.enabled ? 'border-slate-500/20 bg-slate-500/10' : server.active ? 'border-emerald-300/35 bg-emerald-400/10' : 'border-rose-300/30 bg-rose-400/10'}`}>
                <Server className={`h-5 w-5 ${!server.enabled ? 'text-slate-400' : server.active ? 'text-emerald-200' : 'text-rose-200'}`} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="rounded-2xl bg-slate-900/70 p-2.5">
                <div className="text-[11px] uppercase tracking-[0.22em] text-slate-500">CPU</div>
                <div className="mt-1 text-lg font-black">{typeof server.cpuUsage === 'number' ? `${server.cpuUsage.toFixed(1)}%` : 'offline'}</div>
              </div>
              <div className="rounded-2xl bg-slate-900/70 p-2.5">
                <div className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Memory</div>
                <div className="mt-1 text-lg font-black">{typeof server.memoryUsage === 'number' ? `${server.memoryUsage.toFixed(1)}%` : 'offline'}</div>
              </div>
            </div>

            <div className="mt-3 flex items-center justify-between text-xs uppercase tracking-[0.22em] text-slate-400">
              <span>{!server.enabled ? 'disabled' : server.active ? 'active' : 'inactive'}</span>
              <span>{server.id === chosenServerId ? 'chosen server' : !server.enabled ? 'offline' : 'standby'}</span>
            </div>

            {server.error && (
              <div className={`mt-3 rounded-2xl border px-3 py-2 text-xs ${server.enabled ? 'border-rose-300/25 bg-rose-400/8 text-rose-200' : 'border-slate-500/20 bg-slate-500/10 text-slate-400'}`}>
                {server.error}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>

    <div className="pointer-events-none absolute inset-x-8 inset-y-8 hidden lg:block">
      <div className="absolute left-[16%] top-1/2 h-[2px] w-[18%] -translate-y-1/2 bg-gradient-to-r from-cyan-400/10 to-cyan-300/60" />
      <div className="absolute left-[34%] top-1/2 h-[2px] w-[42%] -translate-y-1/2 bg-gradient-to-r from-indigo-300/70 to-emerald-300/40" />

      <AnimatePresence>
        {requests.map(request => (
          <React.Fragment key={request.id}>
            <motion.div
              initial={{ left: '14%', top: '50%', opacity: 0, scale: 0.35 }}
              animate={{
                left: '34%',
                top: '50%',
                opacity: [0, 1, 1],
                scale: [0.35, 1, 1],
                transition: { duration: 0.7, ease: 'easeOut' },
              }}
              exit={{ opacity: 0 }}
              className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-300 shadow-[0_0_18px_#67e8f9]"
            />

            <motion.div
              initial={{ left: '34%', top: '50%', opacity: 0, scale: 0.55 }}
              animate={{
                left: request.targetServerId ? (targetPosition[request.targetServerId]?.left ?? '82%') : '34%',
                top: request.targetServerId ? (targetPosition[request.targetServerId]?.top ?? '50%') : '50%',
                opacity: request.targetServerId ? [0, 1, 1] : [0, 1, 1],
                scale: [0.55, 1, 1],
                transition: { delay: 0.65, duration: 1.05, ease: 'easeInOut' },
              }}
              exit={{ opacity: 0, scale: 0.5 }}
              className={`absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full ${request.targetServerId ? 'bg-emerald-300 shadow-[0_0_18px_#86efac]' : 'bg-rose-300 shadow-[0_0_18px_#fda4af]'}`}
            />

            {request.targetServerId && (
              <motion.div
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{
                  opacity: [0, 0.9, 0],
                  scale: [0.7, 1.35, 1.7],
                  transition: { delay: 1.55, duration: 0.45 },
                }}
                exit={{ opacity: 0 }}
                className="absolute h-6 w-6 -translate-x-1/2 -translate-y-1/2 rounded-full border border-emerald-300/70"
                style={{
                  left: targetPosition[request.targetServerId]?.left ?? '82%',
                  top: targetPosition[request.targetServerId]?.top ?? '50%',
                }}
              />
            )}
          </React.Fragment>
        ))}
      </AnimatePresence>
    </div>

    <div className="mt-8 flex items-center justify-center gap-3 text-xs font-black uppercase tracking-[0.28em] text-slate-500">
      <span>Request block</span>
      <ArrowRight className="h-4 w-4" />
      <span>Choose best server</span>
      <ArrowRight className="h-4 w-4" />
      <span className="text-emerald-200">Animate to chosen server</span>
    </div>

    <div className="pointer-events-none absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(circle, rgba(34,211,238,0.7) 1px, transparent 1px)', backgroundSize: '26px 26px' }} />
  </div>
)

export default SimulationView
