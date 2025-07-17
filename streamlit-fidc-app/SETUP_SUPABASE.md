# FIDC Calculator - Energisa

## 🚀 Setup do Supabase Storage (Recomendado)

Para melhor performance e gestão de arquivos, configure o Supabase Storage:

### 1. Criar Conta no Supabase
1. Acesse [supabase.com](https://supabase.com)
2. Crie uma conta gratuita
3. Crie um novo projeto

### 2. Configurar Storage
1. No painel do Supabase, vá para **Storage**
2. Crie um novo bucket chamado `fidc-files`
3. Configure o bucket como **público** para permitir downloads
4. Nas configurações do bucket, defina as seguintes políticas:
   ```sql
   -- Política para INSERT (upload)
   CREATE POLICY "Enable insert for authenticated users only" ON storage.objects
   FOR INSERT WITH CHECK (bucket_id = 'fidc-files');
   
   -- Política para SELECT (download público)
   CREATE POLICY "Enable select for all users" ON storage.objects
   FOR SELECT USING (bucket_id = 'fidc-files');
   ```

### 3. Obter Credenciais
1. Vá para **Settings** > **API**
2. Copie:
   - **Project URL**
   - **Project API Keys** > **anon** > **public**

### 4. Configurar Aplicação
1. Copie o arquivo `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`
2. Preencha com suas credenciais:
   ```toml
   [secrets]
   SUPABASE_URL = "https://seu-projeto.supabase.co"
   SUPABASE_ANON_KEY = "sua-chave-anonima-aqui"
   ```

### 5. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 6. Executar Aplicação
```bash
streamlit run app.py
```

## 🔧 Funcionalidades

### ✅ Implementado com Supabase Storage
- ✅ Download consolidado Excel (upload automático para storage)
- ✅ URLs públicas para compartilhamento
- ✅ Fallback para download local em caso de erro

### ⚠️ Modo Fallback (sem Supabase)
Se o Supabase não estiver configurado, a aplicação funcionará normalmente usando downloads locais diretos.

## 🎨 Interface

- **Cores Energisa**: Verde #00A859 e #28C76F
- **Spinners**: Feedback visual durante processamento
- **Interface Minimalista**: Focada no workflow essencial
- **Preview de Dados**: Apenas 30 primeiras linhas para performance

## 📊 Workflow

1. **Configurações**: IGP-M e parâmetros de correção
2. **Distribuição por Aging**: Upload e análise de vencimentos
3. **Correção Monetária**: Cálculo automatizado
4. **Download**: Excel com dados corrigidos via Supabase Storage

## 🏗️ Arquitetura

```
app.py                  # Interface principal
├── utils/
│   ├── parametros_correcao.py    # Configurações IGP-M
│   ├── analisador_bases.py       # Análise de arquivos
│   ├── mapeador_campos.py        # Padronização
│   ├── calculador_aging.py       # Distribuição aging
│   ├── calculador_correcao.py    # Correção monetária
│   └── exportador_resultados.py  # Geração Excel
└── .streamlit/
    └── secrets.toml              # Credenciais Supabase
```

## 💡 Benefícios do Supabase Storage

- **Performance**: Não sobrecarrega memória da aplicação
- **Compartilhamento**: URLs públicas para download
- **Escalabilidade**: Suporte a arquivos grandes
- **Confiabilidade**: Storage redundante e backups automáticos
