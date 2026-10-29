chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "bridge_session") {

    // ۱. دریافت اطلاعات از سرور
    fetch("http://127.0.0.1:8000/api/auth/credentials")
      .then(res => {
        if (!res.ok) throw new Error("سرور پاسخ نداد (کد " + res.status + ")");
        return res.json();
      })
      .then((data) => {
        if (!data.username || !data.password) {
          throw new Error("اطلاعات لاگین در سرور یافت نشد.");
        }

        // ۲. باز کردن صفحه اصلی LMS (که اگر لاگین باشید به داشبورد می‌رود)
        chrome.tabs.create({ url: "https://lms4.ui.ac.ir/" }, (tab) => {

          const listener = function(tabId, info) {
            if (tabId === tab.id && info.status === 'complete') {
              chrome.tabs.onUpdated.removeListener(listener);

              // ۳. تزریق اسکریپت
              chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: (username, password) => {
                  // 👇 بررسی می‌کنیم که آیا فیلدهای لاگین وجود دارند یا نه
                  const userField = document.querySelector('input[name="username"]') || document.querySelector('input[type="text"]');
                  const passField = document.querySelector('input[name="password"]') || document.querySelector('input[type="password"]');

                  // اگر فیلدها وجود داشتند (یعنی در صفحه لاگین هستیم)
                  if (userField && passField) {
                    console.log("صفحه لاگین شناسایی شد. در حال پر کردن...");
                    userField.value = username;
                    passField.value = password;

                    const submitBtn = document.querySelector('input[type="submit"]') || document.querySelector('button[type="submit"]');
                    if (submitBtn) submitBtn.click();
                    else passField.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Enter'}));
                  } else {
                    // اگر فیلدها نبودند (یعنی شما از قبل لاگین بودید)
                    console.log("شما از قبل لاگین هستید. نیازی به پر کردن فرم نیست.");
                  }
                },
                args: [data.username, data.password]
              });
            }
          };
          chrome.tabs.onUpdated.addListener(listener);
        });

        sendResponse({ success: true });
      })
      .catch((err) => {
        console.error(err);
        sendResponse({ success: false, error: err.message });
      });

    return true;
  }
});