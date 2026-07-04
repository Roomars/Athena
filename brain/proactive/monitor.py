import asyncio
import logging

from . import ALL_TRIGGERS

log = logging.getLogger("proactive")

INTERVAL = 60   # secondi tra ogni ciclo di controllo


async def monitor_loop(manager, tts) -> None:
    """Loop proattivo — controlla tutti i trigger ogni minuto."""
    log.info(f"monitor proattivo avviato ({len(ALL_TRIGGERS)} trigger, ciclo {INTERVAL}s)")
    while True:
        await asyncio.sleep(INTERVAL)
        for trigger in ALL_TRIGGERS:
            try:
                notif = await trigger.check()
                if notif is None:
                    continue
                log.info(f"trigger: {trigger.__class__.__name__} → '{notif.title}'")
                # Manda a Swift per mostrare la notifica macOS e aggiornare il pannello
                if manager.connection:
                    await manager.send({
                        "type":  "proactive_notification",
                        "title": notif.title,
                        "body":  notif.body,
                    })
                if notif.speak and manager.connection:
                    tts.speak(f"{notif.title}. {notif.body}")
            except Exception as e:
                log.debug(f"trigger {trigger.__class__.__name__} errore: {e}")
