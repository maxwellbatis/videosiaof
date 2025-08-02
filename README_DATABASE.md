# 🗄️ Banco de Dados - Text to Video AI

## 📁 Estrutura do Projeto

```
Text-To-Video-AI/
├── app.py                    # App principal com integração DB
├── database/                 # Pasta do banco de dados
│   ├── __init__.py          # Módulo Python
│   ├── database.py          # Classe VideoDatabase
│   └── setup_database.py    # Script de configuração
├── prisma/
│   └── schema.prisma        # Schema do banco
├── utility/                  # Utilitários existentes
└── package.json             # Dependências Node.js
```

## 📋 Estrutura do Banco

### Tabelas:

#### `ApiCredentials`
- **id**: ID único (CUID)
- **name**: Nome das credenciais (único)
- **openaiKey**: Chave da API OpenAI
- **groqKey**: Chave da API Groq
- **pexelsKey**: Chave da API Pexels
- **createdAt**: Data de criação
- **updatedAt**: Data de atualização

#### `Video`
- **id**: ID único (CUID)
- **title**: Título do vídeo
- **topic**: Tópico do vídeo
- **script**: Script gerado
- **audioPath**: Caminho do arquivo de áudio
- **videoPath**: Caminho do arquivo de vídeo
- **status**: Status do vídeo (PENDING, PROCESSING, COMPLETED, FAILED)
- **duration**: Duração do vídeo
- **credentialsId**: ID das credenciais usadas
- **createdAt**: Data de criação
- **updatedAt**: Data de atualização

## 🚀 Configuração

### 1. Instalar dependências
```bash
npm install
pip install prisma
```

### 2. Configurar variáveis de ambiente
Crie um arquivo `.env`:
```env
DATABASE_URL="postgresql://postgres:sua_senha@localhost:5432/textoemvideos?schema=public"
```

### 3. Gerar cliente Prisma
```bash
npx prisma generate
```

### 4. Aplicar schema no banco
```bash
npx prisma db push
```

### 5. Configurar credenciais padrão
```bash
python -m database.setup_database
```

## 📖 Como Usar

### Gerar vídeo com banco de dados (padrão)
```bash
python app.py "Fatos sobre o Brasil"
```

### Gerar vídeo sem banco de dados
```bash
python app.py "Fatos sobre o Brasil" --no-db
```

### Usar credenciais específicas
```bash
python app.py "Fatos sobre o Brasil" --credentials "minhas_credenciais"
```

### Listar vídeos
```bash
python -m database.setup_database list
```

## 🔧 Scripts Disponíveis

### `app.py` (Atualizado)
- ✅ Integração automática com banco
- ✅ Busca credenciais automaticamente
- ✅ Salva progresso no banco
- ✅ Rastreia status do vídeo
- ✅ Opção `--no-db` para usar sem banco
- ✅ Opção `--credentials` para credenciais específicas

### `database/database.py`
Classe `VideoDatabase` com métodos:
- `create_credentials()`: Criar credenciais
- `get_credentials()`: Buscar credenciais
- `create_video()`: Criar vídeo
- `update_video_status()`: Atualizar status
- `get_video()`: Buscar vídeo
- `list_videos()`: Listar vídeos
- `delete_video()`: Deletar vídeo

### `database/setup_database.py`
Script de configuração:
- Cria credenciais padrão
- Lista vídeos existentes
- Configuração inicial

## 📊 Status dos Vídeos

- **PENDING**: Aguardando processamento
- **PROCESSING**: Em processamento
- **COMPLETED**: Concluído com sucesso
- **FAILED**: Falhou no processamento

## 🔐 Segurança

- Credenciais são armazenadas de forma segura no banco
- Não há hardcoding de chaves no código
- Suporte a múltiplas credenciais
- Rastreamento completo de uso
- Fallback para variáveis de ambiente se banco falhar

## 🎯 Benefícios

- ✅ Histórico completo de vídeos
- ✅ Rastreamento de status
- ✅ Múltiplas credenciais
- ✅ Segurança das chaves
- ✅ Auditoria de uso
- ✅ Backup automático
- ✅ Compatibilidade com versão sem banco
- ✅ Organização em pastas

## 🔄 Migração

O `app.py` original foi atualizado para incluir integração com banco de dados, mantendo compatibilidade:

- **Com banco**: `python app.py "tópico"`
- **Sem banco**: `python app.py "tópico" --no-db`
- **Credenciais específicas**: `python app.py "tópico" --credentials "nome"` 