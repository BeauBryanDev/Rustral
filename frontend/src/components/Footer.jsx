import React from 'react';


const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full py-4 bg-space-gray border-t border-industrial-gray/20">
      <div className="flex flex-col sm:flex-row items-center justify-between px-6 max-w-7xl mx-auto">
        
        {/* Copyright & Info */}
        <p className="text-xs font-mono text-industrial-gray uppercase tracking-widest">
          &copy; {currentYear} Rustral Corp. <span className="hidden sm:inline">| All parameters nominal.</span>
        </p>

        {/* Tech Stack Indicators */}
        <div className="flex items-center gap-4 mt-2 sm:mt-0 text-xs font-mono">
          <span className="flex items-center gap-1 text-industrial-gray">
            <span className="text-rust-orange">■</span> YOLOv8-ONNX
          </span>
          <span className="flex items-center gap-1 text-industrial-gray">
            <span className="text-neon-cyan">■</span> React.v18
          </span>
        </div>

      </div>
    </footer>
  );
};

export default Footer;