import React from 'react';
// 1. 修改引用路徑為相對路徑
import { Card, CardContent, CardHeader } from "../ui/card";
import { Badge } from "../ui/badge";
// 移除沒用到的 Button 引用

import { User, Calendar, FileText, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { zhTW } from 'date-fns/locale';

export default function NoteCard({ note, onClick }) {
  // 定義顏色樣式
  const priorityColors = {
    '一般': 'bg-blue-100 text-blue-800 border-blue-200',
    '重要': 'bg-orange-100 text-orange-800 border-orange-200',
    '緊急': 'bg-red-100 text-red-800 border-red-200'
  };

  const statusColors = {
    'AI已生成': 'bg-blue-100 text-blue-800 border-blue-200',
    '待審核': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    '已確認': 'bg-green-100 text-green-800 border-green-200',
    '已歸檔': 'bg-gray-100 text-gray-800 border-gray-200'
  };

  // 避免日期格式化報錯的安全檢查
  const formatDate = (dateString) => {
    try {
      if (!dateString) return '無日期';
      return format(new Date(dateString), 'yyyy年MM月dd日 HH:mm', { locale: zhTW });
    } catch (e) {
      return '日期格式錯誤';
    }
  };

  return (
    <Card 
      className="border-slate-200 hover:shadow-lg transition-all duration-300 cursor-pointer group bg-white"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* 頭像區域 */}
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-100 to-teal-100 flex items-center justify-center shrink-0">
              <User className="w-6 h-6 text-emerald-700" />
            </div>
            
            {/* 病人資訊 */}
            <div>
              <h3 className="font-semibold text-slate-800 text-lg">{note.patient_name || '未命名病人'}</h3>
              <p className="text-sm text-slate-500">
                {note.patient_id && `ID: ${note.patient_id}`}
                {note.department && ` • ${note.department}`}
              </p>
            </div>
          </div>
          
          {/* 箭頭圖示 */}
          <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-emerald-600 group-hover:translate-x-1 transition-all" />
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* 標籤區域 */}
        <div className="flex flex-wrap gap-2">
          {/* 使用 Optional Chaining (?.) 避免 note.priority 為空時報錯 */}
          <Badge className={(priorityColors[note.priority] || 'bg-gray-100 text-gray-800') + ' border text-xs'}>
            {note.priority || '無優先級'}
          </Badge>
          <Badge className={(statusColors[note.status] || 'bg-gray-100 text-gray-800') + ' border text-xs'}>
            {note.status || '未知狀態'}
          </Badge>
        </div>

        {/* 診斷摘要 */}
        {note.diagnosis && (
          <div className="flex items-start gap-2 text-sm">
            <FileText className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <span className="text-slate-600 line-clamp-2">{note.diagnosis}</span>
          </div>
        )}

        {/* 日期顯示 */}
        <div className="flex items-center gap-2 text-xs text-slate-500 pt-2 border-t border-slate-100">
          <Calendar className="w-3.5 h-3.5" />
          <span>
            {formatDate(note.created_date)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}