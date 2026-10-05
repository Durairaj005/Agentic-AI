import React, { useState } from 'react';
import { Sparkles, LogOut, User as UserIcon, Shield, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

interface NavbarProps {
  backendOnline: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ backendOnline }) => {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
      <div className="flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-md shadow-brand-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold tracking-tight text-white">SmartRecruit AI</span>
              <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 font-semibold border border-brand-500/30">
                Enterprise
              </span>
            </div>
          </div>
        </div>

        {/* Right Section: Backend Status & User Profile */}
        <div className="flex items-center space-x-4">
          {backendOnline ? (
            <div className="hidden sm:flex items-center space-x-1.5 text-xs text-emerald-400 bg-emerald-950/40 px-3 py-1 rounded-full border border-emerald-800/60">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>FastAPI Connected</span>
            </div>
          ) : (
            <div className="hidden sm:flex items-center space-x-1.5 text-xs text-rose-400 bg-rose-950/40 px-3 py-1 rounded-full border border-rose-800/60">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Backend Offline</span>
            </div>
          )}

          {user && (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center space-x-3 p-1.5 rounded-xl hover:bg-slate-800/70 border border-transparent hover:border-slate-700 transition"
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-500 to-violet-500 flex items-center justify-center text-white text-xs font-bold shadow-sm">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div className="text-left hidden md:block">
                  <div className="text-xs font-medium text-slate-200">{user.name}</div>
                  <div className="flex items-center space-x-1">
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${
                        user.role === 'ADMIN'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-brand-500/20 text-brand-300'
                      }`}
                    >
                      {user.role}
                    </span>
                  </div>
                </div>
              </button>

              {dropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-30"
                    onClick={() => setDropdownOpen(false)}
                  />
                  <div className="absolute right-0 mt-2 w-56 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl py-2 z-40 text-xs">
                    <div className="px-4 py-2 border-b border-slate-800">
                      <div className="font-semibold text-slate-200">{user.name}</div>
                      <div className="text-slate-400 truncate">{user.email}</div>
                    </div>

                    <div className="py-1">
                      <div className="px-4 py-1.5 text-slate-400 flex items-center space-x-2">
                        <Shield className="w-3.5 h-3.5 text-brand-400" />
                        <span>Role: {user.role}</span>
                      </div>
                    </div>

                    <div className="border-t border-slate-800 pt-1">
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          logout();
                        }}
                        className="w-full text-left px-4 py-2 text-rose-400 hover:bg-rose-500/10 flex items-center space-x-2 transition"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
