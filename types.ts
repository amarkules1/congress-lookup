
export enum Party {
  DEMOCRAT = 'Democrat',
  REPUBLICAN = 'Republican',
  INDEPENDENT = 'Independent',
  UNKNOWN = 'Unknown'
}

export interface IndustryData {
  name: string;
  amount?: number;
  involvementScore: number; // 1-100
}

export interface GroundingSource {
  title: string;
  uri: string;
}

export interface CongressMember {
  id: string;
  name: string;
  title: string; // Senator or Representative
  party: Party;
  state: string;
  district?: string;
  imageUrl: string;
  committees: string[];
  industries: IndustryData[];
  sources: GroundingSource[];
}

export interface SearchResult {
  members: Partial<CongressMember>[];
}
