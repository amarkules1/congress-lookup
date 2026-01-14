import { CongressMember } from "../types";

export const searchCongressMember = async (query: string): Promise<CongressMember | null> => {
  try {
    // In development mode with separate frontend/backend servers, you might need the full URL
    // e.g., 'http://localhost:5000/api/search' if not proxied.
    // Assuming relative path works (proxy setup or served by Flask) or CORS allows localhost:5000.
    // We will try a relative path first, which is best for production.
    // If running Vite locally without proxy to 5000, this might fail unless we use absolute.
    // Given CORS is enabled in backend, let's allow an env var or default to relative.

    // For simplicity in this refactor, we'll try relative. If user runs `pipenv run flask`, it serves safely.
    // If they run `npm run dev`, they might need to proxy. 
    // Let's assume the user might be running frontend separate. 
    // We will default to relative path.
    const baseUrl = '';
    const response = await fetch(`${baseUrl}/api/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      console.error(`Backend returned code ${response.status}: ${response.statusText}`);
      const text = await response.text();
      console.error("Response body:", text);
      return null;
    }

    const member: CongressMember = await response.json();
    return member;
  } catch (error) {
    console.error("Error fetching congress member data:", error);
    return null;
  }
};
