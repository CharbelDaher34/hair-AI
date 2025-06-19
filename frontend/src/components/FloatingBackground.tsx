import React from 'react';

const FloatingBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      {/* Floating shapes */}
      <div className="absolute top-10 left-10 w-72 h-72 bg-gradient-to-br from-blue-200/30 to-purple-200/30 rounded-full blur-3xl animate-float-slow"></div>
      <div className="absolute top-32 right-20 w-96 h-96 bg-gradient-to-br from-pink-200/25 to-orange-200/25 rounded-full blur-3xl animate-float-reverse"></div>
      <div className="absolute bottom-20 left-32 w-80 h-80 bg-gradient-to-br from-green-200/30 to-teal-200/30 rounded-full blur-3xl animate-float-diagonal"></div>
      <div className="absolute bottom-40 right-10 w-64 h-64 bg-gradient-to-br from-indigo-200/35 to-blue-200/35 rounded-full blur-3xl animate-float-slow"></div>
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-br from-violet-200/20 to-cyan-200/20 rounded-full blur-3xl animate-float-center"></div>
      
      {/* Additional smaller floating elements */}
      <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-gradient-to-br from-yellow-200/40 to-amber-200/40 rounded-full blur-2xl animate-float-small"></div>
      <div className="absolute top-3/4 right-1/4 w-40 h-40 bg-gradient-to-br from-rose-200/35 to-pink-200/35 rounded-full blur-2xl animate-float-small-reverse"></div>
      <div className="absolute top-1/3 right-1/3 w-28 h-28 bg-gradient-to-br from-emerald-200/40 to-green-200/40 rounded-full blur-2xl animate-float-tiny"></div>
      
      {/* Subtle grid pattern overlay */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: `radial-gradient(circle at 1px 1px, rgba(59,130,246,0.5) 1px, transparent 0)`,
        backgroundSize: '50px 50px'
      }}></div>
    </div>
  );
};

export default FloatingBackground; 