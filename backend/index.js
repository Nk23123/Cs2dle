const express = require('express');
const { createClient } = require('@supabase/supabase-js');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.json());

// Carregamento do ambiente
const caminhoEsperado = path.resolve(__dirname, '.env');
if (fs.existsSync(caminhoEsperado)) {
    require('dotenv').config({ path: caminhoEsperado });
}

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error("ERRO: Variaveis de ambiente nao configuradas.");
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Rotas
app.post('/importar', async (req, res) => {
    const dadosJogador = req.body;
    const { data, error } = await supabase
        .from('Jogadores')
        .upsert(dadosJogador, { onConflict: 'nome' });

    if (error) return res.status(400).json({ sucesso: false, erro: error.message });
    res.status(201).json({ sucesso: true });
});

app.get('/', (req, res) => {
    res.send('Backend CS2DLE rodando');
});

// Inicializacao
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log("Conexao Supabase OK!");
    console.log(`Servidor rodando na porta ${PORT} - Link de acesso: http://localhost:${PORT}`);
});