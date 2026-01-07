
import React from 'react';
import { CongressMember, Party } from '../types';

interface MemberCardProps {
  member: CongressMember;
  onSelect: (member: CongressMember) => void;
}

const MemberCard: React.FC<MemberCardProps> = ({ member, onSelect }) => {
  const partyColor = member.party === Party.DEMOCRAT ? 'text-blue-600 bg-blue-50' : 
                   member.party === Party.REPUBLICAN ? 'text-red-600 bg-red-50' : 
                   'text-slate-600 bg-slate-50';

  return (
    <div 
      onClick={() => onSelect(member)}
      className="bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all border border-slate-100 p-6 cursor-pointer group flex flex-col items-center text-center"
    >
      <div className="relative mb-4">
        <img 
          src={member.imageUrl} 
          alt={member.name}
          className="w-24 h-24 rounded-full object-cover border-4 border-white shadow-md"
        />
        <div className={`absolute bottom-0 right-0 w-6 h-6 rounded-full border-2 border-white ${member.party === Party.DEMOCRAT ? 'bg-blue-600' : member.party === Party.REPUBLICAN ? 'bg-red-600' : 'bg-slate-400'}`}></div>
      </div>
      
      <h3 className="text-xl font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
        {member.name}
      </h3>
      <p className="text-slate-500 font-medium mb-3">
        {member.title} • {member.state}{member.district ? `-${member.district}` : ''}
      </p>
      
      <span className={`px-4 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${partyColor}`}>
        {member.party}
      </span>
      
      <div className="mt-6 w-full text-left">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Key Committees</p>
        <div className="flex flex-wrap gap-2">
          {member.committees.slice(0, 2).map((committee, idx) => (
            <span key={idx} className="bg-slate-100 text-slate-700 text-[10px] px-2 py-1 rounded-md font-medium truncate max-w-full">
              {committee}
            </span>
          ))}
          {member.committees.length > 2 && (
            <span className="text-[10px] text-slate-400 font-medium">+{member.committees.length - 2} more</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default MemberCard;
