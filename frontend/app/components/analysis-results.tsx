import type { QueryCell, QueryResponse, QueryRow } from "../lib/query-api";

type AnalysisResultsProps = {
  analysis: QueryResponse | null;
  isLoading: boolean;
};

export function AnalysisResults({ analysis, isLoading }: AnalysisResultsProps) {
  if (!analysis) {
    return (
      <section className="analysis-output" aria-live="polite" aria-labelledby="analysis-title">
        <div className="analysis-heading">
          <div>
            <p className="eyebrow">Analiz çıktısı</p>
            <h2 id="analysis-title">
              {isLoading ? "Soru analiz ediliyor..." : "Henüz bir analiz yok"}
            </h2>
          </div>
        </div>
        <article className="result-panel">
          <p className="empty-analysis">
            {isLoading
              ? "Gemini SQL üretiyor ve PostgreSQL sonucu bekleniyor."
              : "Bir soru yazıp Analiz Et’e basın. SQL, tablo ve açıklama burada görünecek."}
          </p>
        </article>
      </section>
    );
  }

  const columns = analysis.rows[0] ? Object.keys(analysis.rows[0]) : [];

  return (
    <section className="analysis-output" aria-live="polite" aria-busy={isLoading} aria-labelledby="analysis-title">
      <div className="analysis-heading">
        <div>
          <p className="eyebrow">Analiz çıktısı</p>
          <h2 id="analysis-title">{analysis.question}</h2>
        </div>
        <span className="result-badge">{isLoading ? "Güncelleniyor" : "API sonucu"}</span>
      </div>

      <article className="result-panel sql-panel">
        <div className="panel-header">
          <div>
            <p className="panel-label">Generated SQL</p>
            <h3>Oluşturulan sorgu</h3>
          </div>
          <span className="read-only">Read only</span>
        </div>
        <pre><code>{analysis.sql}</code></pre>
      </article>

      <div className="result-grid">
        <article className="result-panel table-panel">
          <div className="panel-header">
            <div>
              <p className="panel-label">Query Result</p>
              <h3>Sorgu sonucu</h3>
            </div>
            <span className="row-count">{analysis.rows.length} satır</span>
          </div>

          <div className="table-wrap">
            {columns.length === 0 ? (
              <p className="empty-analysis">Bu sorgu için satır dönmedi.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    {columns.map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {analysis.rows.map((row, index) => (
                    <tr key={rowKey(row, index)}>
                      {columns.map((column) => (
                        <td key={column}>{formatCell(row[column])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </article>

        <article className="result-panel explanation-panel">
          <div className="panel-header">
            <div>
              <p className="panel-label">AI Explanation</p>
              <h3>Kısa yorum</h3>
            </div>
          </div>
          <p>{analysis.explanation}</p>
          <div className="explanation-note">
            <span className="note-mark" aria-hidden="true">i</span>
            <span>Bu yorum, dönen satırlara dayanarak üretildi.</span>
          </div>
        </article>
      </div>
    </section>
  );
}

function rowKey(row: QueryRow, index: number): string {
  return `${index}:${Object.values(row).map(formatCell).join("|")}`;
}

function formatCell(value: QueryCell | undefined): string {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}
