# 🧪 Testing the TUI in a Browser with Playwright

This guide explains how to run and automate your **TUI** (Text User Interface) for [`prt`](https://github.com/richbodo/prt) using **Playwright**, **tmux**, and **ttyd**.

It creates a local browser view of your TUI so Playwright (and Screenpipe) can see and interact with it.

---

## ✅ Prerequisites

Install the required tools:

brew install tmux ttyd
npm install -D @playwright/test
npx playwright install

## Step 1: Run the TUI in a Shared tmux Session

Start your TUI inside a background tmux session:

tmux new -d -s tui
tmux send-keys -t tui './run_my_tui' C-m

To view it manually (optional):

tmux attach -t tui

Detach with <kbd>Ctrl-b</kbd> + <kbd>d</kbd>

## Step 2: Expose the TUI in a Browser with ttyd

Run this in your terminal:

ttyd -p 7681 tmux attach -t tui

Then open http://localhost:7681 in your browser.

You’ll see your TUI rendered via xterm.js — this is what Playwright will control.

💡 To add simple authentication during local testing:

ttyd -c user:pass -p 7681 tmux attach -t tui

## 🧠 Step 3: Create a Playwright Test

Create a test file: tests/tui.spec.ts

import { test, expect } from '@playwright/test';

test('TUI smoke test', async ({ page }) => {
  await page.goto('http://localhost:7681');

  // Focus the terminal (xterm.js canvas)
  const term = page.locator('div[role="textbox"], .xterm, .xterm-screen').first();
  await expect(term).toBeVisible();
  await term.click();

  // Type into the TUI
  await page.keyboard.type('jjkkhhll');
  await page.keyboard.press('Enter');
  await page.screenshot({ path: 'tui.png' });
});

## ▶️ Step 4: Run the Test

npx playwright test --headed

You’ll see:

A real browser window (--headed) running your TUI.

Playwright typing into it.

Screenshots saved in your project folder.

## 🧩 Notes & Tips

Delay keypresses for debugging:

await page.keyboard.type('hello', { delay: 100 });

Wait for render before typing:

await page.waitForTimeout(300);

Multi-session: you can run multiple TUIs on different ports:

ttyd -p 7682 tmux attach -t tui2
