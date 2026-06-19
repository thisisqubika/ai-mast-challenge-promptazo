# Fan Fest — Canonical User Flow

Source: Benchmark FigJam → **"Flujo"** page (latest v2; supersedes the Page-1 draft).

## End-to-end flow

```
1.  Usuario ingresa a la app
2.  Home — eventos ocurriendo cerca del usuario (mocked)
3.  Info del evento
       → compartir, invitar amigos, hacer predicción del resultado
4.  El usuario indica "Ya estoy acá"   (check-in)
5.  Pantalla del evento (En Vivo)
       • Marcador en vivo + información del lugar
       • Countdown del tiempo del partido
       • Cantidad de goles (estilo summary de Google)
       • Momento de gol → card del jugador que lo hizo
       • Ya registrado → puede completar: predecir resultado, link al evento
6.  Usuario elige una acción ──┬── "Toca botón": 📸 Subir Foto al Muro
                               │        → Sistema carga la foto
                               │        → Foto aparece en Hype Wall (galería en vivo)
                               │
                               └── "Partido termina": Sistema detecta fin del partido
                                        → Sistema actualiza UI a Modo Post-Evento (modo "Recap")
7.  Acciones del usuario (post-evento) ──┬── La AI identifica highlights del evento
                                         │      ("Previa al partido", "Momento penal", "Antes del gol")
                                         └── Compartir en redes / Reaccionar / Comentarios
8.  Recap despliega:
       • Resultado final del partido   (+ muestra quiénes acertaron la predicción)
       • Wrap up del evento
       • Carrousel de fotos
9.  Usuario visualiza sugerencias de próximos eventos
10. Fin del flujo
```

## Key behaviors (from sticky notes)

- **Live screen**: countdown of match time; goal count in a Google-summary style; on each goal show a card of the scoring player.
- **Already registered**: prompt the user to complete actions now — predict the result, link to the event.
- **Hype Wall**: includes photos from *all* attendees as they upload them. Each photo shows **which user uploaded it** — uploaders must be registered on the platform.
- **Post-event UI**: flips to "Recap" mode and **no longer shows** the pre-event details.
- **Prediction**: users predict the match result; the recap reveals **who got it right**.

## Mapping to feature specs

| Flow steps | Draft brief |
|---|---|
| 1–2 | [`feature-01-event-discovery.md`](../../specs/drafts/feature-01-event-discovery.md) |
| 3–4 | [`feature-02-event-details-rsvp.md`](../../specs/drafts/feature-02-event-details-rsvp.md) |
| 5–6 | [`feature-03-live-event-hype-wall.md`](../../specs/drafts/feature-03-live-event-hype-wall.md) |
| 7–10 | [`feature-04-ai-recap.md`](../../specs/drafts/feature-04-ai-recap.md) |

## Delta vs Page-1 draft

The "Flujo" page adds, relative to the original flow chart:
- Home feed of nearby events (mocked).
- Explicit **check-in** step ("Ya estoy acá").
- **Prediction** mechanic (predict result → recap shows who was right).
- AI **highlight identification** with labeled moments.
- Social actions in recap (share, react, comment) with uploader identity.
- **Next-event suggestions** before the flow ends.
