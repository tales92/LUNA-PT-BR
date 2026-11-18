# Pré-lançamento LUNA PT-BR — OPL + Neutrino

Esta publicação foi criada a partir da branch `update/opl-neutrino-luna-runtime-2026-11`.

## Conteúdo

- LUNA PT-BR com OPL como core padrão e suporte de descoberta ZSO.
- Runtime Neutrino mesclado com o upstream fixado, incluindo módulos SMB2 e NFSv4.0.
- Runtime OPL mesclado com o upstream fixado, preservando as adaptações MMCE, VMC, IOPRP e IGR do LUNA.
- Encaminhador de boot Matrix R2.
- Pacote FMCB mc0 instalável e arquivo SHA256SUMS.

## Aviso

Pré-lançamento de integração. A CI verifica a compilação, a presença dos componentes e a integridade dos arquivos, mas esta publicação ainda requer testes em um PlayStation 2 físico. SMB/NFS estão presentes nos runtimes empacotados; a interface e o scanner de bibliotecas do LUNA ainda não os expõem como fontes selecionáveis.

Consulte `docs/UPSTREAM-INTEGRATION.md` para detalhes técnicos e revisões upstream.
