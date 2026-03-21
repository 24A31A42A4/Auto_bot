import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { LogIn, Mail, Lock, Loader2, Zap, ArrowRight, AlertCircle, Eye, EyeOff } from 'lucide-react'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      console.error('Login error:', error)
      setError(error.message)
      setLoading(false)
    } else {
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen bg-black relative overflow-hidden flex flex-col items-center justify-center p-4">
      <div className="blob blob-1" />
      <div className="blob blob-2" />

      {/* Industrial-Grade Auth Terminal */}
      <div className="relative z-10 fade-in auth-terminal-width">
        
        {/* Floating Top Icon: Enforced Centering */}
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 z-20">
          <div className="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-icon border border-white/10 transition-all duration-300">
            <LogIn className="text-black" size={32} />
          </div>
        </div>

        <div className="glass p-10 pt-20 pb-12 rounded-[3.5rem] border-white/10 relative overflow-hidden shadow-2xl flex flex-col items-center">
          
          <div className="text-center mb-10">
            <h1 className="text-2xl font-black text-white mb-2">Welcome Back</h1>
            <p className="text-gray-500 text-xs font-medium">
              Please sign in to continue.
            </p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-4 rounded-xl mb-8 flex items-center gap-3 text-xs font-black uppercase tracking-widest animate-pulse w-full">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4 w-full relative z-10">
            
            {/* Input Hub: Absolute Icon Centering */}
            <div className="relative group">
              <div className="transform-v-center left-5 z-20 pointer-events-none">
                <Mail className="text-gray-500 group-focus-within:text-primary transition-colors" size={18} />
              </div>
              <input
                type="email"
                placeholder="Email Address"
                className="w-full bg-white/5 border-white/5 pl-14 pr-6 py-5 rounded-2xl text-sm focus:bg-white/10 transition-all font-medium"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="relative group">
              <div className="transform-v-center left-5 z-20 pointer-events-none">
                <Lock className="text-gray-500 group-focus-within:text-primary transition-colors" size={18} />
              </div>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                className="w-full bg-white/5 border-white/5 pl-14 pr-14 py-5 rounded-2xl text-sm focus:bg-white/10 transition-all font-medium"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="transform-v-center right-5 z-20 p-0 bg-transparent border-none text-gray-600 hover:text-white transition-colors flex items-center justify-center"
                style={{ height: '32px', width: '32px' }}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <div className="pt-6">
              <button 
                type="submit" 
                className="w-full h-14 bg-white text-black text-sm font-black uppercase tracking-widest shadow-2xl rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all"
                disabled={loading}
              >
                {loading ? <Loader2 className="animate-spin" size={20} /> : "Sign In"}
              </button>
            </div>
          </form>

          <div className="mt-10 pt-8 border-t border-white/5 text-center w-full">
            <p className="text-gray-500 font-black text-[10px] uppercase tracking-widest">
              Don't have an account?{' '}
              <Link to="/register" className="text-primary hover:text-white transition-colors ml-1">
                Sign Up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
