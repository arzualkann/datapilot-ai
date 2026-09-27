"use client";

import { type FormEvent, useState } from "react";

import { AnalysisResults } from "./analysis-results";
import { analyzeQuestion, type QueryResponse } from "../lib/query-api";

export function QueryWorkspace() {
  const [question, setQuestion] = useState("");
  const [analysis, setAnalysis] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submittedQuestion = question.trim();

    if (!submittedQuestion) {
      setErrorMessage("Analiz etmek için önce bir soru yazın.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await analyzeQuestion(submittedQuestion);
      setAnalysis(response);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Analiz sırasında beklenmeyen bir hata oluştu.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="query-workspace" aria-label="SQL analiz alanı">
      <form className="query-card" onSubmit={handleSubmit}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Yeni analiz</p>
            <h2>Veritabanınıza bir soru sorun</h2>
          </div>
          <span className="mock-badge">Canlı API</span>
        </div>

        <label className="sr-only" htmlFor="database-question">
          Veritabanı sorusu
        </label>
        <textarea
          id="database-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Örn: Son 30 günde en çok satan 5 ürünü göster."
          rows={4}
          disabled={isLoading}
        />

        <div className="query-actions">
          <p>Gönderilen soru, development API&apos;sine analiz için iletilir.</p>
          <button type="submit" disabled={isLoading} aria-busy={isLoading}>
            {isLoading ? "Analiz ediliyor..." : "Analiz Et"}
          </button>
        </div>

        {errorMessage ? <p className="query-error" role="alert">{errorMessage}</p> : null}
      </form>

      <AnalysisResults analysis={analysis} isLoading={isLoading} />
    </section>
  );
}
