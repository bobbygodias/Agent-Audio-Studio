# Andrew Studio — Agent Audio Studio

**Andrew Studio** é um conjunto aberto de ferramentas para **análise, edição e processamento de áudio** com Python. O pacote fornece um núcleo de DSP para tratamento de arquivos locais, mixagem de pistas e montagem de cadeias reproduzíveis de efeitos. Pode ser utilizado por linha de comando ou como habilidade de um agente compatível com a especificação Agent Skills.

## Funcionalidades

- Inspeção de formato, duração, canais, picos e níveis de arquivos de áudio.
- Renderização de cadeias de processamento com filtros, equalização, compressão, saturação e distorções.
- Delay, chorus, reverb, ajuste de imagem estéreo e processamento de transientes.
- Processamento experimental de scratch e coloração harmônica de baixo.
- Mixagem de stems com ajustes de ganho, panorâmica e alinhamento, a partir de receita JSON.
- Exportação em WAV float32, preservando os arquivos originais e produzindo relatórios JSON.
- Pitch shift e time stretch opcionais com Librosa, quando a dependência estiver instalada.

## Requisitos

Python 3.9 ou superior, NumPy, SciPy e SoundFile. O processamento opcional de afinação/tempo usa Librosa. É uma ferramenta de processamento **offline** e não exige serviço externo ou chave de API. A versão inicial não é uma estação de trabalho musical com interface gráfica nem substitui uma DAW completa.

Instale as dependências dentro da pasta `andrew-studio`:

```bash
python -m pip install -r requirements.txt
# opcional, se for usar pitch/time:
python -m pip install -r requirements-optional.txt
```

## Exemplos de uso

```bash
python scripts/studio_dsp.py inspect entrada.wav
python scripts/studio_dsp.py render entrada.wav assets/chain.example.json saida.wav
python scripts/studio_dsp.py mix assets/mix.example.json mix.wav
```

O exemplo de mix usa caminhos de stems relativos ao arquivo `assets/mix.example.json`; substitua-os pelos seus arquivos. O processamento não sobrescreve entradas ou saídas existentes, e as caudas de reverberação/delay não são estendidas automaticamente após a duração da entrada.

## Uso por agentes

O arquivo [`SKILL.md`](SKILL.md) descreve a execução orientada por agentes e a seleção responsável de cadeias DSP. Copie a pasta completa `andrew-studio/` para o diretório de habilidades do cliente compatível com Agent Skills. O nome da pasta deve corresponder ao `name` do manifesto. A disponibilidade do ambiente de execução e das dependências varia conforme o cliente.

## Limitações e segurança

Os resultados exigem escuta crítica e comparação em níveis equivalentes; métricas isoladas não avaliam qualidade musical. O pacote não inclui modelos de separação, bibliotecas comerciais, instrumentos sampleados ou plugins proprietários. Processamentos de efeitos e masterização não garantem adequação para qualquer material. Evite sobrescrever gravações originais e faça cópias de segurança.

O código e os testes acompanham o projeto. Consulte `TEST_REPORT.md` para os testes históricos e execute `python -m unittest discover -s tests -v` para verificar os testes de lógica/arquivos no ambiente local.

**Licença:** MIT, conforme `LICENSE`. Projeto de Bobby Dias e Andrew Vox, Enterprise.
