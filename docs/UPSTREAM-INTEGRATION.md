# LUNA PT-BR — integração dos runtimes upstream

## Escopo desta branch

Esta branch atualiza o processo de compilação do LUNA para combinar revisões revisadas dos upstreams Neutrino e Open PS2 Loader com os forks específicos que o LUNA já utiliza.

Os submódulos originais pertencem ao mantenedor do LUNA e não são graváveis por esta integração. Por isso, o workflow realiza a mesclagem em checkouts temporários no GitHub Actions. Não altera os repositórios de terceiros e não faz force-push em submódulos.

## Revisões oficiais testadas

| Componente | Repositório | Commit upstream fixado |
| --- | --- | --- |
| Neutrino | https://github.com/ps2max32/neutrino | `1310a9af7c7395381042f49dd77c4e002515d0f7` |
| OPL | https://github.com/ps2homebrew/Open-PS2-Loader | `b3a2199795fe89ba7e2dd7b843354472dff2c3eb` |

Os hashes são registrados em `tools/upstream-runtime-pins.json` e verificados antes de cada mesclagem. Se a branch upstream avançar, a compilação para até que a revisão seja analisada e o pin seja atualizado explicitamente.

## Adaptações preservadas

- Neutrino: mantém o override de IP do UDPFS do LUNA, o retorno IGR e os ajustes de MMCE; adiciona os backends SMB2 e NFSv4.0, respectivas configurações e módulos.
- OPL: mantém o dispositivo IOPRP privado `opli:`, o ABI de VMC do LUNA, a restauração seletiva de cartões MMCE e o tratamento do botão de energia; incorpora as melhorias upstream de polling do IGR, suporte SIO2MAN e leitura BDM alinhada.
- O workflow valida marcadores de integração antes de compilar e confere que os módulos SMB/NFS foram produzidos.

## Limites conhecidos

- Os módulos SMB/NFS são compilados e empacotados, mas a interface e o scanner de bibliotecas do LUNA ainda não oferecem SMB/NFS como fontes selecionáveis. Esta etapa integra os runtimes; a exposição desses protocolos na interface é trabalho separado.
- O LUNA usa o game core do OPL, não a interface gráfica independente do OPL. Alterações exclusivamente na GUI do OPL não aparecem no menu do LUNA.
- O resultado da CI comprova compilação e integridade do pacote, não compatibilidade em hardware real. É necessário testar o ZIP no PS2 antes de adotá-lo como instalação principal.
