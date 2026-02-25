import React, { useEffect, useState } from "react";

export default function App() {

const [trades,setTrades] = useState([]);
const [ativo,setAtivo] = useState("");
const [resultado,setResultado] = useState("ganhar");
const [valor,setValor] = useState(" ");
const [dashboard,setDashboard] = useState({
 total:0,
 ganhos:0,
 perdas:0,
 saldo:0
});

async function carregarTrades(){
 
async function carregarDashboard(){

 const res = await fetch("/api/dashboard");

 const data = await res.json();

 setDashboard(data);

}  

const res = await fetch("/api/trades");

const data = await res.json();

setTrades(data.items || []);

}

useEffect(()=>{

 carregarTrades();

 carregarDashboard();

},[]);


async function criarTrade(){

await fetch("/api/trades",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

ativo,

resultado,

valor:parseFloat(valor)

})

});

setAtivo("");
setValor("");

carregarTrades();

}

return(

<div style={{padding:"20px"}}>

<h1>📊 Análise Pro</h1>

<h2>Nova Trade</h2>

<input
placeholder="Ativo"
value={ativo}
onChange={e=>setAtivo(e.target.value)}
/>

<select

value={resultado}

onChange={e=>setResultado(e.target.value)}

>

<option value="ganhar">Ganhar</option>

<option value="perder">Perder</option>

</select>

<input

placeholder="Valor"

value={valor}

onChange={e=>setValor(e.target.value)}

/>

<button onClick={criarTrade}>

Salvar Trade

</button>

<hr/>

<h2>Trades</h2>

<button onClick={carregarTrades}>

Atualizar

</button>

<ul>

{trades.map(t=>(

<li key={t.id}>

{t.ativo} — {t.resultado} — R$ {t.valor}

</li>

))}

</ul>

</div>

);

}
