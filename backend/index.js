const express = require('express');
const { createClient } = require('@supabase/supabase-js');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.json());

// 1. Carregamento do Ambiente (.env)
const caminhoEnv = path.resolve(__dirname, '.env');
if (fs.existsSync(caminhoEnv)) {
    require('dotenv').config({ path: caminhoEnv });
}

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

console.log("DEBUG - URL USADA:", supabaseUrl);
console.log("DEBUG - KEY USADA:", supabaseKey ? "CHAVE PRESENTE" : "CHAVE AUSENTE");

if (!supabaseUrl || !supabaseKey) {
    console.error("❌ ERRO: Verifique seu arquivo .env. As chaves do Supabase sumiram.");
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// 2. Rota de Importação
app.post('/importar', async (req, res) => {
    console.log("-----------------------------------------");
    console.log("📥 Dados recebidos do Bot:", req.body);

    try {
        const { nome, funcao, idade, status, pais_nome, link } = req.body;

        // --- DIAGNÓSTICO DE CONEXÃO ---
        // Vamos listar o que o código "enxerga" na tabela Paises
        const { data: listaPaises } = await supabase.from('Paises').select('id, nome');
        console.log(`📊 O banco de dados tem ${listaPaises ? listaPaises.length : 0} países cadastrados.`);
        
        // --- BUSCA DO PAÍS (IGNORANDO MAIÚSCULAS/MINÚSCULAS) ---
        // Usamos .ilike para que 'brazil', 'Brazil' ou 'BRAZIL' funcionem.
        const { data: paisData, error: erroBusca } = await supabase
            .from('Paises')
            .select('id')
            .ilike('nome', pais_nome.trim())
            .maybeSingle();

        if (erroBusca) {
            console.error("❌ Erro ao consultar tabela Paises:", erroBusca.message);
        }

        const idEncontrado = paisData ? paisData.id : null;
        console.log(`🌍 Busca por "${pais_nome}": ID ENCONTRADO = ${idEncontrado}`);

        // --- PREPARAÇÃO DO OBJETO JOGADOR ---
        const objetoJogador = {
            nome: nome,
            funcao: funcao,
            idade: parseInt(idade) || 0,
            Status: status, // Se na sua tabela a coluna for 'Status' com S maiúsculo
            pais_id: idEncontrado,
            link: link
        };

        console.log("📤 Tentando salvar no Supabase:", objetoJogador);

        // --- SALVAMENTO (UPSERT) ---
        const { error: erroUpsert } = await supabase
            .from('Jogadores')
            .upsert(objetoJogador, { onConflict: 'nome' });

        if (erroUpsert) {
            console.error("❌ Erro ao salvar Jogador:", erroUpsert.message);
            return res.status(400).json({ sucesso: false, erro: erroUpsert.message });
        }

        console.log("✅ JOGADOR PROCESSADO COM SUCESSO!");
        res.status(201).json({ sucesso: true, id_pais: idEncontrado });

    } catch (error) {
        console.error("💥 Erro crítico no servidor:", error.message);
        res.status(500).json({ sucesso: false, erro: error.message });
    }
});

// 3. Inicialização
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log("✅ Servidor Node.js Rodando!");
    console.log(`🔗 Endpoint: http://localhost:${PORT}/importar`);
});