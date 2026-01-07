
import React, { useState, useCallback } from 'react';
import { CongressMember } from './types';
import { searchCongressMember } from './services/gemini';
import Header from './components/Header';
import SearchBar from './components/SearchBar';
import MemberCard from './components/MemberCard';
import MemberDetail from './components/MemberDetail';

const App: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<CongressMember[]>([]);
  const [selectedMember, setSelectedMember] = useState<CongressMember | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const member = await searchCongressMember(query);
      if (member) {
        // We prepend to see latest results first
        setResults(prev => {
          const exists = prev.find(m => m.name === member.name);
          if (exists) return prev;
          return [member, ...prev];
        });
      } else {
        setError("We couldn't find a member of Congress with that name. Please try another search.");
      }
    } catch (err) {
      setError("An error occurred while searching. Please try again later.");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="min-h-screen pb-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <Header />
        
        <SearchBar onSearch={handleSearch} isLoading={loading} />

        {error && (
          <div className="max-w-2xl mx-auto mb-12 p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span className="font-medium">{error}</span>
          </div>
        )}

        {results.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
            {results.map((member) => (
              <MemberCard 
                key={member.id} 
                member={member} 
                onSelect={setSelectedMember} 
              />
            ))}
          </div>
        ) : !loading && (
          <div className="text-center py-24 opacity-50">
            <div className="mb-6 inline-block p-6 bg-slate-100 rounded-full">
              <svg className="w-12 h-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-slate-400">No searches yet</h2>
            <p className="text-slate-500">Search for a senator or representative above to get started.</p>
          </div>
        )}

        {selectedMember && (
          <MemberDetail 
            member={selectedMember} 
            onClose={() => setSelectedMember(null)} 
          />
        )}
      </div>

      {/* Persistent Footer CTA */}
      <div className="fixed bottom-0 inset-x-0 p-4 pointer-events-none">
        <div className="max-w-md mx-auto bg-white/80 backdrop-blur-lg border border-slate-200 p-4 rounded-2xl shadow-2xl flex items-center justify-between pointer-events-auto">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <p className="text-sm font-semibold text-slate-700">Live Political Data</p>
          </div>
          <button 
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="text-xs font-bold text-indigo-600 hover:text-indigo-800 uppercase tracking-widest"
          >
            New Search ↑
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;
