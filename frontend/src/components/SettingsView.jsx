import { Settings, Shield, Trash2, Sliders } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import axios from 'axios'

export default function SettingsView({ withRationale, setWithRationale }) {
  const { user, logout } = useAuth()

  const handleDeleteAccount = async () => {
    if (window.confirm("Are you sure you want to delete your account? This action cannot be undone.")) {
      try {
        // Updated to POST to match the new backend route
        await axios.post('/user/delete') 
        logout() 
      } catch (err) {
        console.error(err)
        alert("Failed to delete account. Ensure the backend is restarted.")
      }
    }
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-3xl mx-auto mt-4 pb-12">
      <div className="mb-8 border-b border-slate-800/80 pb-6">
        <h2 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <Settings className="text-indigo-400" size={28} />
          Account Settings
        </h2>
        <p className="text-slate-400 mt-2">Manage your preferences and security for {user?.username}.</p>
      </div>

      <div className="space-y-6">
        <div className="bg-[#151C2C] border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-slate-800/80 bg-[#0B1121]/50 flex items-center gap-2">
            <Sliders size={18} className="text-slate-400" />
            <h3 className="text-white font-medium">System Preferences</h3>
          </div>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium mb-1">Default AI Rationale Mode</p>
                <p className="text-sm text-slate-500">Automatically generate AI explanations for search results.</p>
              </div>
              <Toggle active={withRationale} onClick={() => setWithRationale(!withRationale)} />
            </div>
          </div>
        </div>

        <div className="bg-[#151C2C] border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-slate-800/80 bg-[#0B1121]/50 flex items-center gap-2">
            <Shield size={18} className="text-slate-400" />
            <h3 className="text-white font-medium">Security & Data</h3>
          </div>
          <div className="p-6">
            <button 
              onClick={handleDeleteAccount}
              className="w-full flex items-center justify-between p-4 rounded-lg border border-red-900/30 bg-red-500/5 hover:bg-red-500/10 transition-colors group cursor-pointer"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center text-red-400 group-hover:bg-red-500/20 transition-colors">
                  <Trash2 size={18} />
                </div>
                <div className="text-left">
                  <p className="text-red-400 font-medium">Delete Account</p>
                  <p className="text-xs text-red-500/70">Permanently remove your account and all associated data.</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function Toggle({ active, onClick }) {
  return (
    <button onClick={onClick} className={`w-12 h-6 rounded-full relative transition-colors duration-300 ease-in-out cursor-pointer ${active ? 'bg-indigo-500' : 'bg-slate-700'}`}>
      <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-transform duration-300 ease-in-out ${active ? 'translate-x-7' : 'translate-x-1'}`} />
    </button>
  )
}