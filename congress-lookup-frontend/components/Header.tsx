
import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="pt-12 pb-8 text-center">
      <div className="inline-flex items-center justify-center gap-3 mb-6">
        <div className="p-3 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-200">
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
          </svg>
        </div>
        <h1 className="text-4xl font-black text-slate-900 tracking-tight">CongressConnect</h1>
      </div>
      <p className="text-xl text-slate-600 max-w-2xl mx-auto font-medium leading-relaxed">
        Investigate U.S. Congressional leadership, committee roles, and industry influence using real-time insights powered by AI.
      </p>
    </header>
  );
};

export default Header;
