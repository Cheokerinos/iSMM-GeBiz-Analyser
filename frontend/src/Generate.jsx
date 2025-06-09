import React, { useState } from "react";
import axios from "axios";
import Sidebar from "./utilities/Sidebar";

export default function Generate(){
    const [keywords, setKeywords] = useState("");
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResults(null);

    const keywordsList = keywords
        .split(/[\n,]+/)
        .map((kw) => kw.trim())
        .filter(Boolean);
    
    try {
        const response = await fetch("/api/scrape", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ keywords: keywordsList }),
        });      
        if (!response.ok) {
          throw new Error("Failed to scrape tenders");
        }

        const data = await response.json();
        setResults(data);
        } catch (err) {
        setError(err.message || "Something went wrong");
        } finally {
        setLoading(false);
        }
    };
    return (
      <div className="flex bg-gray-100 min-h-screen w-full">
        <Sidebar/>
        <main className="flex-1 flex items-center justify-center">
          <div className="container bg-white max-w-xl mx-auto p-4 items-center justify-center lg-shadow rounded">
            <h1 className="text-2xl font-bold mb-4 justify center">Tender Scraper</h1>
            <form onSubmit={handleSubmit} className="mb-4">
              <label htmlFor="keywords" className="block mb-2 font-semibold">
                Enter keywords (comma or new line separated):
              </label>
              <textarea
                id="keywords"
                className="w-full border rounded p-2 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="Facilities Management, IFM, Integrated FM"
              ></textarea>
              <button
                type="submit"
                disabled={loading}
                className="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Scraping..." : "Start Scrape"}
              </button>
            </form>
      
            {error && <p className="text-red-600 mb-4">{error}</p>}
      
            {results && (
              <div className="overflow-auto max-h-96 border p-2 rounded">
                <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(results, null, 2)}</pre>
              </div>
            )}
          </div>
        </main>
      </div>
      );
}
