---
name: progressive-web-app
description: Build Progressive Web Apps (PWAs) with offline support, installability, and caching strategies. Trigger whenever the user mentions PWA, service workers, web app manifests, Workbox, 'add to home screen', or wants their web app to work offline, feel native, or be installable.
risk: safe
source: community
date_added: "2026-03-17"
tags:
  - pwa
  - web-dev
  - service-worker
  - frontend
  - offline
  - caching
tools:
  - gemini
  - cursor
  - claude
metadata:
  mcpmarket-version: 1.0.0
---
# Progressive Web Apps (PWAs)

## Overview

A Progressive Web App is a web application that uses modern browser capabilities to deliver a fast, reliable, and installable experience — even on unreliable networks. The three required pillars are:

1. **HTTPS** — Required in production for service workers to register (localhost is exempt for development).
2. **Web App Manifest** (`manifest.json`) — Makes the app installable and defines its appearance on device home screens.
3. **Service Worker** (`sw.js`) — A background script that intercepts network requests, manages caches, and enables offline functionality.

## MisterLab — Spec di riferimento

Le specifiche PWA di MisterLab si trovano in `manuale/pwa/`. Leggere sempre prima di implementare:
- `manuale/pwa/core/architettura_pwa.md` — strategia offline, scope, DEC-026..029
- `manuale/pwa/core/match_live_offline.md` — offline island per Match Live
- `manuale/pwa/core/schema_eventi_live.md` — schema eventi in background sync

## When to Use This Skill

- Use when the user wants their web app to work offline or on unreliable networks.
- Use when building a mobile-first web project where users should be able to install the app to their home screen.
- Use when the user asks about caching strategies, service workers, or improving web app performance and resilience.
- Use when the user mentions Workbox, web app manifests, background sync, or push notifications for the web.
- Use when the user asks "can my website be installed like an app?" or "how do I make my site work offline?" — even if they don't use the word PWA.

## Deliverables Checklist

Every PWA implementation must include these files at minimum:

- [ ] `index.html` — Links manifest, registers service worker
- [ ] `manifest.json` — Full app metadata and icon set
- [ ] `sw.js` — Service worker with install, activate, and fetch handlers
- [ ] `app.js` — Main app logic with SW registration and install prompt handling
- [ ] `offline.html` — Fallback page shown when navigation fails offline (required — missing file will cause install to fail)

---

## Step 1: Web App Manifest (`manifest.json`)

Defines how the app appears when installed. Must be linked from `<head>` via `<link rel="manifest">`.

```json
{
  "name": "My Awesome PWA",
  "short_name": "MyPWA",
  "description": "A fast, offline-capable Progressive Web App.",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait-primary",
  "background_color": "#ffffff",
  "theme_color": "#0055ff",
  "icons": [
    {
      "src": "/assets/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

---

## Step 2: Service Worker Registration & Install Prompt (`app.js`)

```javascript
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      console.log('[App] SW registered, scope:', registration.scope);
    } catch (err) {
      console.error('[App] SW registration failed:', err);
    }
  });
}

let deferredPrompt;
const installBtn = document.getElementById('install-btn');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  if (installBtn) installBtn.hidden = false;
});

if (installBtn) {
  installBtn.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    deferredPrompt = null;
    installBtn.hidden = true;
  });
}
```

---

## Step 3: Service Worker — Caching Strategies (`sw.js`)

```javascript
const CACHE_VERSION = 'v1';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `dynamic-${CACHE_VERSION}`;

const APP_SHELL = ['/', '/index.html', '/styles.css', '/app.js', '/offline.html'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(STATIC_CACHE).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter((n) => n !== STATIC_CACHE && n !== DYNAMIC_CACHE)
          .map((n) => caches.delete(n))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== location.origin) return;

  if (url.pathname.match(/\.(css|js|png|jpg|svg|woff2)$/)) {
    event.respondWith(cacheFirst(request));
  } else if (request.headers.get('Accept')?.includes('text/html')) {
    event.respondWith(networkFirst(request));
  } else if (url.pathname.startsWith('/api/')) {
    event.respondWith(staleWhileRevalidate(request));
  }
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  const cache = await caches.open(STATIC_CACHE);
  cache.put(request, response.clone());
  return response;
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    const cache = await caches.open(DYNAMIC_CACHE);
    cache.put(request, response.clone());
    return response;
  } catch {
    return (await caches.match(request)) || caches.match('/offline.html');
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request).then((response) => {
    cache.put(request, response.clone());
    return response;
  });
  return cached || fetchPromise;
}
```

---

## Edge Cases & Platform Notes

### iOS / Safari
- Non supporta `beforeinstallprompt` — installazione manuale via Share → "Aggiungi a schermata Home"
- Usa i meta tag `apple-mobile-web-app-*` per integrazione iOS corretta
- Safari può cancellare i cache SW dopo ~7 giorni di inattività (ITP)

### HTTPS
- I service worker si registrano solo su `https://`. Eccezione: `http://localhost`

### Cache-Busting al deploy
- Incrementare sempre `CACHE_VERSION` ad ogni deploy per invalidare i vecchi cache

### Workbox (produzione)
Per app in produzione considerare [Workbox](https://developer.chrome.com/docs/workbox) che gestisce edge cases, scadenza cache e versioning automaticamente.

---

## Checklist Before Shipping

- [ ] HTTPS attivo
- [ ] `manifest.json` con `name`, `short_name`, `start_url`, `display`, `icons` (192 + 512)
- [ ] Icone con `purpose: "any maskable"`
- [ ] SW si registra senza errori (DevTools → Application → Service Workers)
- [ ] App shell carica da cache in modalità Offline (DevTools → Network → Offline)
- [ ] `offline.html` fallback funzionante
- [ ] Lighthouse PWA audit passa
- [ ] Testato su iOS Safari e Android Chrome
