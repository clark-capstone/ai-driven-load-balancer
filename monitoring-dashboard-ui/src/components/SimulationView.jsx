import React, { useMemo } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Boxes, Cpu, Server, Activity, AlertCircle } from 'lucide-react'

const ServerCard = ({ server, isChosen }) => {
  const statusColor = !server.enabled ? 'text-slate-500' : server.active ? 'text-emerald-400' : 'text-rose-400'
  const borderColor = isChosen ? 'border-cyan-500/50 shadow-[0_0_15px_rgba(34,211,238,0.15)]' : 'border-white/5'
  const bgColor = isChosen ? 'bg-cyan-500/5' : 'bg-slate-900/40'

  return (
    <motion.div
      layout
      className={`relative rounded-xl border p-4 transition-all duration-300 ${borderColor} ${bgColor}`}
    >
      <div className="mb-3 flex items-start justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{server.region}</div>
          <div className="mt-0.5 text-sm font-black text-white">{server.name}</div>
        </div>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800/50 ${statusColor}`}>
          <Server className="h-4 w-4" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <div className="text-[9px] font-bold uppercase tracking-tight text-slate-500">CPU Usage</div>
          <div className="text-xs font-mono font-bold text-slate-200">
            {typeof server.cpuUsage === 'number' ? `${server.cpuUsage.toFixed(1)}%` : 'Offline'}
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-slate-800">
             <motion.div 
               initial={{ width: 0 }}
               animate={{ width: `${server.cpuUsage ?? 0}%` }}
               className={`h-full ${server.cpuUsage > 80 ? 'bg-rose-500' : server.cpuUsage > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`}
             />
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-[9px] font-bold uppercase tracking-tight text-slate-500">Memory</div>
          <div className="text-xs font-mono font-bold text-slate-200">
            {typeof server.memoryUsage === 'number' ? `${server.memoryUsage.toFixed(1)}%` : 'Offline'}
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-slate-800">
             <motion.div 
               initial={{ width: 0 }}
               animate={{ width: `${server.memoryUsage ?? 0}%` }}
               className="h-full bg-indigo-500"
             />
          </div>
        </div>
      </div>

      {server.error && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-rose-500/10 px-2 py-1.5 text-[10px] text-rose-300">
          <AlertCircle className="h-3 w-3" />
          <span className="truncate">{server.error}</span>
        </div>
      )}

      {isChosen && (
        <div className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-cyan-500 shadow-[0_0_8px_#22d3ee]">
          <Activity className="h-2.5 w-2.5 text-slate-950" />
        </div>
      )}
    </motion.div>
  )
}

const SimulationView = ({ servers, chosenServerId, cpuThreshold, requests }) => {
  // We use a simplified vertical positioning for target servers in the animation
  const serverIndexMap = useMemo(() => {
    const map = {}
    servers.forEach((s, i) => { map[s.id] = i })
    return map
  }, [servers])

  return (
    <div className="relative flex h-full min-h-[400px] flex-col overflow-hidden rounded-2xl bg-slate-950/20 p-4">
      <div className="grid h-full grid-cols-[1fr_auto_1.5fr] items-center gap-8">
        
        {/* Source Panel */}
        <div className="flex flex-col items-center justify-center">
          <div className="relative flex flex-col items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/5 bg-slate-900/50 text-slate-400">
              <Boxes className="h-8 w-8" />
            </div>
            <div className="text-center">
              <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Traffic Source</div>
              <div className="text-xs font-bold text-slate-300">Incoming Requests</div>
            </div>
            
            {/* Connection line to hub */}
            <div className="absolute left-full top-1/2 h-[1px] w-8 -translate-y-1/2 bg-gradient-to-r from-white/5 to-cyan-500/20" />
          </div>
        </div>

        {/* Load Balancer Hub */}
        <div className="relative z-10 flex flex-col items-center">
          <div className="group relative">
            <div className="absolute -inset-4 rounded-full bg-cyan-500/5 blur-xl group-hover:bg-cyan-500/10 transition-all duration-500" />
            <div className="relative flex h-20 w-20 flex-col items-center justify-center rounded-full border border-cyan-500/30 bg-slate-900/80 shadow-[0_0_30px_rgba(34,211,238,0.1)]">
              <Cpu className="h-8 w-8 text-cyan-400" />
              <div className="absolute -bottom-2 rounded-full bg-cyan-500 px-2 py-0.5 text-[8px] font-black text-slate-950 uppercase tracking-tighter">
                AI HUB
              </div>
            </div>
          </div>
          <div className="mt-6 text-center">
            <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Load Balancer</div>
            <div className="text-[10px] font-bold text-cyan-400/80">Threshold: {cpuThreshold}%</div>
          </div>
        </div>

        {/* Server List */}
        <div className="grid gap-3">
          {servers.map(server => (
            <ServerCard 
              key={server.id} 
              server={server} 
              isChosen={server.id === chosenServerId} 
            />
          ))}
        </div>
      </div>

      {/* Animation Layer */}
      <div className="pointer-events-none absolute inset-0 z-20">
        <AnimatePresence>
          {requests.map(request => {
            const targetIndex = serverIndexMap[request.targetServerId]
            if (targetIndex === undefined && request.status !== 'NO_SERVER') return null

            // Map server index to approximate vertical position (percentage)
            const targetTop = request.targetServerId 
              ? `${(100 / (servers.length * 2)) + (targetIndex * (100 / servers.length))}%` 
              : '50%'

            return (
              <React.Fragment key={request.id}>
                {/* Single Request Pulse: Source -> Hub -> Target */}
                <motion.div
                  initial={{ left: '15%', top: '50%', opacity: 0, scale: 0.5 }}
                  animate={{ 
                    left: ['15%', '43%', request.targetServerId ? '73%' : '55%'],
                    top: ['50%', '50%', targetTop],
                    opacity: [0, 1, 1, 0],
                    scale: [0.5, 1, 1, 0.5],
                  }}
                  transition={{
                    duration: 2.2, // Slower motion
                    ease: "easeInOut",
                    times: [0, 0.4, 0.9, 1]
                  }}
                  exit={{ opacity: 0 }}
                  className={`absolute h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full ${request.targetServerId ? 'bg-cyan-400 shadow-[0_0_10px_#22d3ee]' : 'bg-rose-400 shadow-[0_0_10px_#fb7185]'}`}
                />
                
                {/* Impact ripple */}
                {request.targetServerId && (
                  <motion.div
                    initial={{ left: '73%', top: targetTop, opacity: 0, scale: 0.5 }}
                    animate={{ 
                      opacity: [0, 0.5, 0],
                      scale: [0.5, 2, 3],
                    }}
                    transition={{
                      delay: 2.0, // Matches the end of the pulse
                      duration: 0.6
                    }}
                    className="absolute h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-400/50"
                  />
                )}
              </React.Fragment>
            )
          })}
        </AnimatePresence>
      </div>
      
      {/* Background patterns */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.03]" 
           style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '24px 24px' }} 
      />
    </div>
  )
}

export default SimulationView
