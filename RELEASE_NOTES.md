# Agent Audio Studio — v0.1.1

Primeira distribuição pública do **Andrew Studio**, um conjunto de ferramentas Python para análise, mixagem, edição e processamento digital de áudio (DSP) com execução local e integração opcional com clientes compatíveis com **Agent Skills**.

## Inclui

- Inspeção de duração, canais, níveis e propriedades de arquivos de áudio.
- Renderização de cadeias de efeitos: filtros, equalização, compressão, distorção, delay, chorus, reverb, transientes e imagem estéreo.
- Mixagem de stems por receitas JSON com ganho, panorâmica e alinhamento.
- Processamento experimental de scratch e coloração harmônica de baixo.
- Saída WAV float32 e relatórios JSON; preservação dos arquivos de origem.
- Operações opcionais de pitch shift e time stretch com Librosa.

## Como usar

O ZIP inclui a pasta completa `andrew-studio/`, com `README.md`, `SKILL.md`, código, exemplos e testes. Requer Python 3.9+, NumPy, SciPy e SoundFile; Librosa é opcional. Não exige conta nem serviço em nuvem para o núcleo de processamento.

```bash
cd andrew-studio
python -m pip install -r requirements.txt
python scripts/studio_dsp.py inspect entrada.wav
```

## Validação e limitações

**10 testes de código e operações com sinais sintéticos passaram** localmente e no GitHub Actions. A suíte não comprova qualidade musical em gravações reais nem integração com toda plataforma de agentes.

Não é uma DAW gráfica completa; não inclui modelos de separação, instrumentos sampleados ou plugins comerciais. Algumas caudas de delay e reverberação não são estendidas automaticamente além da duração da fonte.

O pacote está sob licença **MIT**. O repositório mantém também um arquivo CC0 1.0 na raiz; consulte os arquivos de licença pertinentes.
