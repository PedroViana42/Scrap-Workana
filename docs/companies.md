# Monitored Companies

Last validation: 2026-08-10

Radar monitors companies through public ATS job boards. This catalog prioritizes technology, data, AI/ML, backend, cloud/platform, Brazil, LATAM, remote-friendly roles, and early-career signals.

Revalidate:

```bash
python -m radar.cli validate-companies
python -m radar.cli validate-companies --source greenhouse
python -m radar.cli validate-companies --source lever
python -m radar.cli validate-companies --source ashby
```

Synchronize validated companies into PostgreSQL without creating Jobs:

```bash
python -m radar.cli sync-companies
```

| Company | ATS | Identifier | Priority | Tags | Verified | Jobs | Brazil | Remote | Tech | Early Career |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Airbnb | Greenhouse | airbnb | 80 | engineering, data, backend, remote | yes | 182 | 10 | 28 | 173 | 93 |
| Wellhub / Gympass | Greenhouse | gympass | 100 | brazil, latam, engineering, backend, data, remote | yes | 114 | 51 | 32 | 113 | 110 |
| Wildlife Studios | Greenhouse | wildlifestudios | 100 | brazil, engineering, backend, data, ai, ml | yes | 20 | 20 | 0 | 20 | 8 |
| Launch Potato | Greenhouse | launchpotato | 80 | latam, remote, engineering, data | yes | 11 | 0 | 10 | 11 | 1 |
| ClickHouse | Greenhouse | clickhouse | 80 | remote, engineering, backend, data, database, cloud | yes | 170 | 0 | 133 | 170 | 94 |
| Cision | Greenhouse | cision | 60 | engineering, data, platform | yes | 50 | 3 | 26 | 50 | 24 |
| Figma | Greenhouse | figma | 80 | engineering, frontend, backend, data, ai | yes | 166 | 4 | 1 | 166 | 128 |
| Kaizen Gaming | Greenhouse | kaizengaming | 60 | engineering, backend, data, qa | yes | 84 | 7 | 0 | 84 | 53 |
| Nearform | Greenhouse | nearform | 80 | remote, engineering, backend, frontend, cloud | yes | 24 | 0 | 0 | 24 | 1 |
| Goodway Group | Greenhouse | goodwaygroup | 60 | remote, engineering, data | yes | 8 | 0 | 8 | 8 | 7 |
| Speechify | Greenhouse | speechify | 80 | remote, engineering, ai, ml, backend | yes | 1289 | 29 | 14 | 1289 | 805 |
| Cloudflare | Greenhouse | cloudflare | 80 | engineering, backend, security, cloud, platform | yes | 297 | 2 | 54 | 297 | 297 |
| Datadog | Greenhouse | datadog | 80 | engineering, devops, cloud, platform, data | yes | 445 | 16 | 53 | 445 | 291 |
| MongoDB | Greenhouse | mongodb | 80 | engineering, backend, data, database, cloud | yes | 406 | 7 | 0 | 406 | 204 |
| Elastic | Greenhouse | elastic | 80 | remote, engineering, data, security, cloud | yes | 245 | 4 | 16 | 245 | 161 |
| Stripe | Greenhouse | stripe | 80 | engineering, backend, data, security, platform | yes | 556 | 1 | 106 | 556 | 547 |
| Canonical | Greenhouse | canonical | 80 | remote, engineering, devops, cloud, platform | yes | 304 | 0 | 6 | 303 | 277 |
| CI&T | Lever | ciandt | 100 | brazil, latam, engineering, backend, frontend, data, qa | yes | 150 | 128 | 0 | 150 | 22 |
| Oowlish | Lever | oowlish | 100 | latam, remote, engineering, backend, frontend, data | yes | 18 | 16 | 0 | 18 | 18 |
| Swile | Lever | swile | 60 | engineering, backend, data | yes | 22 | 10 | 3 | 17 | 8 |
| Yuno | Lever | yuno | 100 | latam, remote, engineering, backend, data | yes | 46 | 3 | 0 | 45 | 15 |
| Spotify | Lever | spotify | 80 | engineering, backend, data, platform, early-career | yes | 98 | 0 | 0 | 77 | 10 |
| Binance | Lever | binance | 80 | remote, engineering, backend, data, security, devops | yes | 296 | 6 | 8 | 288 | 96 |
| Aircall | Lever | aircall | 60 | engineering, backend, frontend, data | yes | 77 | 0 | 5 | 77 | 16 |
| Coupa | Lever | coupa | 60 | engineering, backend, data, cloud | yes | 86 | 1 | 2 | 86 | 14 |
| Shield AI | Lever | shieldai | 80 | engineering, ai, ml, devops, platform | yes | 435 | 0 | 3 | 435 | 71 |
| Lyra Health | Lever | lyrahealth | 60 | engineering, data, backend, platform | yes | 524 | 0 | 55 | 508 | 19 |
| Nubank | Ashby | nubank | 100 | brazil, latam, engineering, backend, data, ai, ml | yes | 107 | 40 | 0 | 107 | 66 |
| Canals | Ashby | canals | 80 | engineering, backend, data, ai | yes | 29 | 2 | 0 | 29 | 5 |
| Camunda | Ashby | camunda | 80 | remote, engineering, backend, cloud, platform | yes | 33 | 0 | 24 | 33 | 14 |
| Pyyne | Ashby | pyyne | 80 | brazil, engineering, data | yes | 4 | 4 | 4 | 4 | 1 |
| Articul8 AI | Ashby | articul8 | 80 | ai, ml, engineering, data, platform | yes | 20 | 8 | 7 | 20 | 13 |
| Sardine | Ashby | sardine | 80 | remote, engineering, backend, data, security | yes | 35 | 3 | 0 | 35 | 23 |
| Alternative Payments | Ashby | alternativepayments | 60 | engineering, backend, data | yes | 14 | 1 | 1 | 14 | 14 |
| Skydropx / Frenet | Ashby | skydropx | 80 | latam, engineering, backend, data | yes | 28 | 8 | 1 | 16 | 14 |
| Tako | Ashby | tako | 80 | engineering, ai, data | yes | 20 | 20 | 0 | 8 | 8 |
| Tempo | Ashby | tempo | 60 | engineering, backend, data | yes | 9 | 2 | 8 | 9 | 2 |
| Oscilar | Ashby | oscilar | 80 | brazil, engineering, data, ai, ml | yes | 23 | 4 | 21 | 23 | 21 |
| LiteLLM | Ashby | litellm | 80 | remote, engineering, ai, ml, backend | yes | 14 | 1 | 1 | 14 | 2 |
| Jump | Ashby | jump | 60 | engineering, ai, ml | yes | 3 | 0 | 3 | 3 | 0 |
| Feegow | Ashby | feegow | 60 | brazil, engineering, healthtech | yes | 1 | 1 | 1 | 1 | 1 |
| ElevenLabs | Ashby | elevenlabs | 80 | remote, engineering, ai, ml, backend | yes | 230 | 7 | 2 | 230 | 80 |
| LangChain | Ashby | langchain | 80 | remote, engineering, ai, ml, backend | yes | 101 | 0 | 6 | 101 | 27 |
| Supabase | Ashby | supabase | 80 | remote, engineering, backend, database, cloud | yes | 57 | 0 | 45 | 57 | 30 |
| Docker | Ashby | docker | 80 | remote, engineering, devops, cloud, platform | yes | 58 | 0 | 0 | 58 | 30 |

## Invalid During Research

These were checked and not included in the final catalog:

- Greenhouse: Teachable (`teachable`) returned 404.
- Greenhouse: Telnyx (`telnyx`) returned 404.
- Lever: Neon (`neon`) timed out during validation.
- Lever: Flex (`flex`) returned 404.
- Lever: Osmind (`osmind`) returned 404.
- Lever: Insider (`insider`) returned 404.
- Ashby: Enter (`enter`) returned 404.
- Ashby: TRM Labs (`trmlabs`) returned 404.
- Ashby: PALO IT (`paloit`) returned 404.
- Greenhouse smoke candidate: OpenAI (`openai`) returned 404.
- Lever smoke candidate: Netlify (`netlify`) returned 404.
- Lever extra candidate: Vercel (`vercel`) returned 404.
- Lever extra candidate: Replit (`replit`) returned 404.
- Ashby extra candidate: Anthropic (`anthropic`) returned 404.
- Ashby extra candidate: Mistral AI (`mistral`) returned 404.
- Ashby extra candidate: Retool (`retool`) returned 404.

