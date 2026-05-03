import { Home, History, Bookmark, Settings, LogOut, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Sidebar({ onNewSearch, activeView, setActiveView }) {
  // Grab the logout function from our AuthContext
  const { logout } = useAuth()

  return (
    <aside className="w-64 bg-[#050B14] border-r border-slate-800 flex flex-col h-full shrink-0">
      {/* Branding */}
      <div className="p-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-8 h-8 bg-blue-600 rounded text-white flex items-center justify-center font-bold text-xs tracking-wider shadow-lg shadow-blue-900/50">
            BIS
          </div>
          <div>
            <h1 className="text-white font-semibold text-sm leading-tight">BIS Copilot</h1>
          </div>
        </div>

        {/* Primary Action */}
        <button 
          onClick={onNewSearch}
          className="w-full bg-[#C3D0FF] text-[#0B1121] font-semibold py-2.5 rounded-lg mb-6 hover:bg-white transition-colors flex items-center justify-center gap-2 text-sm cursor-pointer"
        >
          <span>+</span> New Search
        </button>

        {/* Navigation */}
        <nav className="space-y-1">
          <NavItem 
            icon={<Home size={18} />} 
            label="Search" 
            active={activeView === 'search'} 
            onClick={() => setActiveView('search')} 
          />
          <NavItem 
            icon={<History size={18} />} 
            label="History" 
            active={activeView === 'history'} 
            onClick={() => setActiveView('history')} 
          />
          <NavItem 
            icon={<Bookmark size={18} />} 
            label="Saved" 
            active={activeView === 'saved'} 
            onClick={() => setActiveView('saved')} 
          />
        </nav>
      </div>

      {/* Bottom Actions */}
      <div className="mt-auto p-6 space-y-1">
        <NavItem 
          icon={<User size={18} />} 
          label="Profile" 
          active={activeView === 'profile'} 
          onClick={() => setActiveView('profile')} 
        />
        <NavItem icon={<Settings size={18} />} label="Settings" />
        
        {/* Logout Button */}
        <button 
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer text-slate-500 hover:text-red-400 hover:bg-red-500/10 mt-2"
        >
          <LogOut size={18} />
          Log out
        </button>
      </div>
    </aside>
  )
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer
      ${active ? 'bg-[#151C2C] text-white border border-slate-800' : 'text-slate-400 hover:text-white hover:bg-[#151C2C]/50'}
    `}>
      {icon}
      {label}
    </button>
  )
}