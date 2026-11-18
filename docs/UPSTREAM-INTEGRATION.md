# LUNA PT-BR — sincronização e integração upstream

## Fontes acompanhadas

A automação acompanha as branches oficiais abaixo:

| Projeto | Repositório | Branch acompanhada |
| --- | --- | --- |
| LUNA principal | https://github.com/dnunezx/LUNA | \`main\` |
| Frontend LUNA/NHDDL | https://github.com/dnunezx/nhddl-luna | \`luna\` |
| Neutrino | https://github.com/ps2max32/neutrino | \`master\` |
| Open PS2 Loader | https://github.com/ps2homebrew/Open-PS2-Loader | \`master\` |

O workflow verifica os quatro HEADs todos os dias às **06:00 UTC (03:00 em Brasília)**. Também pode ser executado manualmente. Em uma execução agendada, uma nova build só é iniciada quando ao menos um desses quatro commits difere dos registrados na última Release.

## Como a atualização é aplicada

1. O commit mais recente de \`dnunezx/LUNA:main\` é integrado à branch de manutenção deste projeto.
2. O pin do frontend é atualizado para o HEAD atual de \`dnunezx/nhddl-luna:luna\`.
3. Os hashes atuais de Neutrino e OPL são gravados em \`tools/upstream-runtime-pins.json\`.
4. Os commits oficiais de Neutrino e OPL são mesclados sobre os respectivos forks que contêm as adaptações necessárias ao LUNA.
5. As validações verificam os pontos de integração LUNA/MMCE/VMC/IGR e os backends SMB/NFS. Conflitos ou alterações incompatíveis interrompem a build e impedem a publicação.

As dependências são obtidas por hashes completos, não por downloads flutuantes durante a compilação. O arquivo \`source-revisions.txt\` registra os commits utilizados em cada pacote.

O PSXCore permanece sujeito à revisão declarada em \`tools/dependencies.json\`; ele não é um dos quatro repositórios consultados pelo radar diário desta automação.

## Publicação automática

Uma Release é criada somente depois que a compilação, o empacotamento e as verificações SHA-256 terminam com sucesso. O pacote FMCB, o arquivo de checksums e \`source-revisions.txt\` são anexados à Release. As versões automáticas são marcadas como **pré-lançamento**, pois os testes automatizados não substituem a validação em um PlayStation 2 físico.

Um push na branch \`refresh/luna-official-latest-2026-11-18\` também dispara uma build. O acionamento manual oferece a opção de forçar uma nova publicação mesmo sem commits upstream novos. Uma execução agendada sem alterações apenas informa que está atualizada e não cria uma Release repetida.

## Personalizações preservadas

- **Idioma:** Português (Brasil) como padrão de instalação nova. Preferências já salvas continuam tendo prioridade.
- **Core PS2:** OPL como padrão em uma instalação nova. Preferências globais e por jogo salvas continuam tendo prioridade.
- **ZSO:** descoberta de imagens \`.zso\`, leitura dos metadados ISO comprimidos e encaminhamento obrigatório da execução para OPL.
- **Matrix Infinity:** inclui \`BOOT/BOOT2.ELF\` como encaminhador R2 para \`mc0:/APP_LUNA/luna.elf\`.
- **Neutrino:** preserva as adaptações de UDPFS, MMCE e retorno IGR; incorpora os backends SMB2 e NFSv4.0 do upstream.
- **OPL:** preserva IOPRP privado \`opli:\`, ABI VMC do LUNA, restauração seletiva de cartões MMCE e delegação do botão físico de energia ao IOP quando \`COMPAT_LUNA_IOP_POFF\` está ativo.

## Limites e validação

SMB/NFS são compilados e incluídos nos runtimes, mas esta integração ainda não os expõe como fontes selecionáveis na interface ou no scanner de bibliotecas do LUNA.

O LUNA utiliza o core de jogos do OPL; não carrega a interface gráfica independente do OPL.

A CI verifica compilação, presença dos módulos, geração dos ELFs e integridade dos arquivos do pacote FMCB. Isso **não substitui testes em um PlayStation 2 físico**. O encaminhador Matrix R2, ZSO, MMCE, VMC, retorno IGR e compatibilidade de jogos precisam ser testados no console antes de uma instalação considerada estável.
