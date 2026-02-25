import React, { useEffect, useState } from "react";

export default function App() {
  const [trades, setTrades] = useState([]);
  const [ativo, setAtivo] = useState("");
  const [resultado, setResultado] = useState("ganhar");
  const [valor, setValor] = useState("");

  const [dashboard, setDashboard] = useState({
    total: 0,
    ganhos: 0,
    perdas: 0,
    saldo: 0,
  });

  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  const API = "http://72.61.57.15:8000";

  async function carregarTrades() {
    try {
      setErro("");
      const res = await fetch(`${API}/trades`);

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Falha ao carregar trades (${res.status}): ${txt}`);
      }

      const data = await res.json();
      setTrades(Array.isArray(data?.items) ? data.items : []);
    } catch (e) {
      setErro(String(e.message || e));
      setTrades([]);
    }
  }

  async function carregarDashboard() {
    try {
      setErro("");
      const res = await fetch(`${API}/dashboard`);

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Falha ao carregar dashboard (${res.status}): ${txt}`);
      }

      const data = await res.json();

      // garante formato
      setDashboard({
        total: Number(data?.total ?? 0),
        ganhos: Number(data?.ganhos ?? 0),
        perdas: Number(data?.perdas ?? 0),
        saldo: Number(data?.saldo ?? 0),
      });
    } catch (e) {
      setErro(String(e.message || e));
      setDashboard({ total: 0, ganhos: 0, perdas: 0, saldo: 0 });
    }
  }

  async function atualizarTudo() {
    setLoading(true);
    await Promise.all([carregarTrades(), carregarDashboard()]);
    setLoading(false);
  }

  async function criarTrade() {
    try {
      setErro("");

      if (!ativo.trim()) {
        setErro("Preencha o campo Ativo.");
        return;
      }

      const valorNum = Number(valor);
      if (!Number.isFinite(valorNum) || valorNum <= 0) {
        setErro("Digite um valor válido (ex: 10).");
        return;
      }

      const res = await fetch(`${API}/trades`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ativo: ativo.trim(),
          resultado,
          valor: valorNum,
        }),
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Falha ao salvar trade (${res.status}): ${txt}`);
      }

      // limpa inputs
      setAtivo("");
      setValor("");
      setResultado("ganhar");

      // atualiza lista + dashboard
      await atualizarTudo();
    } catch (e) {
      setErro(String(e.message || e));
    }
  }

  useEffect(() => {
    atualizarTudo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif" }}>
      <h1>📊 Análise Pro</h1>

      <div style={{ marginBottom: 15 }}>
        <h2>Dashboard</h2>
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
          <div><strong>Total:</strong> {dashboard.total}</div>
          <div><strong>Ganhos:</strong> {dashboard.ganhos}</div>
          <div><strong>Perdas:</strong> {dashboard.perdas}</div>
          <div><strong>Saldo:</strong> {dashboard.saldo}</div>
        </div>
      </div>

      <hr />

      <h2>Nova Trade</h2>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <input
          placeholder="Ativo (ex: EURUSD)"
          value={ativo}
          onChange={(e) => setAtivo(e.target.value)}
          style={{ padding: 8, minWidth: 180 }}
        />

        <select
          value={resultado}
          onChange={(e) => setResultado(e.target.value)}
          style={{ padding: 8 }}
        >
          <option value="ganhar">Ganhar</option>
          <option value="perder">Perder</option>
        </select>

        <input
          placeholder="Valor (ex: 10)"
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          style={{ padding: 8, width: 140 }}
        />

        <button
          onClick={criarTrade}
          style={{ padding: "8px 14px", cursor: "pointer" }}
          disabled={loading}
        >
          {loading ? "Salvando..." : "Salvar Trade"}
        </button>
      </div>

      {erro ? (
        <div style={{ marginTop: 10, color: "crimson" }}>
          <strong>Erro:</strong> {erro}
        </div>
      ) : null}

      <hr />

      <h2>Trades</h2>

      <button
        onClick={atualizarTudo}
        style={{ padding: "8px 14px", cursor: "pointer" }}
        disabled={loading}
      >
        {loading ? "Atualizando..." : "Atualizar"}
      </button>

      <ul style={{ marginTop: 10 }}>
        {trades.length === 0 ? (
          <li>Nenhuma trade cadastrada.</li>
        ) : (
          trades.map((t) => (
            <li key={t.id}>
              {t.ativo} — {t.resultado} — R$ {t.valor}
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
