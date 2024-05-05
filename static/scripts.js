// backend/static/scripts.js
async function fetchData() {
    try {
      const response = await fetch('/api/visualization');
      const data = await response.json();
      visualizeData(data);
    } catch (error) {
      console.error('Error fetching visualization data:', error);
    }
  }
  
  function visualizeData(data) {
    const chart = document.getElementById('chart');
    // Insert logic to visualize the `data` using your preferred charting library.
    // For example, using Plotly, Chart.js, or any other JavaScript visualization library.
  }
  
  fetchData();
  