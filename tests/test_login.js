const { chromium } = require('playwright');

(async () => {
  console.log('Starting Playwright test...');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => console.log('Browser:', msg.text()));
  page.on('pageerror', err => console.error('Page error:', err.message));

  try {
    // Navigate to frontend
    console.log('Navigating to http://34.132.117.195:3000...');
    await page.goto('http://34.132.117.195:3000', { timeout: 30000 });
    console.log('Page loaded, title:', await page.title());

    // Take screenshot
    await page.screenshot({ path: '/tmp/1-homepage.png' });
    console.log('Screenshot saved: /tmp/1-homepage.png');

    // Look for login button/link
    const loginLink = await page.$('a[href*="login"], button:has-text("Login"), button:has-text("Sign"), a:has-text("Login")');
    if (loginLink) {
      console.log('Found login link, clicking...');
      await loginLink.click();
      await page.waitForTimeout(2000);
    } else {
      console.log('No login link found, navigating directly...');
      await page.goto('http://34.132.117.195:3000/login', { timeout: 30000 });
    }

    await page.screenshot({ path: '/tmp/2-login-page.png' });
    console.log('Screenshot saved: /tmp/2-login-page.png');

    // Find name input and enter name
    const nameInput = await page.$('input[name="name"], input[placeholder*="name" i], input[type="text"]');
    if (nameInput) {
      console.log('Found name input, entering name...');
      await nameInput.fill('playwrightuser');
      await page.screenshot({ path: '/tmp/3-name-entered.png' });

      // Find and click submit button
      const submitButton = await page.$('button[type="submit"], button:has-text("Login"), button:has-text("Join"), button:has-text("Enter")');
      if (submitButton) {
        console.log('Found submit button, clicking...');
        await submitButton.click();

        // Wait for navigation or response
        await page.waitForTimeout(3000);
        await page.screenshot({ path: '/tmp/4-after-login.png' });
        console.log('Screenshot saved: /tmp/4-after-login.png');

        // Check if we're logged in
        const url = page.url();
        console.log('Current URL:', url);

        // Look for logout button or user info
        const logoutBtn = await page.$('button:has-text("Logout"), a:has-text("Logout"), [data-testid="user"]');
        if (logoutBtn) {
          console.log('SUCCESS: Login worked! Found logout button.');
        } else {
          // Check for error messages
          const error = await page.$('.error, [role="alert"], .text-red');
          if (error) {
            const errorText = await error.textContent();
            console.log('ERROR on page:', errorText);
          } else {
            console.log('Login state unclear, checking page content...');
            const bodyText = await page.textContent('body');
            console.log('Page contains "login":', bodyText.toLowerCase().includes('login'));
            console.log('Page contains "logout":', bodyText.toLowerCase().includes('logout'));
          }
        }
      } else {
        console.log('ERROR: No submit button found');
      }
    } else {
      console.log('ERROR: No name input found');
      console.log('Available inputs:', await page.$$eval('input', inputs => inputs.map(i => ({ type: i.type, name: i.name, placeholder: i.placeholder }))));
    }

  } catch (err) {
    console.error('Test error:', err.message);
    await page.screenshot({ path: '/tmp/error.png' });
  }

  await browser.close();
  console.log('Test complete.');
})();
