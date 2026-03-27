const express = require('express');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const app = express();
app.use(express.json());

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

// Rota inicial
app.get('/', (req, res) => {
  res.send('API de CS:GO rodando 🚀');
});

// Rota para o Python enviar os dados
app.post('/importar', async (req, res) => {
  const dadosJogador = req.body;

  const { data, error } = await supabase
    .from('Jogadores')
    .upsert(dadosJogador, { onConflict: 'nome' });

  if (error) {
    console.error("Erro no Supabase:", error);
    return res.status(400).json({ erro: error.message });
  }

  res.status(201).json({ mensagem: "Jogador sincronizado!", data });
});

// usar porta do .env
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});