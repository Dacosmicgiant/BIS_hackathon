import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Loader2 } from 'lucide-react'

export default function AuthModal() {
  const { login, signup } = useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isLogin) {
        await login(username, password)
      } else {
        await signup(username, password)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen w-screen bg-[#0B1121] items-center justify-center font-sans">
      <div className="w-full max-w-md bg-[#151C2C] border border-slate-800 p-8 rounded-2xl shadow-2xl">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-xl text-white flex items-center justify-center font-bold text-lg mx-auto mb-4 shadow-lg shadow-blue-900/50">
            BIS
          </div>
          <h2 className="text-2xl font-bold text-white">BIS Copilot</h2>
          <p className="text-slate-400 text-sm mt-1">Industrial Intelligence Platform</p>
        </div>

        {/* Toggle */}
        <div className="flex bg-[#0B1121] p-1 rounded-lg mb-6">
          <button 
            onClick={() => { setIsLogin(true); setError(''); }}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${isLogin ? 'bg-[#151C2C] text-white shadow' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Sign In
          </button>
          <button 
            onClick={() => { setIsLogin(false); setError(''); }}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${!isLogin ? 'bg-[#151C2C] text-white shadow' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Create Account
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Username</label>
            <input 
              type="text" 
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-[#0B1121] border border-slate-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Password</label>
            <input 
              type="password" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[#0B1121] border border-slate-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
            />
          </div>

          {error && <p className="text-red-400 text-sm text-center">{error}</p>}

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-[#C3D0FF] text-[#0B1121] font-bold py-3 rounded-lg mt-4 hover:bg-white transition-colors flex justify-center cursor-pointer"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : (isLogin ? 'Access Platform' : 'Initialize Account')}
          </button>
        </form>

      </div>
    </div>
  )
}