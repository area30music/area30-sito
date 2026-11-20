/* Tocco su una notifica: apre il suo dettaglio nella pagina Notifiche di AREA30.
   Registrato prima di OneSignal; se il link è già il dettaglio, lascia fare a OneSignal (che conta i clic). */
self.addEventListener("notificationclick", function (e) {
  var base = "__BASE__";
  var n = e.notification || {};
  var d = n.data || {};
  var u = d.launchURL || d.url || "";
  if (u.indexOf("/notifiche?") !== -1) return;
  e.stopImmediatePropagation();
  n.close();
  var q = new URLSearchParams();
  q.set("n", d.notificationId || d.id || "");
  q.set("t", d.title || n.title || "AREA30");
  q.set("m", d.body || n.body || "");
  if (u && !/^https?:\/\/[^/]+\/?$/.test(u)) q.set("l", u);
  if (d.image || n.image) q.set("i", d.image || n.image);
  var dest = self.location.origin + base + "/notifiche?" + q.toString();
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(function (list) {
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      if ("navigate" in c) {
        return c.focus().then(function (w) { return (w || c).navigate(dest); }).catch(function () { return self.clients.openWindow(dest); });
      }
    }
    return self.clients.openWindow(dest);
  }));
});
