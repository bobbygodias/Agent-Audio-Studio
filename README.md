# Agent Audio Studio — Andrew Studio

**Agent Audio Studio** é um projeto de código aberto para **análise, processamento, mixagem e masterização de áudio** por meio de ferramentas Python executadas localmente. Seu núcleo usa processamento digital de sinais (DSP) e pode ser utilizado tanto pela linha de comando quanto por agentes compatíveis com a especificação Agent Skills.

O objetivo é permitir operações de áudio **reproduzíveis e auditáveis**, preservando as gravações originais e oferecendo controle explícito dos parâmetros de processamento. É útil para músicos, produtores, editores e desenvolvedores que desejam experimentar ou automatizar cadeias de efeitos sem depender de um serviço em nuvem.

## Funcionalidades

- Inspeção de arquivos: duração, canais, taxas de amostragem e níveis.
- Equalização e filtros, dinâmica, saturação e diferentes curvas de distorção.
- Delay, reverberação, chorus, imagem estéreo e processamento de transientes.
- Mixagem de pistas (stems) a partir de receitas em JSON, com ganho e alinhamento.
- Efeitos experimentais, incluindo scratch offline e modelagem harmônica de baixo.
- Renderização para WAV float32 com relatório JSON e preservação dos originais.
- Pitch shift e time stretch como funções opcionais, mediante instalação de Librosa.

## Instalação e primeiros passos

Requer **Python 3.9 ou superior**, com **NumPy, SciPy e SoundFile**. O uso de Librosa é opcional. Não é necessário cadastro, chave de API ou serviço externo para o núcleo.

```bash
cd andrew-studio
python -m pip install -r requirements.txt
python scripts/studio_dsp.py inspect entrada.wav
python scripts/studio_dsp.py render entrada.wav assets/chain.example.json saida.wav
```

Para misturar pistas, configure seus caminhos no arquivo [`mix.example.json`](andrew-studio/assets/mix.example.json) e execute:

```bash
python scripts/studio_dsp.py mix assets/mix.example.json mix.wav
```

A documentação completa de parâmetros e execução está no [guia do Andrew Studio](andrew-studio/README.md). O pacote inclui [`SKILL.md`](andrew-studio/SKILL.md) para integração com clientes compatíveis com Agent Skills e exemplos editáveis de receitas.

## Escopo e limitações

A versão **0.1.1** disponibiliza um **núcleo inicial de processamento DSP**, não uma DAW gráfica completa. A integração com transcrição musical e análise perceptiva OUVIDO está **em desenvolvimento** e **não faz parte da release 0.1.1**. Ela não inclui modelos de separação, plugins comerciais, biblioteca de instrumentos ou masterização automática que substitua decisões artísticas. A qualidade do áudio precisa ser avaliada pela escuta e por comparações coerentes; medições isoladas não garantem um resultado musical adequado.

O render produz WAV float32. A versão atual não estende automaticamente as caudas de delay/reverb além do final do arquivo original. Os scripts evitam sobrescrever arquivos de saída já existentes.

## Desenvolvimento e testes

A pasta [`andrew-studio/`](andrew-studio/) contém o código, as receitas, a documentação e testes. Para executar os testes locais:

```bash
python -m unittest discover -s andrew-studio/tests -v
```

A suíte inicial contém **10 testes** para processamento e preservação de arquivos. Isso não comprova a qualidade perceptiva em gravações reais. Consulte o [relatório de testes](andrew-studio/TEST_REPORT.md) para escopo e limitações.

## Licenciamento

O pacote [`andrew-studio/`](andrew-studio/) é disponibilizado sob licença **MIT**. O arquivo `LICENSE` na raiz do repositório contém licença **CC0 1.0**; consulte os arquivos aplicáveis antes de redistribuir.

Desenvolvido por **Bobby Dias e Andrew Vox**, Enterprise. **Nilo** colaborou tecnicamente na implementação dos efeitos e distorções de áudio. Consulte [os colaboradores](CONTRIBUTORS.md) e [o estado da integração](docs/INTEGRATION.md).
