import { useState, useEffect } from 'react';
import axios from 'axios';
import { Download, RefreshCw, BarChart3, Search, Brain, ShieldCheck, Key, Settings, AlertCircle, PlayCircle } from 'lucide-react';
import { encryptKey, decryptKey } from './utils/crypto';

interface Stock {
  ticker: string;
  name: string;
  market: string;
}

const API_BASE = '/api'; // Modified for Vercel deployment

interface AnalysisResult {
  opinion: string;
  opinion_score: string;
  target_price: string;
  high_52w: string;
  low_52w: string;
  current_price: string;
  sector: string;
  loading?: boolean;
  ai_loading?: boolean;
  strategic_recommendation?: string;
  strategic_solution?: string;
}

function App() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [exporting, setExporting] = useState(false);
  const [batchAnalyzing, setBatchAnalyzing] = useState(false);
  const [selectedMarket, setSelectedMarket] = useState<'전체' | 'KOSPI' | 'KOSDAQ'>('전체');
  const [analysis, setAnalysis] = useState<Record<string, AnalysisResult>>({});

  const [apiKey, setApiKey] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

  const fetchStocks = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/stocks`);
      setStocks(response.data);
    } catch (error) {
      console.error('주식 리스트 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStocks();
    const savedKey = localStorage.getItem('gemini_api_key');
    if (savedKey) {
      setApiKey(decryptKey(savedKey));
    }
  }, []);

  const handleSaveKey = () => {
    if (apiKey) {
      localStorage.setItem('gemini_api_key', encryptKey(apiKey));
      setShowSettings(false);
    }
  };

  const handleTestKey = async () => {
    setTestStatus('testing');
    try {
      const response = await axios.get(`${API_BASE}/gemini-test`, {
        headers: { 'X-Gemini-API-Key': apiKey }
      });
      if (response.data.success) {
        setTestStatus('success');
      } else {
        setTestStatus('error');
      }
    } catch (error) {
      setTestStatus('error');
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await axios.post(`${API_BASE}/export`, {
        stocks: stocks,
        analysis: analysis
      }, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `주식_분석_결과_${new Date().toISOString().slice(0, 10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('내보내기 실패:', error);
    } finally {
      setExporting(false);
    }
  };

  const handleAnalyze = async (ticker: string) => {
    setAnalysis(prev => ({ ...prev, [ticker]: { ...prev[ticker], loading: true } as any }));
    try {
      const response = await axios.get(`${API_BASE}/trading-analysis/${ticker}`);
      setAnalysis(prev => ({ ...prev, [ticker]: { ...response.data, loading: false } }));
    } catch (error) {
      console.error('분석 실패:', error);
      setAnalysis(prev => ({ ...prev, [ticker]: { loading: false } as any }));
    }
  };

  const handleBatchAnalyze = async () => {
    setBatchAnalyzing(true);
    const topStocks = filteredStocks.slice(0, 20); // API 과부하 방지를 위해 상위 20개만 시범 실시
    for (const stock of topStocks) {
      if (!analysis[stock.ticker]?.current_price || analysis[stock.ticker]?.current_price === 'N/A') {
        await handleAnalyze(stock.ticker);
        await new Promise(r => setTimeout(r, 500)); // 매너 타임
      }
    }
    setBatchAnalyzing(false);
  };

  const handleAIAnalyze = async (ticker: string) => {
    if (!apiKey) {
      setShowSettings(true);
      return;
    }
    const stockData = analysis[ticker];
    if (!stockData || !stockData.current_price || stockData.current_price === 'N/A') {
      await handleAnalyze(ticker);
    }

    setAnalysis(prev => ({ ...prev, [ticker]: { ...prev[ticker], ai_loading: true } }));
    try {
      const currentData = analysis[ticker] || {};
      const response = await axios.post(`${API_BASE}/gemini-analyze/${ticker}`, {
        ...currentData,
        name: stocks.find(s => s.ticker === ticker)?.name
      }, {
        headers: { 'X-Gemini-API-Key': apiKey }
      });
      setAnalysis(prev => ({ ...prev, [ticker]: { ...prev[ticker], ...response.data, ai_loading: false } }));
    } catch (error) {
      console.error('AI 분석 실패:', error);
      setAnalysis(prev => ({ ...prev, [ticker]: { ...prev[ticker], ai_loading: false } }));
    }
  };

  const filteredStocks = stocks.filter(stock => {
    const matchesSearch = stock.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.ticker.includes(searchTerm);
    const mkt = selectedMarket === '전체' ? 'ALL' : selectedMarket;
    const matchesMarket = mkt === 'ALL' || stock.market === mkt;
    return matchesSearch && matchesMarket;
  });

  return (
    <div className="app-container" style={{ maxWidth: '1400px' }}>
      <header className="header">
        <div className="title-group">
          <h1>주식 대시보드 <span className="premium-tag">PREMIUM AI</span></h1>
          <p>KOSPI & KOSDAQ 실시간 데이터 분석 시스템</p>
        </div>
        <div className="actions">
          <button className="btn btn-icon" onClick={() => setShowSettings(!showSettings)}>
            <Settings size={20} />
          </button>
          <button className="btn btn-outline" onClick={fetchStocks} disabled={loading}>
            <RefreshCw className={loading ? 'animate-spin' : ''} size={20} />
            새로고침
          </button>
          <button className="btn btn-primary" onClick={handleExport} disabled={exporting || stocks.length === 0}>
            <Download size={20} />
            {exporting ? '내보내는 중...' : 'Excel 저장'}
          </button>
        </div>
      </header>

      {showSettings && (
        <div className="card settings-card animate-slide-down">
          <h3><Key size={18} /> Gemini AI 설정</h3>
          <div className="input-group">
            <input
              type="password"
              placeholder="Gemini API Key를 입력하세요"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <button className="btn btn-secondary" onClick={handleTestKey} disabled={testStatus === 'testing'}>
              {testStatus === 'testing' ? '테스트 중...' : '연결 테스트'}
            </button>
            <button className="btn btn-primary" onClick={handleSaveKey}>암호화 저장</button>
          </div>
          {testStatus === 'success' && <p className="status-msg success"><ShieldCheck size={14} /> 연결 성공!</p>}
          {testStatus === 'error' && <p className="status-msg error"><AlertCircle size={14} /> 연결 실패. 키를 확인하세요.</p>}
        </div>
      )}

      <div className="card">
        <div className="card-header-actions">
          <div className="tabs">
            {['전체', 'KOSPI', 'KOSDAQ'].map(m => (
              <button
                key={m}
                onClick={() => setSelectedMarket(m as any)}
                className={`tab-btn ${selectedMarket === m ? 'active' : ''}`}
              >
                {m}
              </button>
            ))}
          </div>
          <button className="btn btn-batch" onClick={handleBatchAnalyze} disabled={batchAnalyzing || loading}>
            <PlayCircle size={18} />
            {batchAnalyzing ? '일괄 분석 중...' : '전체 일괄 분석 (상위 20개)'}
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1.5rem', gap: '1rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} size={18} />
            <input
              type="text"
              placeholder="종목명 또는 티커로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          <div className="count-label">
            {filteredStocks.length}개 종목 리스팅됨
          </div>
        </div>

        <div className="table-container">
          {loading ? (
            <div className="empty-state">
              <div className="loading-spinner"></div>
              <p>최신 마켓 데이터를 가져오고 있습니다...</p>
            </div>
          ) : filteredStocks.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th style={{ minWidth: '100px' }}>종목코드</th>
                  <th style={{ minWidth: '150px' }}>종목명</th>
                  <th>시장</th>
                  <th>현재가</th>
                  <th>투자의견</th>
                  <th>목표주가</th>
                  <th>52주 최고/최저</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {filteredStocks.slice(0, 100).map(stock => (
                  <>
                    <tr key={stock.ticker}>
                      <td className="ticker-cell">{stock.ticker}</td>
                      <td>{stock.name}</td>
                      <td>
                        <span className={`badge badge-${stock.market.toLowerCase()}`}>
                          {stock.market}
                        </span>
                      </td>
                      <td className="price-cell">
                        {analysis[stock.ticker]?.current_price || '-'}
                      </td>
                      <td className="opinion-cell">
                        {analysis[stock.ticker]?.opinion && analysis[stock.ticker]?.opinion !== 'N/A'
                          ? `${analysis[stock.ticker].opinion} (${analysis[stock.ticker].opinion_score})`
                          : '-'}
                      </td>
                      <td className="target-price-cell">
                        {analysis[stock.ticker]?.target_price || '-'}
                      </td>
                      <td className="range-cell">
                        {analysis[stock.ticker] && analysis[stock.ticker].low_52w !== 'N/A'
                          ? `${analysis[stock.ticker].low_52w} ~ ${analysis[stock.ticker].high_52w}`
                          : '-'}
                      </td>
                      <td>
                        <div className="cell-actions">
                          <button
                            className="btn btn-sm btn-outline"
                            onClick={() => handleAnalyze(stock.ticker)}
                            disabled={analysis[stock.ticker]?.loading}
                          >
                            {analysis[stock.ticker]?.loading ? <RefreshCw className="animate-spin" size={14} /> : '데이터 분석'}
                          </button>
                          <button
                            className="btn btn-sm btn-ai"
                            onClick={() => handleAIAnalyze(stock.ticker)}
                            disabled={analysis[stock.ticker]?.ai_loading}
                          >
                            {analysis[stock.ticker]?.ai_loading ? <RefreshCw className="animate-spin" size={14} /> : <Brain size={14} />}
                            AI 전략
                          </button>
                        </div>
                      </td>
                    </tr>
                    {analysis[stock.ticker]?.strategic_recommendation && (
                      <tr className="ai-row">
                        <td colSpan={8}>
                          <div className="ai-report animate-fade-in">
                            <div className="report-item">
                              <strong>💡 AI 전략 제안:</strong> {analysis[stock.ticker].strategic_recommendation}
                            </div>
                            <div className="report-item">
                              <strong>🛠 전략 솔루션:</strong> {analysis[stock.ticker].strategic_solution}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <BarChart3 size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
              <p>검색 결과가 없습니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
