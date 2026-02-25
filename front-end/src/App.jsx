import React, { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState("carregando...");

  useEffect(() => {
    fetch("/api/db")
      .then((r) => r.json())
      .then((data) => setStatus(JSON.stringify(data, null, 2)))
      .catch((e) => setStatus("Erro: " + e.message));
  }, []);

  return (
    <div style={{ padding: 20, fontFamily: "Arial" }}>
      <h2>Sistema para Análise de Gráfico</h2>
      <p>Teste de conexão API:</p>
      <pre style={{ background: "#111", color: "#0f0", padding: 12 }}>
        {status}
      </pre>
    </div>
  );
}
