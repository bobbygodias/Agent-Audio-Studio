# Integração do Agent Audio Studio — desenvolvimento

A visão de desenvolvimento é uma **única skill** modular de áudio, com execução local e sem obrigação de API remota ou servidor MCP. A release `v0.1.1` existente inclui **somente o núcleo de DSP**, não o Studio completo.

## Componentes previstos

1. **Processamento, efeitos, distorções e mixagem (DSP)** — já incluídos na v0.1.1. A implementação dos efeitos e distorções contou com colaboração técnica de Nilo (Codex).
2. **Transcrição musical** — módulo experimental para gerar rascunhos de letra cantada com reconhecimento local opcional e revisão; ainda não integrado à release.
3. **OUVIDO** — módulo experimental para análise perceptual, intenção artística, saliência, letra e áudio em conjunto; ainda não integrado à release.

Os módulos em desenvolvimento têm dependências e limitações independentes; partes de reconhecimento podem exigir o download prévio de modelos. O desenvolvimento deve preservar os arquivos originais, a intenção artística e o controle humano sobre decisões criativas.

## Estado e critérios de integração

- O código publicado na `main` e na release v0.1.1 permanece o núcleo DSP. **Não anunciar os módulos experimentais como já disponíveis na release.**
- Antes de integrar os novos componentes à distribuição pública, confirmar as licenças aplicáveis, especialmente a do OUVIDO, cuja cópia de desenvolvimento recebida não inclui um arquivo de licença próprio.
- Verificar compatibilidade de ambientes e dependências; executar os testes de cada módulo e testar, separadamente, fluxos reais de transcrição e análise musical.
- Definir contratos de entrada e saída comuns, reduzir duplicação entre mecanismos de transcrição e fornecer um único manifesto de skill.
- O projeto independente **Lua — Partitura e MIDI** permanece deliberadamente fora da integração. Geração de partituras poderá ser pesquisada como funcionalidade futura sem importar esse projeto.

A documentação aqui descreve o **objetivo de desenvolvimento**, não uma declaração de funcionalidade já validada.
