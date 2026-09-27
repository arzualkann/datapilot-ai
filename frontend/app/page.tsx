import { QueryWorkspace } from "./components/query-workspace";

export default function Home() {
  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="header-content">
          <div className="brand" aria-label="DataPilot AI">
            <span className="brand-mark" aria-hidden="true">DP</span>
            <span>DataPilot AI</span>
          </div>
          <span className="workspace-badge">Demo Workspace</span>
        </div>
      </header>

      <div className="page-content">
        <section className="page-intro" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">AI SQL Agent</p>
            <h1 id="page-title">DataPilot AI</h1>
            <p>Verilerinize doğal dille sorun, SQL&apos;i AI oluştursun.</p>
          </div>
          <div className="data-source">
            <span className="source-dot" aria-hidden="true" />
            <div>
              <strong>Demo e-commerce verisi</strong>
              <span>customers, products, orders, order_items</span>
            </div>
          </div>
        </section>

        <QueryWorkspace />
      </div>
    </main>
  );
}
