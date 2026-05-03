import { Shield, Activity, Bookmark, History } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function ProfileView({ historyCount, savedCount }) {
  const { user, logout } = useAuth()

  // Smarter Initials Logic
  const initials = (() => {
    if (!user?.username) return 'U'
    const parts = user.username.trim().split(/\s+/)
    if (parts.length > 1) {
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    return parts[0][0].toUpperCase()
  })()

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-3xl mx-auto mt-4">
      
      {/* Header Card */}
      <div className="bg-[#151C2C] border border-slate-800 rounded-2xl p-8 flex items-center gap-6 relative overflow-hidden mb-6 shadow-sm">
        {/* Background glow effect */}
        <div className="absolute -right-20 -top-20 w-64 h-64 bg-indigo-500/10 blur-3xl rounded-full pointer-events-none"></div>
        
        <div className="w-24 h-24 bg-slate-800 border-2 border-slate-700 rounded-full flex items-center justify-center shrink-0 shadow-xl relative z-10">
          {/* User Initials */}
          <span className="text-3xl font-bold text-slate-300 tracking-wider">
            {initials}
          </span>
        </div>
        
        <div className="relative z-10 flex-1">
          <h2 className="text-3xl font-bold text-white tracking-tight mb-1">
            {user?.username || 'User'}
          </h2>
          <p className="text-indigo-400 text-sm font-medium tracking-wide uppercase flex items-center gap-2">
            <Shield size={14} />
            Verified Industrial Partner
          </p>
        </div>

        <button 
          onClick={logout}
          className="relative z-10 px-6 py-2.5 rounded-lg bg-red-500/10 text-red-400 font-semibold border border-red-500/20 hover:bg-red-500/20 hover:border-red-500/40 transition-colors cursor-pointer"
        >
          Sign Out
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="bg-[#151C2C] border border-slate-800 rounded-xl p-6 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 bg-indigo-500/10 rounded-full flex items-center justify-center mb-4 border border-indigo-500/20">
            <Bookmark className="text-indigo-400" size={20} />
          </div>
          <h3 className="text-4xl font-bold text-white mb-1">{savedCount}</h3>
          <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">Saved Standards</p>
        </div>

        <div className="bg-[#151C2C] border border-slate-800 rounded-xl p-6 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center mb-4 border border-blue-500/20">
            <History className="text-blue-400" size={20} />
          </div>
          <h3 className="text-4xl font-bold text-white mb-1">{historyCount}</h3>
          <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">Total Queries</p>
        </div>
      </div>

      {/* Account Details */}
      <div className="bg-[#151C2C] border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800/80 bg-[#0B1121]/50">
          <h3 className="text-white font-medium flex items-center gap-2">
            <Activity size={16} className="text-slate-400" />
            Account Details
          </h3>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-1">Username</p>
              <p className="text-white text-lg">{user?.username}</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}