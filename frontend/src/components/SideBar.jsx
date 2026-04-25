import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  ScanTarget, 
  Activity, 
  MapPin, 
  Image as ImageIcon, 
  UserCircle,
  LogOut 
} from 'lucide-react';


const SideBar = () => {
  // Definimos la estructura de navegación en un array para mantener el JSX limpio (DRY principle)
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Inference', path: '/inference', icon: ScanTarget },
    { name: 'Detections', path: '/detections', icon: Activity },
    { name: 'Locations', path: '/locations', icon: MapPin },
    { name: 'Images', path: '/images', icon: ImageIcon },
    { name: 'Profile', path: '/profile', icon: UserCircle },
  ];

  return (
    <aside className="w-64 h-full bg-surface-dark border-r border-industrial-gray/20 flex flex-col hidden md:flex shadow-[4px_0_24px_rgba(0,0,0,0.4)] relative z-40">
      
      {/* Decorative Top Accent */}
      <div className="h-1 w-full bg-gradient-to-r from-rust-orange to-neon-cyan opacity-50"></div>

      {/* Navigation Links */}
      <nav className="flex-1 py-6 px-4 space-y-2 overflow-y-auto custom-scrollbar">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-300 font-mono text-sm tracking-wide relative overflow-hidden ${
                  isActive
                    ? 'text-neon-cyan bg-space-gray border-l-2 border-rust-orange'
                    : 'text-industrial-gray hover:text-white hover:bg-space-gray/50 border-l-2 border-transparent hover:border-neon-cyan/50'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {/* Background gradient for active state */}
                  {isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r from-rust-orange/10 to-transparent pointer-events-none"></div>
                  )}
                  
                  <Icon 
                    size={18} 
                    className={`relative z-10 transition-transform duration-300 ${isActive ? 'scale-110 drop-shadow-[0_0_8px_rgba(0,242,255,0.8)]' : 'group-hover:scale-110 group-hover:text-neon-cyan'}`} 
                  />
                  <span className="relative z-10">{item.name}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Section: System Diagnostics & Logout */}
      <div className="p-4 border-t border-industrial-gray/20 bg-surface-dark/50">
        
        {/* Fake Terminal Output for aesthetic */}
        <div className="mb-4 px-2 py-2 bg-space-gray rounded border border-industrial-gray/20 font-mono text-[10px] text-industrial-gray">
          <p className="text-neon-cyan opacity-70">&gt; Memory: Nominal</p>
          <p className="text-rust-orange opacity-70">&gt; GPU: Standby</p>
          <p className="opacity-50 animate-pulse">_</p>
        </div>

        <button 
          className="flex items-center gap-3 w-full px-4 py-2 font-mono text-sm text-industrial-gray hover:text-rust-orange transition-colors duration-200 group"
          onClick={() => {
            // Lógica de logout que conectaremos con Zustand más adelante
            console.log("Logout sequence initiated...");
          }}
        >
          <LogOut size={18} className="group-hover:-translate-x-1 transition-transform duration-200" />
          <span>Disconnect</span>
        </button>
      </div>

    </aside>
  );
};

export default SideBar;