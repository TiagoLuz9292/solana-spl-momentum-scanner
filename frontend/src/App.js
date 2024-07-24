import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [tokenAddress, setTokenAddress] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.get(`http://10.103.157.196:8000/check_ohlcv_v2`, {
        params: { pairAddress: tokenAddress },
      });
      setResult(response.data);
    } catch (err) {
      setError('Failed to fetch data. Please check the pair address and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Solana Token Checker</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={tokenAddress}
          onChange={(e) => setTokenAddress(e.target.value)}
          placeholder="Enter Solana token address"
          required
        />
        <button type="submit">Check</button>
      </form>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {result && (
        <div>
          <h2>Results</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;