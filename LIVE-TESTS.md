# V4.2.5 — Live tests no Windows

## 1. Confirmar instalação

```powershell
xcursos version
```

Esperado: `4.2.5`.

```powershell
xcursos doctor
```

Esperado: runnerVersion 4.2.5; Chrome/yt-dlp/ffprobe disponíveis. Depois de `xcursos login`, CDP deve estar acessível.

## 2. Aula 108 manual

Abra manualmente a aula 108 e rode:

```powershell
xcursos probe --json
```

Esperado:
- posição `108 / 198`;
- `mediaType: DIRECT_MP4`;
- `videoUrlAvailable: true`;
- `mediaSourceConfidence: PROVEN` quando exposto na metadata;
- nenhuma signed URL completa em diagnostics persistidos;
- Google Tag Manager nunca deve aparecer como mídia selecionada.

## 3. Range das lacunas

```powershell
xcursos range --start 108 --end 123 --json
```

O resume deve pular posições já saudáveis e atacar apenas as pendentes. Durante navegação rápida, se o player ainda não estiver pronto, o runner deve aguardar mídia comprovada ou devolver `MEDIA_NOT_READY`; ele nunca deve entregar iframe de analytics ao yt-dlp.

Se houver arquivo rejeitado pelo ffprobe, observar:
- código específico, por exemplo `VERIFY_NO_VIDEO_STREAM`;
- refresh da mesma aula em signed direct MP4;
- clean redownload sem retomar bytes parciais da tentativa inválida.

## 4. Curso completo

```powershell
xcursos-all
```

Se não houver ganho real de cobertura por várias passadas, deve encerrar com `NO_PROGRESS` mesmo que as causas alternem entre categorias diferentes.

## 5. Auditoria

```powershell
xcursos audit --json
```

Meta final para o curso de 198 posições:
- `missingPositions: []`;
- `duplicatePositions: []`;
- `invalidFilePositions: []`;
- DRM, se houver, permanece apenas classificado e não é contornado.

Se alguma das 12 posições continuar falhando, anexar o novo `_xcursos-runner/errors.jsonl` e `runner.log`; a V4.2.5 preserva códigos de verificação mais específicos para o próximo diagnóstico.
