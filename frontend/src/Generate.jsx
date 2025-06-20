import React, { useState } from "react";
import authAxios from "./utilities/authAxios";
import Sidebar from "./utilities/Sidebar";

export default function Generate(){
    const [keywords, setKeywords] = useState("");
    const [inputValue, setInputValue] = useState("");
    const [tags, setTags] = useState([])
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [irrelevant, setIrrelevant] = useState([]);
    const [relevant, setRelevant] = useState([]);

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
      const response = await authAxios.post("/generate", {
        keywords: tags,
        });
      setRelevant(response.relevant);
      setIrrelevant(response.irrelevant);
      setResults(response.data);
    } catch (err) {
      if (err.response?.status === 401) {
        setError("Unauthorized. Please log in again.");
        localStorage.removeItem("accessToken"); // optional: clear token
      } else {
      setError(err.message || "Something went wrong");
        }
      } finally {
          setLoading(false);
        }
      };
    return (
      <div className="flex bg-gray-100 min-h-screen w-full">
        <Sidebar/>
        <main className="flex-1 flex items-center justify-center">
          <div className="container bg-white max-w-xl mx-auto p-4 items-center justify-center lg-shadow rounded-xl">
            <h1 className="text-2xl font-bold mb-4 justify center">Tender Scraper</h1>
            <form onSubmit={handleSubmit} className="mb-4">
              <input 
                type = "text"
                value = {inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && inputValue.trim()){
                    e.preventDefault()
                    if(!tags.includes(inputValue.trim())){
                      setTags([...tags, inputValue.trim()])
                    }
                    setInputValue("")
                  }
                }}
              placeholder="Type a keyword and press Enter"
              className="w-full border rounded p-2 focus:outline-none focus:ring-2 focus:ring-grey-400"
              >
              </input>
              <div className="flex flex-wrap gap-2 mt-2">
                {tags.map((tag, index) => (
                  <span key={index} className="bg-blue-50 text-blue-800 rounded-xl px-2 py-1 flex items-center space-x-1">
                    <span>{tag}</span>
                    <button
                      onClick={() => setTags(tags.filter((_, i) => i !== index))}
                      className="text-blue-500 hover:text-blue-700 bg-grey-300"
                    >
                      &times;
                    </button>
                  </span>
                ))}
              </div>
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
