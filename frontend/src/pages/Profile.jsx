import React, { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'
import { User, Phone, Mail, Award, Save, Loader2, ChevronLeft, Hash, Activity, ShieldCheck, Cpu, MapPin, GraduationCap, Edit3, AlertCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

const Profile = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  
  const [profile, setProfile] = useState({
    name: '',
    phone_number: '',
    email: '',
    roll_number: '',
    section: '',
    branch: '',
    year: ''
  })
  const [stats, setStats] = useState({
    forms_filled: 0,
    total_points: 0,
    max_points: 0,
    accuracy: 0
  })

  useEffect(() => {
    fetchProfile()
    fetchStats()
  }, [user])

  const fetchProfile = async () => {
    if (!user) return
    try {
      const { data, error } = await supabase
        .from('Auto_bot')
        .select('*')
        .eq('auth_user_id', user.id)
        .single()

      if (data) {
        setProfile(data)
      }
    } catch (err) {
      console.error('Error fetching profile:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    if (!user) return
    try {
      const res = await fetch(`http://localhost:8000/api/stats/${user.id}`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Stats fetch error:', err)
    }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)

    try {
      const { error } = await supabase
        .from('Auto_bot')
        .update({
          name: profile.name,
          email: profile.email,
          phone_number: profile.phone_number,
          section: profile.section,
          branch: profile.branch,
          year: profile.year,
          roll_number: profile.roll_number
        })
        .eq('auth_user_id', user.id)

      if (error) throw error
      setMessage({ type: 'success', text: 'Identity synced successfully' })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <Loader2 className="animate-spin text-primary" size={40} />
    </div>
  )

  return (
    <div className="bg-black min-h-screen relative overflow-hidden flex flex-col items-center pt-32 pb-20 px-4">
      <div className="blob blob-1" />
      <div className="blob blob-2" />

      <div className="w-full max-w-2xl relative z-10 fade-in">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary/10 border border-primary/30 text-[10px] font-black uppercase tracking-[0.2em] text-primary hover:text-black hover:bg-primary transition-all mb-12 group shadow-[0_0_20px_rgba(0,191,255,0.1)]"
        >
          <ChevronLeft size={14} className="group-hover:-translate-x-1 transition-transform" />
          Return to Dashboard
        </Link>


        {/* Global Identity Card */}
        <div className="glass rounded-[3.5rem] border-white/10 overflow-hidden shadow-2xl">
          {/* Top Banner: Profile Info */}
          <div className="p-10 border-b border-white/5 bg-white/5 flex flex-col items-center text-center">
            <div className="relative mb-6">
              <div className="w-24 h-24 rounded-3xl bg-black border border-white/10 flex items-center justify-center shadow-inner group-hover:scale-105 transition-all">
                <User className="text-gray-800" size={48} />
              </div>
              <div className="absolute -bottom-1 -right-1 bg-green-500 w-5 h-5 rounded-full border-4 border-black animate-pulse" />
            </div>
            
            <h2 className="text-3xl font-black tracking-tighter uppercase mb-2">
              {profile.name || 'Anonymous'}
            </h2>
            <div className="flex items-center gap-4 text-[10px] text-gray-500 font-black uppercase tracking-widest mb-10">
              <span className="flex items-center gap-1.5"><Activity size={12} className="text-primary" /> Status: Active</span>
              <span className="w-1 h-1 rounded-full bg-white/10" />
              <span className="flex items-center gap-1.5"><ShieldCheck size={12} className="text-primary" /> Identity Verified</span>
            </div>

            {/* Neuro-Stats Grid */}
            <div className="grid grid-cols-3 gap-4 w-full px-4">
              <div className="glass p-4 rounded-3xl border-white/5 bg-black/40">
                <span className="block text-[8px] text-gray-600 font-black uppercase mb-1 tracking-widest">Forms Filled</span>
                <div className="text-xl font-black text-white">{stats.forms_filled || 0}</div>
              </div>
              <div className="glass p-4 rounded-3xl border-white/5 bg-black/40">
                <span className="block text-[8px] text-gray-600 font-black uppercase mb-1 tracking-widest">Total Points</span>
                <div className="text-xl font-black text-primary">{stats.total_points || 0}<span className="text-[10px] text-gray-700 ml-1">/ {stats.max_points || 0}</span></div>
              </div>
              <div className="glass p-4 rounded-3xl border-white/5 bg-black/40">
                <span className="block text-[8px] text-gray-600 font-black uppercase mb-1 tracking-widest">Efficiency</span>
                <div className="text-xl font-black text-green-500">{stats.accuracy || 0}%</div>
              </div>
            </div>
          </div>

          {/* Form Content */}
          <div className="p-10 md:p-14">
            <div className="flex items-center gap-3 mb-10">
              <ShieldCheck className="text-primary" size={20} />
              <h3 className="text-sm font-black uppercase tracking-[0.3em]">Your Profile</h3>
            </div>

            <form onSubmit={handleUpdate} className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <User size={12} /> Full Name
                  </label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="Enter Name"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <Mail size={12} className="text-primary" /> Email Address
                  </label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="name@example.com"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <Phone size={12} className="text-primary" /> Phone Number
                  </label>
                  <input
                    type="text"
                    value={profile.phone_number}
                    onChange={(e) => setProfile({ ...profile, phone_number: e.target.value })}
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full font-mono"
                    placeholder="+91 XXXXX XXXXX"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <Hash size={12} /> Roll Number
                  </label>
                  <input
                    type="text"
                    value={profile.roll_number}
                    onChange={(e) => setProfile({ ...profile, roll_number: e.target.value })}
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="Enter Roll No"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <Cpu size={12} /> Branch
                  </label>
                  <input
                    type="text"
                    value={profile.branch}
                    onChange={(e) => setProfile({ ...profile, branch: e.target.value })}
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="e.g. AIML"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <MapPin size={12} /> Section
                  </label>
                  <input
                    type="text"
                    value={profile.section}
                    onChange={(e) => setProfile({ ...profile, section: e.target.value })}
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="e.g. A"
                  />
                </div>
                <div className="space-y-3 md:col-span-2">
                  <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                    <GraduationCap size={12} /> Academic Year
                  </label>
                  <input
                    type="text"
                    value={profile.year}
                    onChange={(e) => setProfile({ ...profile, year: e.target.value })}
                    className="bg-white/5 border-white/5 py-4 rounded-xl text-sm w-full"
                    placeholder="e.g. 2nd Year"
                  />
                </div>
              </div>

              <div className="flex flex-col items-center pt-10">
                {message && (
                  <div className={`mb-6 p-4 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-3 w-full justify-center ${message.type === 'success' ? 'bg-primary/10 text-primary border border-primary/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
                    {message.type === 'success' ? <ShieldCheck size={16} /> : <AlertCircle size={16} />}
                    {message.text}
                  </div>
                )}
                <button 
                   type="submit" 
                   className="w-full md:w-fit px-12 h-14 text-[11px] font-black uppercase tracking-widest shadow-2xl rounded-2xl"
                   disabled={saving}
                >
                  {saving ? <Loader2 className="animate-spin" size={18} /> : <span>Save Changes</span>}
                </button>
              </div>
            </form>
          </div>

        </div>

        <p className="mt-12 text-center text-[10px] font-black text-gray-800 uppercase tracking-[0.5em] leading-loose">
          Profile Management
        </p>
      </div>
    </div>
  )
}

export default Profile
