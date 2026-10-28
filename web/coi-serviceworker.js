/*! coi-serviceworker v0.1.7 - Guido Zuidhof and contributors, MIT License */
let coepCredentialless = true;
if (typeof window === 'undefined') {
    self.addEventListener("install", () => self.skipWaiting());
    self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
    self.addEventListener("message", (ev) => {
        if (ev.data && ev.data.type === "deregister") {
            self.registration.unregister();
        }
    });
    self.addEventListener("fetch", function (event) {
        if (event.request.cache === "only-if-cached" && event.request.mode !== "same-origin") {
            return;
        }
        event.respondWith(
            fetch(event.request).then((response) => {
                if (response.status === 0) {
                    return response;
                }
                const newHeaders = new Headers(response.headers);
                newHeaders.set("Cross-Origin-Opener-Policy", "same-origin");
                newHeaders.set("Cross-Origin-Embedder-Policy", coepCredentialless ? "credentialless" : "require-corp");
                newHeaders.set("Cross-Origin-Resource-Policy", "cross-origin");
                return new Response(response.body, {
                    status: response.status,
                    statusText: response.statusText,
                    headers: newHeaders,
                });
            })
        );
    });
} else {
    (() => {
        const reloadedBySelf = window.sessionStorage.getItem("coiReloadedBySelf");
        window.sessionStorage.removeItem("coiReloadedBySelf");
        const coepDegradation = (reloadedBySelf === "true");
        if (window.crossOriginIsolated || coepDegradation) {
            return;
        }
        if ("serviceWorker" in navigator) {
            const scriptSrc = window.document.currentScript ? window.document.currentScript.src : "./coi-serviceworker.js";
            navigator.serviceWorker.register(scriptSrc).then(
                (registration) => {
                    registration.addEventListener("updatefound", () => {
                        window.sessionStorage.setItem("coiReloadedBySelf", "true");
                        window.location.reload();
                    });
                    if (registration.active && !navigator.serviceWorker.controller) {
                        window.sessionStorage.setItem("coiReloadedBySelf", "true");
                        window.location.reload();
                    }
                },
                (err) => {
                    console.error("COI ServiceWorker registration failed: ", err);
                }
            );
        }
    })();
}
