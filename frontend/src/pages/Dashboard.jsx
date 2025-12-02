import React from 'react';
import axios from 'axios'; // 新增：用來連後端
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, FileText, CheckCircle2, Clock, AlertCircle, FileUp } from 'lucide-react';

// 修改 import 路徑 (假設你的檔案結構是標準的 ../components)
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import NoteCard from '../components/nursing/NoteCard';

export default function Dashboard() {
  // 設定後端 API 網址
  // 開發時通常是 http://localhost:5000/api/notes
  // 上線到 Railway 後要換成 Railway 的網址
  const API_URL = 'http://localhost:5000/api/notes';

  const { data: notes = [], isLoading, isError } = useQuery({
    queryKey: ['nursing-notes'],
    queryFn: async () => {
      // 這裡改成用 axios 去跟你的 Python 後端要資料
      const response = await axios.get(API_URL);
      return response.data;
    }
  });

  // 統計數據邏輯 (保持不變)
  const stats = {
    total: notes.length,
    completed: notes.filter(n => n.status === '已完成').length,
    inProgress: notes.filter(n => n.status === '進行中').length,
    urgent: notes.filter(n => n.priority === '緊急').length
  };

  const recentNotes = notes.slice(0, 6);

  if (isError) {
    return <div className="p-8 text-red-500">無法連接到後端，請確認 Python 後端是否已啟動 (localhost:5000)。</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-emerald-50/30 to-teal-50/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 標題區 */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            AI護理摘要系統
          </h1>
          <p className="text-slate-600">智能生成結構化護理記錄，提升護理效率</p>
        </div>

        {/* 統計卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600">總記錄數</CardTitle>
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats.total}</div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600">已完成</CardTitle>
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats.completed}</div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600">進行中</CardTitle>
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats.inProgress}</div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600">緊急案例</CardTitle>
                <AlertCircle className="w-5 h-5 text-red-600" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats.urgent}</div>
            </CardContent>
          </Card>
        </div>

        {/* 快速操作區 - 修改連結路徑 */}
        <div className="mb-8 flex flex-wrap gap-4">
          <Link to="/create">
            <Button 
              size="lg" 
              className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 shadow-lg shadow-emerald-500/30 text-white"
            >
              <Plus className="w-5 h-5 mr-2" />
              創建新的護理摘要
            </Button>
          </Link>
          <Link to="/import">
            <Button 
              size="lg" 
              variant="outline"
              className="bg-white text-slate-700 hover:bg-slate-50 border-slate-200 shadow-sm"
            >
              <FileUp className="w-5 h-5 mr-2" />
              匯入CSV資料
            </Button>
          </Link>
        </div>

        {/* 最近記錄區 */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-slate-900">最近記錄</h2>
            <Link to="/history">
              <Button variant="ghost" className="text-emerald-700 hover:text-emerald-800 hover:bg-emerald-50">
                查看全部 →
              </Button>
            </Link>
          </div>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
              <p className="text-slate-600 mt-4">載入中...</p>
            </div>
          ) : recentNotes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recentNotes.map((note) => (
                <Link key={note.id} to={`/view/${note.id}`}>
                  <NoteCard note={note} />
                </Link>
              ))}
            </div>
          ) : (
            <Card className="border-slate-200 shadow-sm">
              <CardContent className="py-12 text-center">
                <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-600 mb-4">還沒有任何護理記錄</p>
                <Link to="/create">
                  <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">
                    創建第一筆記錄
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}