document.getElementById("btn-bridge").addEventListener("click", () => {
  const statusDiv = document.getElementById("status");
  statusDiv.textContent = "در حال اتصال...";

  chrome.runtime.sendMessage({ action: "bridge_session" }, (response) => {
    if (response && response.success) {
      statusDiv.style.color = "green";
      statusDiv.textContent = "✅ اتصال برقرار شد!";
    } else {
      statusDiv.style.color = "red";
      statusDiv.textContent = "❌ خطا در اتصال. آیا در برنامه لاگین هستید؟";
    }
  });
});