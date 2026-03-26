const express = require('express');
const { createClient } = require('@supabase/supabase-js');

const app = express();
app.use(express.json());

const supabaseUrl = 'https://uldoiuoutbhnmnhuetzt.supabase.co';
const supabaseKey = 'sb_publishable_tmmu44SisLvv6oeGVryhnw_sG-B8i0U';
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
    .upsert(dadosJogador, { onConflict: 'nome' }); // 'nome' deve ser uma coluna única no Supabase

  if (error) {
    console.error("Erro no Supabase:", error);
    return res.status(400).json({ erro: error.message });
  }

  res.status(201).json({ mensagem: "Jogador sincronizado!", data });
});

// LISTA SEMPRE NO FINAL
app.listen(3000, () => {
  console.log('Servidor rodando em http://localhost:3000');
});