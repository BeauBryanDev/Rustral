import React from 'react';
import { User, Bell } from 'lucide-react';
// Use React-router-dom for nav in futre 
import { Link } from 'react-router-dom';


const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full h-16 bg-surface-dark/80 backdrop-blur-md border-b border-neon-cyan/20 shadow-[0_4px_30px_rgba(0,242,255,0.05)]">
      <div className="flex items-center justify-between h-full px-6 max-w-7xl mx-auto">
        
        {/* Left Side: Brand & Logo */}
        <div className="flex items-center gap-3 cursor-pointer group">
          <div className="relative">
            {/* Glow effect on hover */}
            <div className="absolute inset-0 bg-rust-orange rounded-full blur-md opacity-20 group-hover:opacity-50 transition-opacity duration-300"></div>
            <img 
              src="../assets/fractal_rust_icon.svg"
              alt="Rustral Logo" 
              className="w-8 h-8 relative z-10"
              onError={(e) => {
              
                e.target.style.display = 'none';
              }}
            />
          </div>
          <h1 className="text-xl font-mono font-bold tracking-widest text-white uppercase group-hover:text-neon-cyan transition-colors duration-300">
            Rustral<span className="text-rust-orange">.OS</span>
          </h1>
        </div>

        {/* Right Side: User Controls & Status */}
        <div className="flex items-center gap-5">
          {/* Status Indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-space-gray rounded-full border border-industrial-gray/30">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-cyan opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-neon-cyan"></span>
            </span>
            <span className="text-xs font-mono text-industrial-gray uppercase tracking-wider">Sys_Online</span>
          </div>

          {/* Action Icons */}
          <button className="text-industrial-gray hover:text-rust-orange transition-colors duration-200">
            <Bell size={20} />
          </button>
          
          {/* User Avatar */}
          <button className="p-2 rounded-full bg-space-gray border border-industrial-gray/50 text-neon-cyan hover:border-neon-cyan hover:shadow-glow-cyan transition-all duration-300">
            <User size={20} />
          </button>
        </div>

      </div>
    </header>
  );
};

export default Header;