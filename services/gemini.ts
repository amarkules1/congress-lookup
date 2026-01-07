
import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { Party, CongressMember, GroundingSource } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

const SYSTEM_INSTRUCTION = `
You are a political data analyst assistant. Your task is to provide accurate, up-to-date information about members of the U.S. Congress.
When a user searches for a member, you must:
1. Identify the correct member (Senator or Representative).
2. Retrieve their current standing committees.
3. Identify top 5 industries they are most involved with (based on campaign contributions or legislative focus).

CRITICAL: Return your response ONLY in the following JSON format within your text response. Do not include any other conversational text.
{
  "name": "Full Name",
  "title": "Senator / Representative",
  "party": "Democrat / Republican / Independent",
  "state": "State Code",
  "district": "District Number (if applicable)",
  "committees": ["Committee 1", "Committee 2"],
  "industries": [
    {"name": "Industry Name", "involvementScore": 85, "amount": 100000}
  ]
}
`;

export const searchCongressMember = async (query: string): Promise<CongressMember | null> => {
  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: `Search for this member of Congress: ${query}. Provide their current committees and industry involvement.`,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        tools: [{ googleSearch: {} }],
        temperature: 0.1,
      },
    });

    const text = response.text;
    if (!text) return null;

    // Extract JSON from the response text
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return null;

    const rawData = JSON.parse(jsonMatch[0]);

    // Extract grounding sources
    const sources: GroundingSource[] = [];
    const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
    if (chunks) {
      chunks.forEach((chunk: any) => {
        if (chunk.web && chunk.web.uri) {
          sources.push({
            title: chunk.web.title || chunk.web.uri,
            uri: chunk.web.uri
          });
        }
      });
    }

    // Map to our internal type
    const member: CongressMember = {
      id: Math.random().toString(36).substr(2, 9),
      name: rawData.name,
      title: rawData.title,
      party: rawData.party as Party,
      state: rawData.state,
      district: rawData.district,
      imageUrl: `https://picsum.photos/400/400?random=${Math.floor(Math.random() * 1000)}`, // Using picsum as placeholder for bio photo
      committees: rawData.committees || [],
      industries: rawData.industries || [],
      sources: sources
    };

    return member;
  } catch (error) {
    console.error("Error fetching congress member data:", error);
    return null;
  }
};
