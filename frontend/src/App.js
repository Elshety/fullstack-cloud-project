import React, { useState, useEffect } from 'react';

function App() {
  const [data, setData] = useState('');

  useEffect(() => {
    fetch(process.env.REACT_APP_API_URL || 'http://localhost:3001/api')
      .then(res => res.json())
      .then(data => setData(data.message))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <p>Backend Response: {data}</p>
      </header>
    </div>
  );
}

export default App;