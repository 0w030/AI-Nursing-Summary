import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// 1. 引入 React Query 的核心元件
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import Dashboard from './pages/Dashboard';

// 2. 建立一個 Client 實例 (這是引擎)
const queryClient = new QueryClient();

function App() {
  return (
    // 3. 把整個 App 包在 Provider 裡面，讓所有頁面都能用
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;

