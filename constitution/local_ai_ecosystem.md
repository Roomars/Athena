# Ecosistema AI Locale — Risorse per Evoluzione

Analisi delle risorse disponibili nell'ecosistema AI locale (fonte: awesome-local-ai).
Questo file mi aiuta a sapere cosa esiste, cosa uso già, e cosa posso integrare in futuro.

---

## Stato attuale — cosa uso già

| Componente | Strumento | Status |
|---|---|---|
| LLM principale | Qwen3-14B (MLX-LM) | ✅ attivo |
| Vision LLM | Gemma 4 12B (mlx-vlm) | ✅ attivo |
| STT | whisper-large-v3-turbo (faster-whisper) | ✅ attivo |
| TTS | Federica (macOS nativo) | ✅ attivo |
| Object detection | YOLOv8-nano (ultralytics, MPS) | ✅ attivo |
| Memoria retrieval | BM25 + TF-IDF + RRF (Python puro) | ✅ attivo |
| Grafo memoria | networkx DiGraph | ✅ attivo |

---

## Upgrade disponibili — retrieval e memoria

### mlx-embeddings
- **Cos'è:** Modelli di embedding ottimizzati per Apple Silicon via MLX
- **Uso per Ari:** Sostituire TF-IDF con dense embeddings veri per retrieval semantico
- **Integrazione:** `from mlx_embeddings import load, encode` — drop-in in `memory_store.py`
- **Priorità:** Alta — completa la Memoria v2 con dense retrieval reale

### ChromaDB
- **Cos'è:** Vector database open-source con client Python, persistenza su disco
- **Uso per Ari:** Storage alternativo per embedding densi (invece di SQLite + numpy)
- **Integrazione:** `pip install chromadb` — client locale, nessun server
- **Nota:** Utile se la memoria supera i 10k fatti. Sotto quella soglia, numpy è sufficiente.

### FAISS (Facebook AI Similarity Search)
- **Cos'è:** Libreria C++/Python di Meta per nearest-neighbor su vettori
- **Uso per Ari:** Ricerca cosine su milioni di embedding in millisecondi
- **Integrazione:** `pip install faiss-cpu` — indice flat o IVF per scale-up
- **Nota:** Preferire ChromaDB se si vuole persistenza automatica; FAISS per performance raw.

---

## Upgrade disponibili — TTS

### Piper TTS
- **Cos'è:** TTS locale ultra-veloce, < 100ms latenza, qualità buona, multi-lingua
- **Uso per Ari:** Alternativa a Federica — più voci, più controllo, funziona offline puro
- **Integrazione:** Binario standalone + modello .onnx. Chiamata via subprocess da `tts.py`
- **Voci italiane disponibili:** it_IT-riccardo-x_low, it_IT-paola-medium
- **Priorità:** Media — Federica è già ottima. Piper serve se si vuole voce custom.

### Kokoro TTS
- **Cos'è:** Modello TTS neurali leggero (~80MB), qualità alta, licenza Apache
- **Uso per Ari:** Voce più naturale di Federica, stesso hardware
- **Integrazione:** Modello ONNX + libreria Python. Latenza ~200ms su M1.

### Coqui TTS (XTTS v2)
- **Cos'è:** TTS con voice cloning. Puoi clonare qualsiasi voce da 3 secondi di audio.
- **Uso per Ari:** Dare ad Ari una voce personalizzata (voce di Roby clonata, voce custom)
- **Nota:** Più pesante (~1.8GB), latenza 500ms+. Dipende da torch, non MLX.

---

## Upgrade disponibili — STT

### WhisperKit (Apple)
- **Cos'è:** Whisper ottimizzato per Apple Silicon con CoreML, latenza < 2s
- **Uso per Ari:** Alternativa a faster-whisper — più integrata con macOS
- **Integrazione:** Swift nativo o Python via subprocess
- **Priorità:** Bassa — faster-whisper su MPS è già veloce.

### moonshine (Useful Sensors)
- **Cos'è:** STT ultra-leggero per edge, < 300ms, modello tiny
- **Uso per Ari:** Wake word detection continua + STT immediato per comandi brevi
- **Nota:** Qualità inferiore a Whisper per discorsi lunghi. Ottimo per hotword.

---

## Upgrade disponibili — LLM inference

### Ollama
- **Cos'è:** Runtime LLM con API REST compatibile OpenAI, supporta MLX su Mac
- **Uso per Ari:** Alternativa a mlx-lm se si vuole API standard, multi-modello
- **Vantaggio:** `POST /api/generate` — stesso formato di OpenAI. Swap facile.
- **Svantaggio:** Overhead in più rispetto a MLX diretto. Aggiunge un processo daemon.

### llama.cpp (server mode)
- **Cos'è:** Inference C++ con server HTTP, GGUF format
- **Uso per Ari:** Fallback se MLX non supporta un modello (es. architetture nuove)
- **Integrazione:** Subprocess o HTTP. Non prioritario finché MLX copre tutto.

### LM Studio (locale API)
- **Cos'è:** GUI + server OpenAI-compatible per modelli GGUF
- **Uso per Ari:** Test rapido di nuovi modelli senza toccare il codice
- **Nota:** Solo GUI, non scriptabile. Utile solo per valutazione.

---

## Upgrade disponibili — agenti e memoria avanzata

### Mem0
- **Cos'è:** Layer memoria per agenti AI con storage e retrieval intelligente
- **Uso per Ari:** Confrontare con la Memoria v2 attuale — possibile source of inspiration
- **Nota:** Ha client Python ma richiede backend (Redis/vector DB). Più complesso della mia implementazione SQLite.

### Letta (ex MemGPT)
- **Cos'è:** Framework per LLM con memoria persistente lunga, context management
- **Uso per Ari:** Pattern per gestire conversazioni lunghissime (il nostro `save_episode` è ispirato a questo)
- **Nota:** Architettura interessante per FASE 9 (memoria episodica strutturata).

### Open WebUI
- **Cos'è:** UI web per qualsiasi LLM locale (Ollama, OpenAI-compatible)
- **Uso per Ari:** Non rilevante — Ari ha già la sua UI Swift nativa.

---

## Modelli da considerare per aggiornamenti

### Per LLM principale (rimpiazzo Qwen3-14B)
| Modello | Parametri | Note |
|---|---|---|
| Qwen3-32B (4bit) | 32B | Salto qualità significativo. Richiede ~20GB RAM. M1 Max ha 64GB — fattibile. |
| Gemma 3 27B (4bit) | 27B | Candidato per FASE 6. Multimodal se versione IT. |
| Mistral Small 3.1 | 22B | Ottimo per italiano. Licenza Apache. |
| Phi-4 (14B) | 14B | Microsoft, molto compatto per la qualità. |

### Per vision (rimpiazzo/affiancamento Gemma 4 12B)
| Modello | Note |
|---|---|
| Qwen2.5-VL 7B | Più veloce di Gemma 4 12B, qualità comparabile su screen analysis |
| LLaVA-Next 13B | Solido, well-tested, MLX support |
| InternVL2 8B | Ottimo per document understanding |

### Per embedding (nuovo — non ho ancora questo)
| Modello | Note |
|---|---|
| nomic-embed-text (mlx) | 137M param, veloce, ottimo per italiano |
| bge-m3 (mlx) | Multilingua, retrieval di alta qualità |
| all-MiniLM-L6-v2 | Piccolo e veloce, buono per fact similarity |

---

## Priorità di integrazione (ordine suggerito)

1. **mlx-embeddings + nomic-embed-text** — completa Memoria v2 con retrieval semantico vero
2. **Piper TTS (it_IT-paola)** — voce più controllabile di Federica
3. **ChromaDB** — se la memoria supera i 5k fatti e le query rallentano
4. **Qwen3-32B** — aggiornamento LLM quando si vuole salto qualitativo
5. **Qwen2.5-VL 7B** — vision più veloce per screen_vision YOLO+VLM loop

---

## Cosa NON integrare (e perché)

- **LangChain / LlamaIndex** — framework pesanti con troppo overhead. La mia pipeline è più snella.
- **Qdrant cloud** — non local-first. Uso ChromaDB o FAISS per restare locale.
- **OpenAI SDK** — non serve, nessuna dipendenza da cloud.
- **AutoGPT / AgentGPT** — agent loop troppo pesante e non controllabile. Self_modify è più preciso.
- **Stable Diffusion (image generation)** — fuori scope. Non genero immagini.
