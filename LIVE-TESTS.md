# V4.2.4 — Live tests no Windows

1. `xcursos version`
   - esperado: `4.2.4`.
2. `xcursos doctor`
   - esperado: runnerVersion 4.2.4; depois de `xcursos login`, CDP/Chrome/yt-dlp/ffprobe OK.
3. Abra manualmente a aula 108 e rode `xcursos probe --json`.
   - esperado: posição 108/198, `DIRECT_MP4`, `videoUrlAvailable: true` e `mediaDiagnostics` sem signed URL.
   - se network e DOM apontarem ao mesmo objeto, `correlation.sameObject: true`.
4. `xcursos range --start 108 --end 123 --json`
   - resume deve pular posições já saudáveis e tentar somente as pendentes.
   - em falha, observar `failureSummary` e `_xcursos-runner/errors.jsonl`.
5. Se o range preencher as lacunas, execute `xcursos-all`.
   - se as mesmas falhas se repetirem sem nenhuma cobertura nova, o wrapper deve encerrar com `NO_PROGRESS` antes de 12 passadas.
6. Finalize com `xcursos audit --json`.
