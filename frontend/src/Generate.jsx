import React, { useEffect, useState, useRef } from "react";
import authAxios from "./utilities/authAxios";
import Sidebar from "./utilities/Sidebar";
import { CloudSnowIcon } from "lucide-react";

export default function Generate(){
    const [keywords, setKeywords] = useState("");
    const [inputValue, setInputValue] = useState("");
    const [tags, setTags] = useState([])
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [scrapedData, setScrapedData] = useState([]);
    const [saveStatus, setSaveStatus] = useState({});
    const [classifiedTenders, setClassifiedTenders] = useState([]);
    const [userDecisions, setUserDecisions] = useState({});
    const [results, setResults] = useState(null);
    const abortController = useRef(null)


    const handleSubmit = async (e) => {
        e.preventDefault();
        abortController.current?.abort()    // just in case a previous one is still around
        const controller = new AbortController()
        abortController.current = controller
        setLoading(true);
        setError(null);
        setResults(null);

    const keywordsList = keywords
        .split(/[\n,]+/)
        .map((kw) => kw.trim())
        .filter(Boolean);
    
    
    try {
      const scraped = await authAxios.post("/generate", {
        keywords: tags},
        { signal: controller.signal});
      setResults(scraped.data);
      setScrapedData(scraped.data);
      const titles = scraped.data.results.map(r => r.Title);
      const { data : cls } = await authAxios.post("/classify", {
        tenders: titles,
        keywords: keywords.split(',').map(k => k.trim())
      },
      { signal: controller.signal });
      setClassifiedTenders(cls);
    } catch (err) {
      if (err.response?.status === 401) {
        setError("Unauthorized. Please log in again.");
        localStorage.removeItem("accessToken"); // optional: clear token
      } 
      if (err.name === 'CanceledError') {
        setError("Scraping cancelled by user.");
      }
      else {
      setError(err.message || "Something went wrong");
        }
      } finally {
          setLoading(false);
        }
    };

    useEffect(() => {
      const init = {};
      classifiedTenders.forEach(tender => {
        init[tender.title] = tender.ai_prediction; // or `undefined` if you want users to choose
      });
      setUserDecisions(init);
    }, [classifiedTenders]);

    function enrichTenderData(classifiedTender) {
      const full = scrapedData.results.find(t => t.Title === classifiedTender.title);
      const rawAwardee = full?.Awardee;
      const awardeeString = Array.isArray(rawAwardee)
        ? rawAwardee.join(", ")
        : rawAwardee || "";
      return {
        title: classifiedTender.title,
        tender_number: full?.["Tender Number"] || "",
        agency: full.Agency,
        ref_number: full?.["Ref_Num"] || "",
        awarded: full.Awarded,
        awardee: awardeeString,
        respondents: full?.Respondents,
        num_of_respondents: full?.["Num of Respondents"] || 0,
        keywords: tags,
        ai_prediction: classifiedTender.ai_prediction,
        ai_confidence: classifiedTender.ai_confidence,
        user_decision: userDecisions[classifiedTender.title],
      };
    }
    const handleStop = async () => {
      // tell the browser to immediately cancel that fetch
      abortController.current?.abort()
      setLoading(false)
      } 
    useEffect(() => {
      return () => abortController.current?.abort();
    }, []);

    function makedecisionsPayload() {
        return classifiedTenders
        .map(enrichTenderData)
        .filter(item => item.user_decision === true);;
      }
    const handleDecisionChange = (title, decision) => {
        setUserDecisions(prev => ({
          ...prev,
          [title]: decision
        }));
      };

      function saveOne(tender){
        setSaveStatus(s => ({ ...s, [tender.title]: "saving" }));
        const enriched = enrichTenderData(tender);
        if (!enriched.user_decision) {
          setSaveStatus(s => ({
            ...s,
            [tender.title]: "removed"   // or whatever label you like
          }));
          return Promise.resolve();     // do nothing
        }
        return authAxios.post("/save-decisions", { decisions: [enriched] });
      };

      function saveAll() {
        const payload = makedecisionsPayload();
        console.log("Payload to send:", JSON.stringify({ decisions: payload }, null, 2));
        return authAxios.post("/save-decisions", { decisions: payload });
      };


    return (
      <div className="flex bg-gray-100 min-h-screen w-full">
        <Sidebar/>
        <main className="flex-1 flex items-center justify-center">
          <div className="container bg-white mx-auto p-4 items-center justify-center lg-shadow rounded-xl">
            <h1 className="text-2xl font-bold mb-4 justify center">Tender Scraper</h1>
            <form onSubmit={handleSubmit} className="w-xl mb-4">
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
            {classifiedTenders.length > 0 && (
        <div className="mb-8 bg-white p-4 rounded-lg shadow">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-xl font-semibold">Classified Tenders</h2>
            <span className="text-sm text-gray-500">
              {classifiedTenders.length} results
            </span>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead>
                <tr className="bg-gray-100">
                  <th className="py-3 px-4 text-left">Tender Title</th>
                  <th className="py-3 px-4 text-center">AI Prediction</th>
                  <th className="py-3 px-4 text-center">Confidence</th>
                  <th className="py-3 px-4 text-center">Your Decision</th>
                  <th className="py-3 px-4 text-center">Save to DB</th>
                </tr>
              </thead>
              <tbody>
                {classifiedTenders.map((tender, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="py-3 px-4 border-b">{tender.title}</td>
                    <td className="py-3 px-4 border-b text-center">
                      <span className={`inline-block px-3 py-1 rounded-full text-sm ${
                        tender.ai_prediction ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {tender.ai_prediction ? 'Relevant' : 'Irrelevant'}
                      </span>
                    </td>
                    <td className="py-3 px-4 border-b text-center">
                      <span className="font-mono">
                        {Math.round(tender.ai_confidence * 100)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 border-b text-center">
                      <div className="flex justify-center">
                        <div className="flex items-center space-x-4">
                          <label className="flex items-center">
                            <input
                              type="radio"
                              name={`decision-${index}`}
                              checked={userDecisions[tender.title] === true}
                              onChange={() => handleDecisionChange(tender.title, true)}
                              className="form-radio h-4 w-4 text-green-600"
                            />
                            <span className="ml-2 text-sm">Keep</span>
                          </label>
                          <label className="flex items-center">
                            <input
                              type="radio"
                              name={`decision-${index}`}
                              checked={userDecisions[tender.title] === false}
                              onChange={() => handleDecisionChange(tender.title, false)}
                              className="form-radio h-4 w-4 text-red-600"
                            />
                            <span className="ml-2 text-sm">Remove</span>
                          </label>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 border-b text-center">
                      <button
                        onClick={() => saveOne(tender)}
                        disabled={userDecisions[tender.title] === undefined}
                        className={`text-sm px-3 py-1 rounded ${
                          saveStatus[tender.title] === 'success'
                            ? 'bg-green-100 text-green-800'
                            : saveStatus[tender.title] === 'error'
                            ? 'bg-red-100 text-red-800'
                            : saveStatus[tender.title] === 'saving'
                            ? 'bg-gray-200 text-gray-800 animate-pulse'
                            : userDecisions[tender.title] === undefined
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                        }`}
                      >
                        {saveStatus[tender.title] === 'success' 
                          ? '✓ Saved' 
                          : saveStatus[tender.title] === 'error'
                          ? '✗ Failed'
                          : saveStatus[tender.title] === 'saving'
                          ? 'Saving...'
                          : 'Save to DB'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="mt-6 flex justify-center">
            <button
              onClick={() => {
                saveAll()
                .then(() => /* show success */ setSaveStatus(s => ({ ...s, all: 'success' })))
              }}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded font-medium"
            >
              Save All Decisions
            </button>
          </div>
        </div>
      )}
      
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-xl">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-4"></div>
              <div>
                <p className="font-medium">Scraping Gebiz</p>
                <p className="text-sm text-gray-600">Searching for tenders...</p>
                <button className="mt-4 p-2 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 rounded-lg" onClick={handleStop}>
                  Stop Scrape
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
          </div>
        </main>
      </div>
      );
}
