const puppeteer = require('puppeteer');

// const URL = 'http://www.message.test.com/';
const URL = 'http://localhost:8000/';
const INTERVAL = 8000;

async function check_msg(browser, id) {
  const page = await browser.newPage();
  page.on('dialog', async (dialog) => {
    await dialog.accept();
  });
  console.log(`Admin checking message with id=${id}`);
  await page.goto(URL + `?mid=${id}`, {
    waitUntil: 'networkidle2',
  });
  await page.waitForTimeout(INTERVAL - 5000);

  console.log(`Deleting message with id=${id}`);
  await page.goto(URL + `?mid=${id}&action=delete`, {
    waitUntil: 'networkidle2',
  });
  await page.close();
}

async function adminRoutine(browser) {
  // Get all msg id
  console.log('Fetching message list');
  const page = await browser.newPage();
  await page.goto(URL, {
    waitUntil: 'networkidle2',
  });

  const ids = await page.$$eval('tr > td:nth-child(1)', (eles) =>
    eles.map((ele) => ele.innerHTML)
  );
  if (ids.length) {
    console.log(`Got ${ids.length} messages`);
  } else {
    console.log('Nothing to check');
  }
  for (id of ids) {
    try {
      await check_msg(browser, id);
    } catch (e) {
      console.error('[ERR]:' + e);
    }
  }
}

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  // Login
  await page.goto(URL + '?action=login', {
    waitUntil: 'networkidle2',
  });
  const usernameField = await page.$('#login-form > input:nth-child(2)');
  const passwordField = await page.$('#login-form > input:nth-child(6)');
  await usernameField.click();
  await page.keyboard.type('admin');
  await passwordField.click();
  await page.keyboard.type('potiquyrou');
  await page.keyboard.press('Enter');
  await Promise.all([
    page.waitForNavigation(),
    page.waitForResponse((resp) => resp.status() === 200),
    page.waitForSelector('table'),
  ]);

  // Set flag
  await page.setCookie({ name: 'FLAG', value: 'duckctf{fake_flag}' });
  await page.close();
  setInterval(async () => {
    await adminRoutine(browser);
  }, INTERVAL);
})();
