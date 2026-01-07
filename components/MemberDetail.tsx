
import React from 'react';
import { CongressMember, Party } from '../types';
import IndustryChart from './IndustryChart';

interface MemberDetailProps {
  member: CongressMember;
  onClose: () => void;
}

const MemberDetail: React.FC<MemberDetailProps> = ({ member, onClose }) => {
  const partyColor = member.party === Party.DEMOCRAT ? 'text-blue-600 border-blue-600' : 
                   member.party === Party.REPUBLICAN ? 'text-red-600 border-red-600' : 
                   'text-slate-600 border-slate-600';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
      <div className="bg-white w-full max-w-5xl max-h-[90vh] overflow-y-auto rounded-3xl shadow-2xl relative animate-in fade-in zoom-in duration-300">
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 p-2 rounded-full hover:bg-slate-100 transition-colors text-slate-400 hover:text-slate-600"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>

        <div className="p-8 lg:p-12">
          {/* Header Info */}
          <div className="flex flex-col lg:flex-row gap-8 items-start mb-12">
            <img 
              src={member.imageUrl} 
              alt={member.name}
              className="w-32 h-32 lg:w-48 lg:h-48 rounded-2xl object-cover shadow-xl border-4 border-slate-50"
            />
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-2">
                <span className={`px-4 py-1.5 rounded-full text-sm font-bold border-2 ${partyColor}`}>
                  {member.party}
                </span>
                <span className="text-slate-400 font-medium">
                  {member.title} from {member.state}{member.district ? ` District ${member.district}` : ''}
                </span>
              </div>
              <h2 className="text-4xl lg:text-6xl font-black text-slate-900 mb-6">{member.name}</h2>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Committees Section */}
            <div>
              <div className="flex items-center gap-2 mb-6">
                <div className="w-1.5 h-8 bg-indigo-500 rounded-full"></div>
                <h3 className="text-2xl font-bold text-slate-900">Committee Assignments</h3>
              </div>
              <div className="space-y-3">
                {member.committees.map((committee, idx) => (
                  <div key={idx} className="flex items-start gap-4 p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
                    <div className="mt-1 flex-shrink-0 w-2 h-2 rounded-full bg-slate-400"></div>
                    <span className="text-slate-700 font-medium leading-tight">{committee}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Industry Influence Section */}
            <div>
              <div className="flex items-center gap-2 mb-6">
                <div className="w-1.5 h-8 bg-emerald-500 rounded-full"></div>
                <h3 className="text-2xl font-bold text-slate-900">Industry Involvement</h3>
              </div>
              <p className="text-slate-500 mb-6 text-sm">
                Based on recent campaign contributions and legislative priority tracking. Scores represent weighted relative influence.
              </p>
              <IndustryChart data={member.industries} />
            </div>
          </div>

          {/* Sources / Grounding */}
          <div className="mt-16 pt-8 border-t border-slate-100">
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Research Sources</h4>
            <div className="flex flex-wrap gap-3">
              {member.sources.map((source, idx) => (
                <a 
                  key={idx}
                  href={source.uri}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-slate-50 hover:bg-indigo-50 hover:text-indigo-600 rounded-lg text-sm text-slate-600 font-medium transition-all"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                  {source.title.length > 30 ? source.title.substring(0, 30) + '...' : source.title}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemberDetail;
