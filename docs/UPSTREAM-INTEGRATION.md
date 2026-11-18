# LUNA PT-BR — sincronização e integração upstream

## Base desta reconstrução

| Projeto | Revisão |
| --- | --- |
| LUNA principal, `dnunezx/LUNA` | `4ee0b462e9486d5c384ec6db2f990c526a7ad3fe` |
| Frontend, branch `luna` de `dnunezx/nhddl-luna` | `df302ea8d961df17594d8c581958406ced203be7` |
| Neutrino específico do LUNA | `669acaa3838770481e4f9b5a708c133c3a4e7278` |
| OPL específico do LUNA | `c533f939195847df1cd4d905f089aeb07300c72e` |
| PSXCore | `5d4de02f57933f70c48335d938c1d4c8b69634ad` |

O frontend foi avançado até o último commit disponível na branch `luna` do repositório `dnunezx/nhddl-luna`, que é dois commits à frente do pin ainda declarado pelo repositório principal oficial.

## Runtimes oficiais

A integração parte dos forks mantidos pelo autor do LUNA e mescla os commits mais recentes das branches oficiais, sem sobrescrever as adaptações específicas do launcher.

| Runtime | Upstream oficial | Commit oficial verificado |
| --- | --- | --- |
| Neutrino | https://github.com/ps2max32/neutrino | `1310a9af7c7395381042f49dd77c4e002515d0f7` |
| Open PS2 Loader | https://github.com/ps2homebrew/Open-PS2-Loader | `b3a2199795fe89ba7e2dd7b843354472dff2c3eb` |

Na verificação de 18/11/2026, esses commits já eram os HEADs de `master` nos respectivos repositórios oficiais. Não havia commits oficiais posteriores para incorporar.

Os pins são armazenados em `tools/upstream-runtime-pins.json`. A CI valida os hashes e interrompe a compilação se o upstream avançar, exigindo revisão explícita.

## Personalizações do fork

- **Idioma:** Português (Brasil) como padrão de instalação nova. Preferências já salvas continuam tendo prioridade.
- **Core PS2:** OPL como padrão em uma instalação nova. Preferências globais e por jogo salvas continuam tendo prioridade.
- **ZSO:** descoberta de imagens `.zso`, leitura dos metadados ISO comprimidos e encaminhamento obrigatório da execução para OPL.
- **Matrix Infinity:** inclui `BOOT/BOOT2.ELF` como encaminhador R2 para `mc0:/APP_LUNA/luna.elf`.
- **Neutrino:** preserva as adaptações de UDPFS, MMCE e retorno IGR; incorpora os backends SMB2 e NFSv4.0 do upstream.
- **OPL:** preserva IOPRP privado `opli:`, ABI VMC do LUNA, restauração seletiva de cartões MMCE e delegação do botão físico de energia ao IOP quando `COMPAT_LUNA_IOP_POFF` está ativo.

## Limites e validação

SMB/NFS são compilados e incluídos nos runtimes, mas esta integração ainda não os expõe como fontes selecionáveis na interface ou no scanner de bibliotecas do LUNA.

O LUNA utiliza o core de jogos do OPL; não carrega a interface gráfica independente do OPL.

A CI verifica compilação, presença dos módulos, geração dos ELFs e integridade dos arquivos do pacote FMCB. Isso **não substitui testes em um PlayStation 2 físico**. O encaminhador Matrix R2, ZSO, MMCE, VMC, retorno IGR e compatibilidade de jogos precisam ser testados no console antes de uma instalação considerada estável.

Nenhuma publicação em Releases é criada automaticamente nesta etapa. Primeiro será gerado e inspecionado um artefato de CI.
