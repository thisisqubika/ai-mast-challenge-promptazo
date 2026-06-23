// Runtime config — backend origin per environment.
// Local dev (localhost) hits the local backend; anywhere else (Cloudflare
// Pages) hits the deployed App Runner backend. No manual toggling.
(function () {
  var isLocal =
    location.hostname === "localhost" || location.hostname === "127.0.0.1";
  window.FANFEST_API_BASE = isLocal
    ? "http://localhost:8000"
    : "https://qv3pgi6de6.us-east-1.awsapprunner.com";
})();
