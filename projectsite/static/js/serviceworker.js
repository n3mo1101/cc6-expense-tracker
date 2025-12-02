self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open("projectsite-cache-v1").then(function (cache) {
      return cache.addAll([
        "/",
        "/static/admin_template/css/main-DLfE7m78.css",
        "/static/css/base.css",
        "/static/css/budgets.css",
        "/static/css/categories.css",
        "/static/css/dashboard.css",
        "/static/css/login.css",
        "/static/css/profile.css",
        "/static/css/signup.css",
        "/static/css/transactions.css",
        "/static/css/landing-page.css",

        "/static/admin_template/js/main-f0Mg-34g.js",
        "/static/js/base.js",
        "/static/js/budgets.js",
        "/static/js/categories.js",
        "/static/js/dashboard.js",
        "/static/js/icon-picker.js",
        "/static/js/profile.js",
        "/static/js/transactions.js",
      ]);
    })
  );
});
self.addEventListener("fetch", function (e) {
  e.respondWith(
    caches.match(e.request).then(function (response) {
      return response || fetch(e.request);
    })
  );
});
